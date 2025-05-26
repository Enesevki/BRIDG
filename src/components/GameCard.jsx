import React from 'react';
import { useNavigate } from 'react-router-dom';

function GameCard({ image, alt, id }) {
  const navigate = useNavigate();

  return (
    <div className="game-card">
      <img src={image} alt={alt} />
      <div className="game-hover-info">
        <p>Game Title</p>
        <p>Short description...</p>
      </div>
      <div
        className="play-icon"
        onClick={() => navigate(`/game/${id}`)}
        title="Play Game"
      >
        ▶
      </div>
    </div>
  );
}

export default GameCard;
