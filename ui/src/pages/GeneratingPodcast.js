import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiService from '../services/apiService';
import useEventStream from '../hooks/useEventStream';

function GeneratingPodcast() {
  const { podId } = useParams();
  const navigate = useNavigate();
  
  const [status, setStatus] = useState('QUEUED');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('Initializing podcast generation...');
  const [eventStreamUrl, setEventStreamUrl] = useState(null);
  const [podcastData, setPodcastData] = useState(null);
  const [error, setError] = useState(null);
  
  // Initial check for job status to get the event stream URL
  useEffect(() => {
    const checkJobStatus = async () => {
      try {
        const result = await apiService.checkStatus(podId);
        
        setStatus(result.status);
        setProgress(result.progress || 0);
        
        // Handle error status from the API
        if (result.status === 'ERROR') {
          setError('The server reported an error with this podcast generation');
          return;
        }

        // If completed, navigate directly to the podcast player
        if (result.status === 'COMPLETED') {
          navigate(`/play/${podId}`);
          return;
        }
        
        if (result.events_url) {
          setEventStreamUrl(result.events_url);
        } else {
          // If no events_url yet, poll again after a short delay
          setTimeout(checkJobStatus, 2000);
        }
      } catch (err) {
        setError('Failed to connect to the server');
        console.error(err);
      }
    };
    
    checkJobStatus();
  }, [podId, navigate]);
  
  // Handle status updates from EventStreamListener
  const handleStatusUpdate = (data) => {
    setStatus(data.status);
    setProgress(data.progress);
    setMessage(data.message);
    
    // If completed, navigate to the podcast player
    if (data.status === 'COMPLETED') {
      setTimeout(() => {
        navigate(`/watch/${podId}`);
      }, 1500); // Short delay to show completion
    }
  };

  const handleError= (data) => {
    setError(data.error);
    setStatus('ERROR');
  };
  
  // useEventStream to listen to EventStream updates
  const {isConnected } = useEventStream(
    {
      url: eventStreamUrl,
      onStatusUpdate: handleStatusUpdate,
      onError: handleError 
    }
  );
  // Function to cancel generation
  const handleCancel = () => {
    // Simple navigation back to home, no history to update
    navigate('/');
  };
  
  return (
    <div className="generating-container">
      <h2>Generating Your Podcast</h2>
      
      <div className="connection-status">
        {eventStreamUrl && (
          <span className={`connection-indicator-${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? 'Connected to EventStream' : 'Connecting...'}
          </span>
        )}
        </div>
      
      <div className="status-display">
        <div className="progress-bar-container">
          <div 
            className="progress-bar" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <p className="status-message">{message}</p>
        <p className="status-percent">{progress}% Complete</p>
      </div>
      
      {status === 'ERROR' ? (
        <div className="error-container">
          <p className="error-message">Error: {error}</p>
          <button 
            onClick={() => navigate('/')}
            className="retry-button"
          >
            Return Home
          </button>
        </div>
      ) : (
        <button 
          onClick={handleCancel}
          className="cancel-button"
        >
          Cancel
        </button>
      )}
      
      {/* Show preview of what's being generated */}
      {podcastData && podcastData.papers && (
        <div className="preview-container">
          <h3>Sources Being Analyzed</h3>
          <ul className="papers-list">
            {podcastData.papers.map((paper, index) => (
              <li key={index} className="paper-item">
                {paper.title || paper}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {podcastData && podcastData.analysis && (
        <div className="analysis-preview">
          <h3>Podcast Preview</h3>
          <div className="analysis-content">
            {podcastData.analysis.key_findings && (
              <p>{podcastData.analysis.key_findings}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default GeneratingPodcast;