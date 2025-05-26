import React from 'react';
import logo from '../assets/logo.jpg';
import { useNavigate } from 'react-router-dom';

const Header = () => {
  const navigate = useNavigate();

  return (
    <header className="header">
      <img src={logo} alt="Logo" className="logo" onClick={() => navigate('/')} />
      <button className="signup-btn" onClick={() => navigate('/signup')}>Sign Up →</button>
    </header>
  );
};

export default Header;
