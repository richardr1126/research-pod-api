import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/apiService';

function Create() {
  const [query, setQuery] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  
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
    <div className="generate-container">
      <h2>Generate a New Podcast</h2>
      <p>Enter a topic or question to create an AI-generated podcast</p>
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="E.g., The history of jazz music, or Latest advancements in renewable energy..."
          rows={5}
          className="query-input"
        />
        
        <button 
          type="submit" 
          className="generate-button"
          disabled={isGenerating || !query.trim()}
        >
          {isGenerating ? 'Generating...' : 'Generate Podcast'}
        </button>
      </form>
    </div>
  );
}

export default Create;