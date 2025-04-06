import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../../services/apiService';
import PodcastCard from './PodcastCard';

function Browse() {
  const [podcasts, setPodcasts] = useState([]);
  const [filteredPodcasts, setFilteredPodcasts] = useState([]);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  
  // Load podcasts from API when component mounts
  useEffect(() => {
    const loadPodcasts = async () => {
      setIsLoading(true);
      try {
        // In a real implementation, you would fetch this from the API
        // For now, we'll use mock data
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
        
        const formattedPodcasts = [
          { 
            pod_id: "pod-1", 
            title: 'The Future of AI', 
            duration: '25:43', 
            date: '2025-03-05', 
            sources: [
              { title: 'MIT Technology Review: AI Advancements', url: 'https://example.com/mit-ai-review' },
              { title: 'Stanford AI Lab Research', url: 'https://example.com/stanford-ai-lab' },
              { title: 'Nature: Machine Learning Special', url: 'https://example.com/nature-ml' }
            ] 
          },
          { 
            pod_id: "pod-2", 
            title: 'Space Exploration in 2025', 
            duration: '32:17', 
            date: '2025-03-01', 
            sources: [
              { title: 'NASA Official Reports', url: 'https://example.com/nasa-reports' },
              { title: 'SpaceX Mission Updates', url: 'https://example.com/spacex-updates' },
              { title: 'Astrophysics Journal', url: 'https://example.com/astrophysics-journal' }
            ]
          },
          { 
            pod_id: "pod-3", 
            title: 'Climate Change Solutions', 
            duration: '28:55', 
            date: '2025-02-25', 
            sources: [
              { title: 'IPCC Latest Reports', url: 'https://example.com/ipcc-reports' },
              { title: 'Environmental Science & Technology', url: 'https://example.com/env-sci-tech' },
              { title: 'Global Climate Action Summit', url: 'https://example.com/climate-summit' }
            ] 
          },
        ];
        
        setPodcasts(formattedPodcasts);
        setFilteredPodcasts(formattedPodcasts);
      } catch (error) {
        console.error('Error loading podcasts:', error);
        setError('Failed to load podcasts. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadPodcasts();
  }, []);
  
  // Filter podcasts based on search query
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

  // Generate a new podcast from the search query
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    try {
      setIsGenerating(true);
      setError('');
      
      console.log('Generating podcast for query:', query);
      const result = await apiService.createPodcast(query);
      console.log('API response:', result);
      
      if (result.status === 'success' || result.pod_id) {
        // Navigate to the generating status page
        navigate(`/generating/${result.pod_id}`);
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
        <form onSubmit={handleSubmit}>
          <textarea 
            placeholder="Search podcasts..." 
            className="search-input"
            value={query}
            onChange={handleSearch}
            rows={1}
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
            <PodcastCard
              key={`podcast-${podcast.pod_id}`}
              podcast={podcast}
            />
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