import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import NavigationSidebar from './components/NavigationSidebar';
import RecommenderSidebar from './components/RecommenderSidebar';
import Create from './pages/Create';
import Browse from './pages/browse/Browse';
import Play from './pages/Play';
import GeneratingPodcast from './pages/GeneratingPodcast';

// Separate AppContent component to handle layout logic within the <Router>
function AppContent() { 
  return (
      <div className="app">
        <NavigationSidebar />
        <main className="content">
          <Routes>
            <Route path="/create" element={<Create />} />
            <Route path="/browse" element={<Browse />} />
            <Route path="/Play/:podId" element={<Play />} />
            <Route path="/generating/:podId" element={<GeneratingPodcast />} />
            <Route path="*" element={<Navigate to="/browse" replace />} />
          </Routes>
        </main>
       < RecommenderSidebar />
      </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;