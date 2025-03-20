import React from 'react';
import { useLocation } from 'react-router-dom';
import '../App.css';

const NavigationSidebar = () => {
    const location = useLocation();
    
    // Determine active page based on current URL
    const getActivePage = (path) => {
      if (path === '/' || path.includes('/generating')) return 'generate';
      if (path === '/browse') return 'browse';
      return '';
    };
    
    const activePage = getActivePage(location.pathname);
    
    return (
      <div className="sidebar">
        <div className="logo">
          <h2>AI Podcast</h2>
        </div>
        <div className="navigation">
          <a href="/browse" className={`nav-button ${activePage === 'browse' ? 'active' : ''}`}>
            Browse Podcasts
          </a>
          <a href="/create" className={`nav-button ${activePage === 'create' ? 'active' : ''}`}>
            Generate New Podcast
          </a>
        </div>
      </div>
    );
  };
  
  export default NavigationSidebar;