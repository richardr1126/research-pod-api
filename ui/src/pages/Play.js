import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import apiService from '../services/apiService';

function Play() {
  const { podId } = useParams();
  const audioRef = useRef(null);

  const [podcast, setPodcast] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [transcript, setTranscript] = useState([]);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [activeTab, setActiveTab] = useState('sources'); // Default to 'sources' tab

  // Fetch podcast data when component mounts
  useEffect(() => {
    const fetchPodcast = async () => {
      try {
        setIsLoading(true);

        // Fetch podcast data directly from API
        const result = await apiService.getPodcast(podId);

        if (result.status === 'COMPLETED') {
          setPodcast({
            id: podId,
            title: result.query || 'Untitled Podcast',
            audioUrl: result.audio_url || `/v1/api/podcast/${podId}/audio`,
            transcriptUrl: `/v1/api/podcast/${podId}/transcript`,
            keywords: result.keywords_arxiv || [],
            sources: result.sources_arxiv || [],
            summary: result.summary || 'Summary not available yet.' // Assuming summary might be available
          });

          // In a real implementation, you'd fetch the transcript from the API
          // Example: Fetch transcript
          try {
            const transcriptData = await apiService.getTranscript(podId); // Assuming an API service method exists
             // Assuming transcriptData is an array like [{ time: 0, text: "..."}]
             // Make sure the format matches what the component expects
            if (Array.isArray(transcriptData) && transcriptData.length > 0 && 'time' in transcriptData[0] && 'text' in transcriptData[0]) {
                 setTranscript(transcriptData);
            } else {
                 // Fallback or default message if transcript format is wrong or empty
                console.warn("Transcript format unexpected or empty, using placeholder.");
                 setTranscript([
                    { time: 0, text: "Welcome to this AI generated podcast." },
                    { time: 5, text: "Today we're exploring the topic you requested." },
                    { time: 10, text: "Let's dive into the details." }
                 ]);
            }
          } catch (transcriptError) {
            console.error("Failed to fetch transcript:", transcriptError);
            // Set placeholder if fetch fails
            setTranscript([
                { time: 0, text: "Transcript loading failed." },
            ]);
          }


        } else if (result.status === 'PROCESSING' || result.status === 'PENDING' || result.status === 'INITIALIZING') {
             setError('This podcast is still generating. Please check back later.');
             // Optional: Redirect to generating page?
             // navigate(`/generating/${podId}`);
        }
         else {
             setError(`Podcast generation failed with status: ${result.status}.`);
        }
      } catch (err) {
        console.error('Error fetching podcast:', err);
        setError('Failed to load podcast. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPodcast();
  }, [podId]); // Removed navigate from dependency array as it's not used here anymore

  // Set up audio element event listeners
  useEffect(() => {
    if (audioRef.current && podcast) {
      const audio = audioRef.current;

      const handleTimeUpdate = () => {
        setCurrentTime(audio.currentTime);

        // Update current transcript based on time
        const currentSegment = transcript.find((segment, index) => {
          const nextSegment = transcript[index + 1];
          return segment.time <= audio.currentTime &&
                 (!nextSegment || nextSegment.time > audio.currentTime);
        });

        if (currentSegment) {
          setCurrentTranscript(currentSegment.text);
        } else if (transcript.length > 0 && audio.currentTime < transcript[0].time) {
            // If before the first segment, show nothing or a placeholder
            setCurrentTranscript('');
        }
      };

      const handleLoadedMetadata = () => {
         // Check if duration is a valid number
         if (isFinite(audio.duration)) {
             setDuration(audio.duration);
         } else {
             console.warn("Audio duration is not available or infinite.");
             setDuration(0); // Set to 0 or handle appropriately
         }
      };

      const handlePlay = () => setIsPlaying(true);
      const handlePause = () => setIsPlaying(false);
      const handleEnded = () => {
        setIsPlaying(false);
        setCurrentTime(0); // Reset time to beginning on end
        setCurrentTranscript(transcript.length > 0 ? transcript[0].text : ''); // Reset transcript display
      };

      audio.addEventListener('timeupdate', handleTimeUpdate);
      audio.addEventListener('loadedmetadata', handleLoadedMetadata);
      audio.addEventListener('play', handlePlay);
      audio.addEventListener('pause', handlePause);
      audio.addEventListener('ended', handleEnded);

      // Attempt to load metadata if src is set but duration is 0
      if (audio.src && duration === 0) {
          audio.load(); // Trigger loading metadata explicitly if needed
      }


      return () => {
        audio.removeEventListener('timeupdate', handleTimeUpdate);
        audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
        audio.removeEventListener('play', handlePlay);
        audio.removeEventListener('pause', handlePause);
        audio.removeEventListener('ended', handleEnded);
      };
    }
  }, [audioRef, podcast, transcript, duration]); // Added duration to dependencies


  // Toggle play/pause
  const togglePlay = () => {
    if (audioRef.current && duration > 0) { // Only allow play if duration is valid
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play().catch(e => console.error("Error playing audio:", e)); // Add catch for play promise
      }
    } else {
         console.warn("Audio not ready or has zero duration.");
    }
  };

  // Seek to a specific position
  const handleSeek = (e) => {
    if (audioRef.current && duration > 0) { // Check duration before seeking
      const seekTime = (e.target.value / 100) * duration;
      audioRef.current.currentTime = seekTime;
      setCurrentTime(seekTime);
    }
  };

  // Format time (mm:ss)
  const formatTime = (seconds) => {
     const validSeconds = isFinite(seconds) ? seconds : 0;
     const mins = Math.floor(validSeconds / 60);
     const secs = Math.floor(validSeconds % 60);
     return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  // Render podcast tab content
  const renderTabContent = () => {
    if (!podcast) return null;

    switch (activeTab) {
      case 'sources':
        return (
          <div className="tab-content sources-tab">
            <h4>Sources:</h4>
            {podcast.sources && podcast.sources.length > 0 ? (
              <ul className="sources-list-play">
                {podcast.sources.map((source, index) => (
                  <li key={`source-${index}`}>
                    <a href={source.url} target="_blank" rel="noopener noreferrer">
                      {source.title || source.url || `Source ${index + 1}`}
                    </a>
                  </li>
                ))}
              </ul>
            ) : <p>No sources available.</p>}
          </div>
        );
      case 'summary':
        return (
          <div className="tab-content summary-tab">
            <h4>Summary:</h4>
            <p>{podcast.summary || 'No summary available'}</p>
          </div>
        );
      case 'keywords':
        return (
          <div className="tab-content keywords-tab">
            <h4>Search Keywords:</h4>
             {podcast.keywords && podcast.keywords.length > 0 ? (
              <ul className="keywords-list-play">
                {podcast.keywords.map((group, index) => (
                  <li key={`keyword-group-${index}`}>{Array.isArray(group) ? group.join(' | ') : group}</li>
                ))}
              </ul>
            ) : <p>No keywords available.</p>}
          </div>
        );
      default:
        return null;
    }
  };

  if (isLoading) return <div className="loading loading-message">Loading podcast...</div>;
  if (error) return <div className="error-message">{error}</div>;
  if (!podcast) return <div className="not-found not-found-message">Podcast not found</div>;

  return (
    <div className="play-container">
      <h2 className="play-title">{podcast.title}</h2>

      {/* Audio element (hidden but controlled) */}
      <audio
        ref={audioRef}
        src={podcast.audioUrl}
        preload="metadata"
        onLoadedMetadata={() => { // Directly handle loadedmetadata to ensure duration is set
             if (audioRef.current && isFinite(audioRef.current.duration)) {
                 setDuration(audioRef.current.duration);
             }
        }}
        onError={(e) => {
             console.error("Audio loading error:", e);
             setError("Failed to load audio file.");
        }}
      />

      {/* Custom player controls */}
      <div className="player-controls">
        {/* Time display and seek bar */}
        <div className="time-controls">
          <div className="time-display current-time">
            {formatTime(currentTime)}
          </div>

          <input
            type="range"
            min="0"
            max="100"
            value={duration > 0 ? (currentTime / duration) * 100 : 0} // Prevent NaN if duration is 0
            onChange={handleSeek}
            disabled={duration === 0} // Disable slider if no duration
            className="time-scrubber"
          />

          <div className="time-display duration">
            {formatTime(duration)}
          </div>
        </div>

        {/* Play button centered below the seek bar */}
        <div className="play-button-container">
          <button
            className={`play-pause-button ${isPlaying ? 'pause' : 'play'}`}
            onClick={togglePlay}
            disabled={duration === 0} // Disable button if no duration
          >
            {isPlaying ? 'Pause' : 'Play'}
          </button>
        </div>
      </div>

      {/* Current transcript line */}
      <div className="current-transcript">
        {currentTranscript}
      </div>

      {/* Full transcript (styled like the log in GeneratingPodcast.js) */}
      <div className="transcript-container">
        <h3 className="transcript-title">Transcript</h3>
        <div className="transcript-log">
          {transcript.length > 0 ? (
            transcript.map((segment, index) => (
              <div
                key={index}
                 // Use Math.floor for comparison to avoid floating point issues maybe? Or a tolerance.
                className={`transcript-segment ${Math.abs(segment.time - currentTime) < 1 ? 'active' : ''}`}
                onClick={() => {
                  if (audioRef.current && duration > 0) { // Check duration before seeking
                    audioRef.current.currentTime = segment.time;
                    setCurrentTime(segment.time); // Update state immediately
                  }
                }}
                // Add role and tabindex for accessibility
                role="button"
                tabIndex="0"
                onKeyPress={(e) => { // Allow activation with Enter key
                    if (e.key === 'Enter' && audioRef.current && duration > 0) {
                        audioRef.current.currentTime = segment.time;
                        setCurrentTime(segment.time);
                    }
                }}

              >
                <span className="transcript-time">
                  [{formatTime(segment.time)}]
                </span>
                <span className="transcript-text">{segment.text}</span>
              </div>
            ))
          ) : (
            <p className="transcript-empty-message">No transcript available...</p>
          )}
        </div>
      </div>

      {/* Tabset for Podcast Details */}
      <div className="podcast-details-tabs">
        <div className="tab-navigation">
          <div
            className={`tab-button ${activeTab === 'sources' ? 'active' : ''}`}
            onClick={() => setActiveTab('sources')}
            role="tab" // Accessibility
            aria-selected={activeTab === 'sources'} // Accessibility
            tabIndex={0} // Accessibility
            onKeyPress={(e) => e.key === 'Enter' && setActiveTab('sources')} // Accessibility
          >
            Sources
          </div>
          <div
            className={`tab-button ${activeTab === 'summary' ? 'active' : ''}`}
            onClick={() => setActiveTab('summary')}
            role="tab"
            aria-selected={activeTab === 'summary'}
            tabIndex={0}
            onKeyPress={(e) => e.key === 'Enter' && setActiveTab('summary')}
          >
            Summary
          </div>
          <div
            className={`tab-button ${activeTab === 'keywords' ? 'active' : ''}`}
            onClick={() => setActiveTab('keywords')}
            role="tab"
            aria-selected={activeTab === 'keywords'}
            tabIndex={0}
            onKeyPress={(e) => e.key === 'Enter' && setActiveTab('keywords')}
          >
            Search Keywords
          </div>
        </div>

        <div className="tab-content-container">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}

export default Play;