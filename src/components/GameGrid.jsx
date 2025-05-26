import React from 'react';
import GameCard from './GameCard';
import placeholder from '../assets/placeholder.webp';

function GameGrid() {
  const numCards = 6;

  return (
    <div className="game-grid">
      {Array.from({ length: numCards }).map((_, index) => (
        <GameCard
          key={index}
          id={index + 1}
          image={placeholder}
          alt={`Game ${index + 1}`}
        />
      ))}
    </div>
  );
}

export default GameGrid;
