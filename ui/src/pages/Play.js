import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import apiService from '../services/apiService';

function Play() {
  const { jobId } = useParams();
  const audioRef = useRef(null);
  
  const [podcast, setPodcast] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [transcript, setTranscript] = useState([]);
  const [currentTranscript, setCurrentTranscript] = useState('');
  
  // Fetch podcast data when component mounts
  useEffect(() => {
    const fetchPodcast = async () => {
      try {
        setIsLoading(true);
        
        // Fetch podcast data directly from API
        const result = await apiService.checkStatus(jobId);
        
        if (result.status === 'COMPLETED') {
          setPodcast({
            id: jobId,
            title: result.query || 'Untitled Podcast',
            audioUrl: `/v1/api/podcast/${jobId}/audio`,
            transcriptUrl: `/v1/api/podcast/${jobId}/transcript`
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
  }, [jobId]);
  
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
  
  if (isLoading) return <div className="loading">Loading podcast...</div>;
  if (error) return <div className="error-message">{error}</div>;
  if (!podcast) return <div className="not-found">Podcast not found</div>;
  
  return (
    <div className="Play-container">
      <h2>{podcast.title}</h2>
      
      {/* Audio element (hidden) */}
      <audio 
        ref={audioRef}
        src={podcast.audioUrl} 
        preload="metadata"
      />
      
      {/* Custom player controls */}
      <div className="player-controls">
        <button 
          className={`play-button ${isPlaying ? 'pause' : 'play'}`}
          onClick={togglePlay}
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        
        <div className="time-display current-time">{formatTime(currentTime)}</div>
        
        <input 
          type="range" 
          min="0" 
          max="100" 
          value={(currentTime / duration) * 100 || 0}
          onChange={handleSeek}
          className="time-scrubber"
        />
        
        <div className="time-display duration">{formatTime(duration)}</div>
      </div>
      
      {/* Real-time transcript/captions */}
      <div className="transcript-container">
        <h3>Transcript</h3>
        <div className="current-transcript">{currentTranscript}</div>
        
        {/* Full transcript (scrollable) */}
        <div className="full-transcript">
          {transcript.map((segment, index) => (
            <div 
              key={index}
              className={`transcript-segment ${Math.abs(segment.time - currentTime) < 2 ? 'active' : ''}`}
              onClick={() => {
                if (audioRef.current) {
                  audioRef.current.currentTime = segment.time;
                  setCurrentTime(segment.time);
                }
              }}
            >
              <span className="transcript-time">[{formatTime(segment.time)}]</span>
              <span className="transcript-text">{segment.text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Play;