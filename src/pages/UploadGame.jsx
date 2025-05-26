import React, { useState } from 'react';
import Header from '../components/Header';
import '../App.css';

function UploadGame() {
  const [genre, setGenre] = useState('');
  const [description, setDescription] = useState('');
  const [files, setFiles] = useState(null);

  const genres = ['Adventure', 'Puzzle', 'Fighting', 'Sports', 'Casual'];

  const handleUpload = () => {
    console.log('Genre:', genre);
    console.log('Description:', description);
    console.log('Files:', files);
    // Later: send data to backend
  };

  return (
    <div className="upload-container">
      <Header showProfileIcon customClass="auth-header" />

      <div className="upload-form">
       <select
        className={`upload-select ${genre ? 'selected' : ''}`}
        value={genre}
        onChange={(e) => setGenre(e.target.value)}
       >
        <option value="" disabled hidden>
         game genre
        </option>
        {genres.map((g, i) => (
         <option key={i} value={g}>{g}</option>
        ))}
       </select>


        <textarea
          className="upload-textarea"
          placeholder="description..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        <input
         type="file"
         className="upload-file-input"
         onChange={(e) => setFiles(e.target.files)}
         multiple
        />

        <button className="upload-btn" onClick={handleUpload}>
          <span className="material-symbols-outlined">upload</span>
          Upload
        </button>
      </div>
    </div>
  );
}

export default UploadGame;
