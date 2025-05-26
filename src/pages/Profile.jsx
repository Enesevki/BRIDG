import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import '../App.css';

function Profile() {
  const navigate = useNavigate();

  return (
    <div className="profile-container">
      <Header showProfileIcon />

      <div className="profile-buttons">
        <button className="profile-btn">
            <span className="material-symbols-outlined">person</span>
            User Info
        </button>

        <button className="profile-btn">
            <span className="material-symbols-outlined">favorite</span>
            Liked Games
        </button>

        <button className="profile-btn">
            <span className="material-symbols-outlined">upload</span>
            Upload a Game
        </button>

        <button className="logout-btn">
            <span className="material-symbols-outlined">logout</span>
            Log out
        </button>
      </div>
    </div>
  );
}

export default Profile;
