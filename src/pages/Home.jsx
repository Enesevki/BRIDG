import React from 'react';
import Header from '../components/Header';
import CategoryBar from '../components/CategoryBar';
import GameGrid from '../components/GameGrid';

function Home() {
  return (
    <>
      <Header showSignUp />
      <CategoryBar />
      <GameGrid />
    </>
  );
}

export default Home;
