import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

function PodcastCard({ podcast }) {

    const [showSources, setShowSources] = useState(false);

    const navigate = useNavigate();

    // Handle play button click
    const onPlay = () => {
        navigate(`/play/${podcast.pod_id}`);
    };

    // Mock function for download (would be implemented with actual file download in a real app)
    const onDownload = () => {
        alert(`Download functionality would be implemented here for podcast ID: ${podcast.pod_id}`);
    };

    //Mock function to handle opening sources
    const onToggleSources = () => {
        setShowSources(!showSources);
    };

    return (
        <div className="podcast-card" key={podcast.pod_id}>
            <h3>{podcast.title}</h3>
            <div className="podcast-details">
                <span>Duration: {podcast.duration}</span>
                <span>Generated on: {podcast.date}</span>
            </div>
            <div className="podcast-controls">
                <button
                    className="play-button"
                    onClick={() => onPlay(podcast.podId)}
                >
                    Play
                </button>
                <button
                    className="download-button"
                    onClick={() => onDownload()}
                >
                    Download
                </button>
                <button
                    className="sources-button"
                    onClick={() => onToggleSources()}
                >
                    Sources
                </button>
            </div>
            {showSources && podcast.sources && (
                <div className="sources-list">
                    <h4>Sources:</h4>
                    <ul className="sources-list">
                        {podcast.sources.map((source, index) => (
                            <li key={index}>
                                <Link to={source.url}>
                                    {source.title}
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export default PodcastCard;