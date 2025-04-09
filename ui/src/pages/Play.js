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
            sources: result.sources_arxiv || []
          });
          
          // In a real implementation, you'd fetch the transcript from the API
          // For now using mock data
          setTranscript([
            { time: 0, text: "Welcome to this AI generated podcast." },
            { time: 5, text: "Today we're exploring the topic you requested." },
            { time: 10, text: "Let's dive into the details." }
          ]);
        } else {
          setError('This podcast is not ready yet. Please check back later.');
        }
      } catch (err) {
        console.error('Error fetching podcast:', err);
        setError('Failed to load podcast. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchPodcast();
  }, [podId]);
  
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
        }
      };
      
      const handleLoadedMetadata = () => {
        setDuration(audio.duration);
      };
      
      const handlePlay = () => setIsPlaying(true);
      const handlePause = () => setIsPlaying(false);
      const handleEnded = () => setIsPlaying(false);
      
      audio.addEventListener('timeupdate', handleTimeUpdate);
      audio.addEventListener('loadedmetadata', handleLoadedMetadata);
      audio.addEventListener('play', handlePlay);
      audio.addEventListener('pause', handlePause);
      audio.addEventListener('ended', handleEnded);
      
      return () => {
        audio.removeEventListener('timeupdate', handleTimeUpdate);
        audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
        audio.removeEventListener('play', handlePlay);
        audio.removeEventListener('pause', handlePause);
        audio.removeEventListener('ended', handleEnded);
      };
    }
  }, [audioRef, podcast, transcript]);
  
  // Toggle play/pause
  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
    }
  };
  
  // Seek to a specific position
  const handleSeek = (e) => {
    if (audioRef.current) {
      const seekTime = (e.target.value / 100) * duration;
      audioRef.current.currentTime = seekTime;
      setCurrentTime(seekTime);
    }
  };
  
  // Format time (mm:ss)
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
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
            <ul style={{ 
              listStyle: 'none', 
              padding: 0,
              maxWidth: '80%',
              margin: '0 auto'
            }}>
              {(podcast.sources || []).map((source, index) => (
                <li key={`source-${index}`}>
                  <a href={source.url} target="_blank" rel="noopener noreferrer">
                    {source.title || source.url || `Source ${index + 1}`}
                  </a>
                </li>
              ))}
            </ul>
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
            <ul style={{ 
              listStyle: 'none', 
              padding: 0,
              maxWidth: '80%',
              margin: '0 auto'
            }}>
              {(podcast.keywords || []).map((group, index) => (
                <li key={`keyword-group-${index}`}>{Array.isArray(group) ? group.join(' | ') : group}</li>
              ))}
            </ul>
          </div>
        );
      default:
        return null;
    }
  };
  
  if (isLoading) return <div className="loading" style={{ textAlign: 'center', padding: '40px' }}>Loading podcast...</div>;
  if (error) return <div className="error-message" style={{ textAlign: 'center', padding: '40px', color: 'red' }}>{error}</div>;
  if (!podcast) return <div className="not-found" style={{ textAlign: 'center', padding: '40px' }}>Podcast not found</div>;
  
  return (
    <div className="Play-container" style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2 style={{ textAlign: 'center' }}>{podcast.title}</h2>
      
      {/* Audio element (hidden) */}
      <audio 
        ref={audioRef}
        src={podcast.audioUrl} 
        preload="metadata"
      />
      
      {/* Custom player controls */}
      <div className="player-controls" style={{ 
        margin: '20px 0',
        padding: '15px',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px'
      }}>
        {/* Time display and seek bar */}
        <div className="time-controls" style={{
          display: 'flex',
          alignItems: 'center',
          marginBottom: '15px'
        }}>
          <div className="time-display current-time" style={{ minWidth: '45px', textAlign: 'right', marginRight: '10px' }}>
            {formatTime(currentTime)}
          </div>
          
          <input 
            type="range" 
            min="0" 
            max="100" 
            value={(currentTime / duration) * 100 || 0}
            onChange={handleSeek}
            className="time-scrubber"
            style={{ 
              flex: 1, 
              height: '8px', 
              borderRadius: '4px',
              appearance: 'none',
              backgroundColor: '#ddd'
            }}
          />
          
          <div className="time-display duration" style={{ minWidth: '45px', marginLeft: '10px' }}>
            {formatTime(duration)}
          </div>
        </div>
        
        {/* Play button centered below the seek bar */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button 
            className={`play-button ${isPlaying ? 'pause' : 'play'}`}
            onClick={togglePlay}
            style={{
              width: '60px',
              height: '60px',
              borderRadius: '50%',
              backgroundColor: isPlaying ? '#ff5555' : '#4CAF50',
              color: 'white',
              border: 'none',
              fontSize: '16px',
              cursor: 'pointer'
            }}
          >
            {isPlaying ? 'Pause' : 'Play'}
          </button>
        </div>
      </div>
      
      {/* Current transcript line */}
      <div className="current-transcript" style={{ 
        backgroundColor: '#eef8ff', 
        padding: '15px', 
        borderRadius: '8px',
        marginBottom: '20px',
        textAlign: 'center',
        fontSize: '18px',
        minHeight: '30px'
      }}>
        {currentTranscript}
      </div>
      
      {/* Full transcript (styled like the log in GeneratingPodcast.js) */}
      <div className="transcript-container">
        <h3 style={{ textAlign: 'center' }}>Transcript</h3>
        <div className="transcript-log" style={{ 
          backgroundColor: '#000',
          color: '#fff',
          height: '200px',
          overflow: 'auto',
          padding: '10px',
          borderRadius: '5px',
          textAlign: 'left',
          fontFamily: 'monospace',
          marginBottom: '20px'
        }}>
          {transcript.length > 0 ? (
            transcript.map((segment, index) => (
              <div 
                key={index}
                className={`transcript-segment ${Math.abs(segment.time - currentTime) < 2 ? 'active' : ''}`}
                onClick={() => {
                  if (audioRef.current) {
                    audioRef.current.currentTime = segment.time;
                    setCurrentTime(segment.time);
                  }
                }}
                style={{ 
                  margin: '5px 0',
                  cursor: 'pointer',
                  backgroundColor: Math.abs(segment.time - currentTime) < 2 ? '#333' : 'transparent',
                  padding: '5px',
                  borderRadius: '3px'
                }}
              >
                <span className="transcript-time" style={{ 
                  color: '#8ff',
                  marginRight: '10px',
                  fontSize: '0.9em'
                }}>
                  [{formatTime(segment.time)}]
                </span>
                <span className="transcript-text">{segment.text}</span>
              </div>
            ))
          ) : (
            <p style={{ textAlign: 'center' }}>No transcript available...</p>
          )}
        </div>
      </div>
      
      {/* Tabset for Podcast Details */}
      <div className="podcast-details-tabs">
        <div className="tab-navigation" style={{
          display: 'flex',
          borderBottom: '1px solid #ddd',
          marginBottom: '15px'
        }}>
          <div 
            className={`tab-button ${activeTab === 'sources' ? 'active' : ''}`}
            onClick={() => setActiveTab('sources')}
            style={{
              padding: '10px 15px',
              cursor: 'pointer',
              backgroundColor: activeTab === 'sources' ? '#f0f0f0' : 'transparent',
              borderTopLeftRadius: '8px',
              borderTopRightRadius: '8px',
              borderTop: activeTab === 'sources' ? '1px solid #ddd' : 'none',
              borderLeft: activeTab === 'sources' ? '1px solid #ddd' : 'none',
              borderRight: activeTab === 'sources' ? '1px solid #ddd' : 'none',
              marginRight: '5px',
              fontWeight: activeTab === 'sources' ? 'bold' : 'normal'
            }}
          >
            Sources
          </div>
          <div 
            className={`tab-button ${activeTab === 'summary' ? 'active' : ''}`}
            onClick={() => setActiveTab('summary')}
            style={{
              padding: '10px 15px',
              cursor: 'pointer',
              backgroundColor: activeTab === 'summary' ? '#f0f0f0' : 'transparent',
              borderTopLeftRadius: '8px',
              borderTopRightRadius: '8px',
              borderTop: activeTab === 'summary' ? '1px solid #ddd' : 'none',
              borderLeft: activeTab === 'summary' ? '1px solid #ddd' : 'none',
              borderRight: activeTab === 'summary' ? '1px solid #ddd' : 'none',
              marginRight: '5px',
              fontWeight: activeTab === 'summary' ? 'bold' : 'normal'
            }}
          >
            Summary
          </div>
          <div 
            className={`tab-button ${activeTab === 'keywords' ? 'active' : ''}`}
            onClick={() => setActiveTab('keywords')}
            style={{
              padding: '10px 15px',
              cursor: 'pointer',
              backgroundColor: activeTab === 'keywords' ? '#f0f0f0' : 'transparent',
              borderTopLeftRadius: '8px',
              borderTopRightRadius: '8px',
              borderTop: activeTab === 'keywords' ? '1px solid #ddd' : 'none',
              borderLeft: activeTab === 'keywords' ? '1px solid #ddd' : 'none',
              borderRight: activeTab === 'keywords' ? '1px solid #ddd' : 'none',
              fontWeight: activeTab === 'keywords' ? 'bold' : 'normal'
            }}
          >
            Search Keywords
          </div>
        </div>
        
        <div className="tab-content-container" style={{
          padding: '15px',
          backgroundColor: '#f0f0f0',
          borderBottomLeftRadius: '8px',
          borderBottomRightRadius: '8px',
          borderLeft: '1px solid #ddd',
          borderRight: '1px solid #ddd',
          borderBottom: '1px solid #ddd'
        }}>
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}

export default Play;