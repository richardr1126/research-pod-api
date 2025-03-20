import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/apiService';
function Browse() {
  const [podcasts, setPodcasts] = useState([]);
  const [filteredPodcasts, setFilteredPodcasts] = useState([]);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  
  // Load podcasts from local storage when component mounts
  useEffect(() => {
    const loadPodcasts = async () => {
        setIsLoading(true);
      try {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate a delay for loading podcasts
        // Mock podcast data
        const formattedPodcasts = () => [
          { id: 1, title: 'The Future of AI', duration: '25:43', date: '2025-03-05' },
          { id: 2, title: 'Space Exploration in 2025', duration: '32:17', date: '2025-03-01' },
          { id: 3, title: 'Climate Change Solutions', duration: '28:55', date: '2025-02-25' },
        ];
        setPodcasts(formattedPodcasts);
        setFilteredPodcasts(formattedPodcasts);
      } catch (error) {
        console.error('Error loading podcasts:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadPodcasts();
    
    // Set up a listener for storage changes (in case podcasts are added in another tab)
    const handleStorageChange = () => {
      loadPodcasts();
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);
  
  // Handle search
  const handleSearch = (e) => {
    const term = e.target.value;
    setQuery(term);
    
    if (!term.trim()) {
      setFilteredPodcasts(podcasts);
      return;
    }
    
    // Filter podcasts by title
    const filtered = podcasts.filter(podcast => 
      podcast.title.toLowerCase().includes(term.toLowerCase())
    );
    
    setFilteredPodcasts(filtered);
  };
  
  // Handle play button click
  const handlePlay = (podcastId) => {
    navigate(`/play/${podcastId}`);
  };
  
  // Mock function for download (would be implemented with actual file download in a real app)
  const handleDownload = (podcastId) => {
    alert(`Download functionality would be implemented here for podcast ID: ${podcastId}`);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    try {
      setIsGenerating(true);
      setError('');
      
      // Call the backend API to generate a podcast
      const result = await apiService.createPodcast(query);
      
      if (result.status === 'success') {
        // Store the job details locally
        localStorage.setItem('currentPodcastJob', JSON.stringify({
          jobId: result.job_id,
          query: query,
          timestamp: new Date().toISOString()
        }));
        
        // Navigate to the generating status page
        navigate(`/generating/${result.job_id}`);
      } else {
        setError('Failed to start podcast generation. Please try again.');
      }
    } catch (err) {
      console.error('Error generating podcast:', err);
      setError('An error occurred while connecting to the server. Please try again later.');
    } finally {
      setIsGenerating(false);
    }
  };
  
  return (
    <div className="browse-container">
      <h2>Browse Podcasts</h2>
      <div className="search-container">
        <form className="search-container-form" onSubmit={handleSubmit}>
        <textarea 
          placeholder="Search podcasts..." 
          className="search-input"
          value={query}
          onChange={handleSearch}
          rows="1"
        />
        <button 
          type="submit" 
          className="generate-button"
          disabled={isGenerating || !query.trim()}
        >
          {isGenerating ? 'Generating...' : 'Generate New Podcast'}
        </button>
        </form>
      </div>
      {error && <div className="error-message">{error}</div>}
      {isLoading ? (
        <div className="loading">Loading podcasts...</div>
      ) : filteredPodcasts.length > 0 ? (
        <div className="podcasts-list">
          {filteredPodcasts.map(podcast => (
            <div key={podcast.id} className="podcast-card">
              <h3>{podcast.title}</h3>
              <div className="podcast-details">
                <span>Duration: {podcast.duration}</span>
                <span>Generated on: {podcast.date}</span>
              </div>
              <div className="podcast-controls">
                <button 
                  className="play-button"
                  onClick={() => handlePlay(podcast.id)}
                >
                  Play
                </button>
                <button 
                  className="download-button"
                  onClick={() => handleDownload(podcast.id)}
                >
                  Download
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-podcasts">
          {query ? 'No podcasts match your search.' : 'No podcasts available. Generate your first podcast!'}
        </div>
      )}
    </div>
  );
}

export default Browse;