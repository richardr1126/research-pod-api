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
        if (eventData.status === 'COMPLETED') {
          console.log('Pod processing complete...');
          newEventSource.close();
          setEventSource(null);
          // Navigate directly to the Play page when completed
          setTimeout(() => navigate(`/play/${podId}`), 1500);
        } else if (eventData.status === 'ERROR') {
          console.log('Pod processing failed...');
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
        
        // If the status is already completed, navigate to Play page
        if (statusData.status === 'COMPLETED') {
          clearInterval(statusInterval);
          setTimeout(() => navigate(`/play/${podId}`), 1500);
        } else if (statusData.status === 'ERROR') {
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

  const handleViewPodcast = () => {
    navigate(`/play/${podId}`);
  };

  // Component render functions
  const renderErrorState = () => (
    <div className="error-message" style={{ textAlign: 'center' }}>
      See generation log for error.
      <button onClick={navigate('/browse')} className="button-primary">
        Back to Browse
      </button>
    </div>
  );

  const renderStatusCard = () => (
    <div className="status-card" style={{ textAlign: 'center' }}>
      <h3>Status: {status}</h3>
      <div className="progress-container" style={{ 
        width: '80%', 
        margin: '0 auto 20px',
        position: 'relative'
      }}>
        <div className="progress-bar" style={{
          height: '20px',
          backgroundColor: '#f0f0f0',
          borderRadius: '10px',
          overflow: 'hidden',
          border: '1px solid #ccc'
        }}>
          <div 
            className="progress-fill" 
            style={{ 
              width: `${progress}%`,
              height: '100%',
              backgroundColor: '#4CAF50',
              transition: 'width 0.3s ease'
            }}
          ></div>
        </div>
        <div className="progress-text" style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          fontWeight: 'bold'
        }}>
          {progress}%
        </div>
      </div>
      <p className="status-message" style={{ margin: '0 auto 20px' }}>{message}</p>
      
      {status === 'COMPLETED' && (
        <button onClick={handleViewPodcast} className="button-primary">
          View Your Podcast
        </button>
      )}
      
      {(status === 'ERROR' || status === 'COMPLETED') && (
        <button onClick={navigate('/browse')} className="button-secondary" style={{ marginLeft: status === 'COMPLETED' ? '10px' : '0' }}>
          Back to Browse
        </button>
      )}
    </div>
  );

  const renderGenerationLog = () => (
    <div className="events-container" style={{ 
      textAlign: 'center',
      margin: '20px auto',
      maxWidth: '80%'
    }}>
      <div className="events-list" style={{ 
        backgroundColor: '#000',
        color: '#fff',
        height: '200px',
        overflow: 'auto',
        padding: '10px',
        borderRadius: '5px',
        textAlign: 'left',
        fontFamily: 'monospace'
      }}>
        {events.length > 0 ? (
          events.map((event, index) => (
            <div key={`event-${index}`} className="event" style={{ margin: '5px 0' }}>
              <span className="event-time" style={{ 
                color: '#8ff', 
                marginRight: '10px',
                fontSize: '0.9em'
              }}>
                {event.timestamp}
              </span>
              <span className="event-message">{event.message}</span>
            </div>
          ))
        ) : (
          <p style={{ textAlign: 'center' }}>Waiting for events...</p>
        )}
      </div>
    </div>
  );

  // Main render
  return (
    <div className="generating-container" style={{ 
      maxWidth: '800px', 
      margin: '0 auto',
      padding: '20px'
    }}>
      <h2 style={{ textAlign: 'center' }}>Generating Your Podcast</h2>
      
      {error ? (
        renderErrorState()
      ) : (
        <>
          {renderStatusCard()}
          {renderGenerationLog()}
        </>
      )}
    </div>
  );
}

export default GeneratingPodcast;