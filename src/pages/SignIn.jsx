
import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import '../App.css';

function SignIn() {
  const navigate = useNavigate();

  return (
    <div className="signup-container">
      <Header showProfileIcon customClass="auth-header" />

      <div className="signup-form">
        <button className="google-signup-btn">
          <img
            src="https://www.svgrepo.com/show/475656/google-color.svg"
            alt="Google logo"
            className="google-icon"
          />
          Sign in with Google
        </button>

        <input type="email" placeholder="e-mail" />
        <input type="password" placeholder="password" />

        <button className="submit-btn">Sign in</button>

        <p className="login-link">
          Don't have an account?{' '}
          <span onClick={() => navigate('/signup')} className="link-text">
            Sign up
          </span>
        </p>
      </div>
    </div>
  );
}

export default SignIn;
