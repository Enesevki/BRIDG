import React from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../assets/logo.png';

function Header({ showSignUp = false, showProfileIcon = false, customClass = '' }) {
  const navigate = useNavigate();

  return (
    <header className={`header ${customClass}`}>
      <img
        src={logo}
        alt="Logo"
        className="logo clickable"
        onClick={() => navigate('/')}
      />

      {showSignUp && (
        <button className="signup-btn" onClick={() => navigate('/signup')}>
          Sign Up →
        </button>
      )}

      {showProfileIcon && (
        <div className="user-icon" onClick={() => navigate('/profile')}>
          <span className="material-symbols-outlined">account_circle</span>
        </div>
      )}
    </header>
  );
}

export default Header;
