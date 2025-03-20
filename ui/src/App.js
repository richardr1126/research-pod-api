import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import './App.css';
import NavigationSidebar from './components/NavigationSidebar';
import RecommenderSidebar from './components/RecommenderSidebar';
import Home from './pages/Home';
import Browse from './pages/Browse';
import Play from './pages/Play';
import GeneratingPodcast from './pages/GeneratingPodcast';


function App() {
  const location = useLocation();
  const path = location.pathname;

  const showRecommenderSidebar = path === '/' || path.includes('/Play') || path.includes('/generating');
  
  return (
    <Router>
      <div className="app">
        <NavigationSidebar />
        <main className="content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/browse" element={<Browse />} />
            <Route path="/Play/:jobId" element={<Play />} />
            <Route path="/generating/:jobId" element={<GeneratingPodcast />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        {showRecommenderSidebar && < RecommenderSidebar />}
      </div>
    </Router>
  );
}

export default App;