import { useEffect, useState, useRef } from 'react';

// This custom hook manages an EventSource connection to a server for real-time updates.
const useEventStream = ({ url, onStatusUpdate, onPapersUpdate, onAnalysisUpdate, onError }) => {
    const [isConnected, setConnected] = useState(false);
    const [lastEvent, setLastEvent] = useState(null);
    const [connectionAttempts, setConnectionAttempts] = useState(0);
    const eventSourceRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    // Clear any existing timeouts on unmount
    useEffect(() => {
        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, []);

    // Handle connection and reconnection
    useEffect(() => {
        // Clear any existing connection timeouts when URL changes
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        // Don't attempt to connect if no URL is provided
        if (!url) {
            console.log('No URL provided for the event stream');
            return;
        }

        // Close any existing connections when URL changes
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }

        // Attempt to connect to the event stream
        const connectEventSource = () => {
            console.log(`Connecting to event stream (attempt ${connectionAttempts + 1}):`, url);
            
            try {
                // Create new EventSource
                eventSourceRef.current = new EventSource(url);
                
                // Connection opened successfully
                eventSourceRef.current.onopen = () => {
                    console.log('EventSource connected successfully');
                    setConnected(true);
                    setConnectionAttempts(0); // Reset counter on successful connection
                };

                // Set up event listeners for different event types
                eventSourceRef.current.addEventListener('status', (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('Received status update:', data);
                        setLastEvent({ type: 'status', data });
                        if (onStatusUpdate) onStatusUpdate(data);
                    } catch (error) {
                        console.error('Error parsing status event:', error);
                        if (onError) onError({ error: 'Error parsing status event' });
                    }
                });

                eventSourceRef.current.addEventListener('papers', (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('Received papers update:', data);
                        setLastEvent({ type: 'papers', data });
                        if (onPapersUpdate) onPapersUpdate(data);
                    } catch (error) {
                        console.error('Error parsing papers event:', error);
                    }
                });

                eventSourceRef.current.addEventListener('analysis', (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('Received analysis update:', data);
                        setLastEvent({ type: 'analysis', data });
                        if (onAnalysisUpdate) onAnalysisUpdate(data);
                    } catch (error) {
                        console.error('Error parsing analysis event:', error);
                    }
                });

                // Handle regular message events
                eventSourceRef.current.onmessage = (event) => {
                    try {
                        console.log('Received message event:', event.data);
                        const data = JSON.parse(event.data);
                        setLastEvent({ type: 'message', data });
                        // Handle generic messages (could be status updates without event type)
                        if (data.status && onStatusUpdate) {
                            onStatusUpdate(data);
                        }
                    } catch (error) {
                        console.error('Error parsing message event:', error);
                    }
                };

                // Handle connection errors
                eventSourceRef.current.onerror = (error) => {
                    console.error('EventSource error:', error);
                    setConnected(false);
                    
                    // Close the failed connection
                    if (eventSourceRef.current) {
                        eventSourceRef.current.close();
                        eventSourceRef.current = null;
                    }
                    
                    // Increment connection attempts
                    setConnectionAttempts(prev => prev + 1);
                    
                    // Calculate backoff time (exponential with max of 10 seconds)
                    const backoffTime = Math.min(1000 * Math.pow(1.5, connectionAttempts), 10000);
                    console.log(`Will retry in ${backoffTime / 1000} seconds (attempt ${connectionAttempts + 1})`);
                    
                    // Notify about error
                    if (onError) onError({ 
                        error: 'EventStream connection failed', 
                        willRetry: true,
                        retryIn: backoffTime 
                    });
                    
                    // Schedule reconnection attempt with exponential backoff
                    reconnectTimeoutRef.current = setTimeout(() => {
                        reconnectTimeoutRef.current = null;
                        connectEventSource();
                    }, backoffTime);
                };
            } catch (err) {
                console.error('Failed to create EventSource:', err);
                if (onError) onError({ 
                    error: `Failed to create EventSource: ${err.message}`,
                    willRetry: true 
                });
                
                // Schedule reconnection attempt
                reconnectTimeoutRef.current = setTimeout(connectEventSource, 2000);
            }
        };

        // Initialize connection
        connectEventSource();

        // Clean up function to close the connection when component unmounts or URL changes
        return () => {
            console.log('Cleaning up EventSource connection');
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
                reconnectTimeoutRef.current = null;
            }
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
                eventSourceRef.current = null;
            }
            setConnected(false);
        };
    }, [url, connectionAttempts, onStatusUpdate, onPapersUpdate, onAnalysisUpdate, onError]);

    return { 
        isConnected, 
        lastEvent,
        connectionAttempts,
        reconnect: () => setConnectionAttempts(prev => prev + 1) // Force reconnection
    };
};

export default useEventStream;