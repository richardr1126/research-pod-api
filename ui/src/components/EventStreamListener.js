import { useEffect, useState } from 'react';

const EventStreamListener = ({ url, onStatusUpdate, onPapersUpdate, onAnalysisUpdate, onError}) => {
    const [isConnected, setConnected] = useState(false);

    useEffect(() => {
        if (!url) {
            onError('No URL provided for the event stream');
            return;
        }

        const eventSource = new EventSource(url);
        eventSource.onopen = () =>{
            setConnected(true);
        }

        eventSource.addEventListener('status', (event) => {
            const data = JSON.parse(event.data);
            onStatusUpdate(data);
        });

        eventSource.addEventListener('papers', (event) => {
            const data = JSON.parse(event.data);
            onPapersUpdate(data);
        });
        eventSource.addEventListener('analysis', (event) => {
            const data = JSON.parse(event.data);
            onAnalysisUpdate(data);
        });
        eventSource.addEventListener('error', (event) => {
            const data = JSON.parse(event.data);
            onError(data);
        });

        eventSource.onerror = (event) => {
            console.error('EventSource error:', event);
            setConnected(false);
            eventSource.close();
        }

        return () => {
            eventSource.close();
            setConnected(false);
        };
    }, [url, onStatusUpdate, onPapersUpdate, onAnalysisUpdate, onError]);
    
    return { isConnected };
}
export default EventStreamListener;