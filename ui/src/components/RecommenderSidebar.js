import React from 'react';
import '../App.css';

const RecommenderSidebar = () => {
  // Sample recommended podcasts data
  // In a real application, this would come from props or a context/state
  const recommendedPodcasts = [
    { id: '1', title: 'Tech Trends 2025', category: 'Technology' },
    { id: '2', title: 'History Uncovered', category: 'History' },
    { id: '3', title: 'Science Today', category: 'Science' },
    { id: '4', title: 'Business Insights', category: 'Business' },
    { id: '5', title: 'Creative Minds', category: 'Arts' },
  ];
  
  return (
    <div className="recommender-sidebar">
      <div className="recommender-header">
        <h3>Recommended For You</h3>
      </div>
      <div className="recommender-content">
        {recommendedPodcasts.map(podcast => (
          <div key={podcast.id} className="podcast-recommendation">
            <div className="podcast-thumbnail">
              {/* Placeholder for podcast thumbnail */}
              <div className="thumbnail-placeholder"></div>
            </div>
            <div className="podcast-info">
              <h4>{podcast.title}</h4>
              <p>{podcast.category}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="see-more">
        <a href="/browse">See More Recommendations</a>
      </div>
    </div>
  );
};

export default RecommenderSidebar;