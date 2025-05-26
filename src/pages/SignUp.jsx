import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import '../App.css';

function SignUp() {
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
