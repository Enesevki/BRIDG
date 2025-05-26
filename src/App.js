import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Home from './pages/Home';
import SignUp from './pages/SignUp';
import Profile from './pages/Profile';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/login" element={<h2 className="route-placeholder">Login Page (Coming Soon)</h2>} /> 
          <Route path="/profile" element={<Profile />} />        
          <Route path="/game/:id" element={<h2 className="route-placeholder">Game Page (Coming Soon)</h2>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
