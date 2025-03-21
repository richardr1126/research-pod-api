import { useEffect, useState } from 'react';

// This custom hook manages an EventSource connection to a server for real-time updates.
const useEventStream= ({url, onStatusUpdate, onPapersUpdate, onAnalysisUpdate, onError}) => {
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

            if (onPapersUpdate){
                try{
                    eventSource.addEventListener('papers', (event) => {
                    const data = JSON.parse(event.data);
                    onPapersUpdate(data);
                });
                } catch (error) {
                    console.error('Error parsing papers event:', error);
                    onError?.({error: 'Error parsing papers event'});
                }
            }

            if (onAnalysisUpdate){
                try{
                    eventSource.addEventListener('analysis', (event) => {
                    const data = JSON.parse(event.data);
                    onAnalysisUpdate(data);
                });
                } catch (error) {
                    console.error('Error parsing analysis event:', error);
                    onError?.({error: 'Error parsing analysis event'});
                }
            }

            if (onError){
                eventSource.addEventListener('error', (event) => {
                    const data = JSON.parse(event.data);
                    onError?.(data);
                });
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
}, [url, onStatusUpdate, onPapersUpdate, onAnalysisUpdate, onError]);
    return { isConnected };
};

export default useEventStream;