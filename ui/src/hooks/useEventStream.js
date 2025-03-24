import { useEffect, useState } from 'react';

// This custom hook manages an EventSource connection to a server for real-time updates.
const useEventStream= ({url, onStatusUpdate, onError}) => {
    const [isConnected, setConnected] = useState(false);

    useEffect(() => {
        if(!url) {
            onError?.({error: 'No URL provided for the event stream'});
            return;
        }

        let eventSource = null;

        try {
            eventSource = new EventSource(url);
            eventSource.onopen = () => {
                setConnected(true);
            }

            //Set up event listeners
            if (onStatusUpdate){
                try{
                    eventSource.addEventListener('status', (event) => {
                    const data = JSON.parse(event.data);
                    onStatusUpdate(data);
                });
                } catch (error) {
                    console.error('Error parsing status event:', error);
                    onError?.({error: 'Error parsing status event'});
                }
            }

            eventSource.onerror = (event) => {
                console.error('EventSource connection error:', event);
                onError?.({error: 'EventStream connection failed'});
                eventSource.close();
                setConnected(false);            }
        } catch (err) {
            console.error('Failed to create EventSource:', err);
            onError?.({error: 'Failed to create EventSource'});
        }

        return () => {
            if (eventSource) {
                eventSource.close();
                setConnected(false);
            }
        };
}, [url, onStatusUpdate]);
    return { isConnected };
};

export default useEventStream;