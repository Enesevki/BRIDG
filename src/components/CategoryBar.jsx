import React from 'react';

const categories = ['Adventure', 'Puzzle', 'Fighting', 'Sports', 'Casual'];

function CategoryBar() {
  const handleClick = (category) => {
    alert(`Category clicked: ${category}`);
  };

  return (
    <div className="category-bar">
      {categories.map((cat) => (
        <button
          key={cat}
          className="category-btn"
          onClick={() => handleClick(cat)}
        >
          {cat}
        </button>
      ))}
    </div>
  );
}

export default CategoryBar;
