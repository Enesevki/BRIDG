import React from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../assets/logo.jpg'; // use your actual logo later
import '../App.css'; // reuse global styles

function SignUp() {
  const navigate = useNavigate();

  return (
    <div className="signup-container">
      <header className="signup-header">
        <img
          src={logo}
          alt="Logo"
          className="logo clickable"
          onClick={() => navigate('/')}
        />
        <div className="user-icon" onClick={() => navigate('/profile')}>
          <span role="img" aria-label="profile">👤</span>
        </div>
      </header>

      <div className="signup-form">
        <button className="google-signup-btn">
          <img
            src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg"
            alt="Google logo"
            className="google-icon"
          />
          Sign up with Google
        </button>

        <input type="text" placeholder="username" />
        <input type="email" placeholder="e-mail" />
        <input type="password" placeholder="password" />

        <button className="submit-btn">Sign up</button>

        <p className="login-link">
          Already have an account?{' '}
          <span onClick={() => navigate('/login')} className="link-text">
            Sign in
          </span>
        </p>
      </div>
    </div>
  );
}

export default SignUp;
