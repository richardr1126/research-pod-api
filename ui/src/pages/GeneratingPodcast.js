import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiService from '../services/apiService';

function GeneratingPodcast() {
  const { podId } = useParams();
  const navigate = useNavigate();
  
  // State variables
  const [status, setStatus] = useState('INITIALIZING');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('Starting podcast generation...');
  const [events, setEvents] = useState([]);
  const [podDetails, setPodDetails] = useState(null);
  const [error, setError] = useState('');
  const [eventSource, setEventSource] = useState(null);

  // Effect to start polling status when component mounts
  useEffect(() => {
    if (!podId) {
      setError('No podcast ID provided');
      return;
    }

    let statusInterval = null;
    let eventStreamConnected = false;

    // Poll for status until we get the events URL
    const pollStatus = async () => {
      try {
        const statusData = await apiService.checkStatus(podId);
        
        // Update status display
        setStatus(statusData.status);
        setProgress(statusData.progress || 0);
        setMessage(statusData.message || 'Processing...');
        
        // Connect to event stream once we have a valid events_url
        if (!eventStreamConnected && statusData.events_url) {
          console.log('Found events URL:', statusData.events_url);
          connectEventStream(statusData.events_url);
          eventStreamConnected = true;
          // Stop polling once event stream is connected
          clearInterval(statusInterval);
        }
        
        // If the status is already completed or error, fetch details and stop polling
        if (statusData.status === 'COMPLETED' || statusData.status === 'ERROR') {
          clearInterval(statusInterval);
          fetchPodDetails();
        }
      } catch (err) {
        console.error('Error polling status:', err);
        setError('Failed to get podcast status. Please try again later.');
        clearInterval(statusInterval);
      }
    };

    // Start polling
    pollStatus(); // Call immediately
    statusInterval = setInterval(pollStatus, 2000);

    // Cleanup function
    return () => {
      if (statusInterval) clearInterval(statusInterval);
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [podId]);

  // Function to connect to the EventSource
  const connectEventStream = (eventsUrl) => {
    if (!eventsUrl || eventsUrl === 'null') {
      console.error('Invalid events URL');
      return;
    }

    // Close existing event source if any
    if (eventSource) {
      eventSource.close();
    }

    const newEventSource = new EventSource(eventsUrl);
    setEventSource(newEventSource);
    
    newEventSource.onopen = () => {
      console.log('EventSource connected');
    };

    newEventSource.onmessage = (event) => {
      try {
        const eventData = JSON.parse(event.data);
        
        // Add new event to the events list (add to beginning for newest first)
        setEvents(prevEvents => [{
          timestamp: new Date().toISOString(),
          message: eventData.message || event.data
        }, ...prevEvents]);
        
        // Update status display from event data
        setStatus(eventData.status);
        setProgress(eventData.progress || 0);
        setMessage(eventData.message || 'Processing...');

        // Check for completion
        if (eventData.status === 'COMPLETED' || eventData.status === 'ERROR') {
          console.log('Pod processing complete, fetching details...');
          newEventSource.close();
          setEventSource(null);
          fetchPodDetails();
        }
      } catch (e) {
        console.error('Error parsing event data:', e);
        setEvents(prevEvents => [{
          timestamp: new Date().toISOString(),
          message: event.data
        }, ...prevEvents]);
      }
    };

    newEventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      newEventSource.close();
      setEventSource(null);
      
      // Only reconnect if podcast is still active and not completed
      if (podId && eventsUrl && status !== 'COMPLETED' && status !== 'ERROR') {
        setTimeout(() => connectEventStream(eventsUrl), 5000);
      }
    };
  };

  // Function to fetch podcast details
  const fetchPodDetails = async () => {
    try {
      const data = await apiService.getPodcast(podId);
      setPodDetails(data);
    } catch (err) {
      console.error('Error fetching podcast details:', err);
      setError('Failed to load podcast details. Please try again later.');
    }
  };

  // Function to handle going back to browse page
  const handleBackToBrowse = () => {
    navigate('/browse');
  };

  // Function to handle going to the podcast details page when complete
  const handleViewPodcast = () => {
    navigate(`/podcast/${podId}`);
  };

  // Render the component
  return (
    <div className="generating-container">
      <h2>Generating Your Podcast</h2>
      
      {error ? (
        <div className="error-message">
          {error}
          <button onClick={handleBackToBrowse} className="button-primary">
            Back to Browse
          </button>
        </div>
      ) : (
        <>
          <div className="status-card">
            <h3>Status: {status}</h3>
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <div className="progress-text">{progress}%</div>
            </div>
            <p className="status-message">{message}</p>
            
            {status === 'COMPLETED' && (
              <button onClick={handleViewPodcast} className="button-primary">
                View Your Podcast
              </button>
            )}
            
            {(status === 'ERROR' || status === 'COMPLETED') && (
              <button onClick={handleBackToBrowse} className="button-secondary">
                Back to Browse
              </button>
            )}
          </div>

          {podDetails && status === 'COMPLETED' && (
            <div className="pod-preview">
              <h3>Podcast Preview</h3>
              
              <h4>Search Keywords:</h4>
              <ul>
                {(podDetails.keywords_arxiv || []).map((group, index) => (
                  <li key={`keyword-group-${index}`}>{group.join(' | ')}</li>
                ))}
              </ul>

              <h4>Summary:</h4>
              
              <h4>Sources:</h4>
              <ul>
                {(podDetails.sources_arxiv || []).map((source, index) => (
                  <li key={`source-${index}`}>
                    <a href={source.url} target="_blank" rel="noopener noreferrer">
                      {source.title}
                    </a>
                  </li>
                ))}
              </ul>
              
              {podDetails.audio_url && (
                <>
                  <h4>Audio:</h4>
                  <audio controls>
                    <source src={podDetails.audio_url} type="audio/mpeg" />
                    Your browser does not support the audio element.
                  </audio>
                </>
              )}
            </div>
          )}

          <div className="events-container">
            <h3>Generation Log</h3>
            <div className="events-list">
              {events.length > 0 ? (
                events.map((event, index) => (
                  <div key={`event-${index}`} className="event">
                    <span className="event-time">{event.timestamp}</span>
                    <span className="event-message">{event.message}</span>
                  </div>
                ))
              ) : (
                <p>Waiting for events...</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default GeneratingPodcast;