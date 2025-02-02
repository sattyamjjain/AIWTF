import React, { useState } from 'react';
import axios from 'axios';
import '../styles/ResearchForm.css';
import LoadingSpinner from './LoadingSpinner';
import ResearchResults from './ResearchResults';

const ResearchForm = () => {
  const [topic, setTopic] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResults([]);

    try {
      const response = await axios.post('http://localhost:8000/api/v1/research', { topic });
      setResults(response.data.sources || []);
    } catch (err) {
      setError('Error fetching research results. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="research-form-container">
      <h2>Research a Topic</h2>
      <form onSubmit={handleSubmit} className="research-form">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter topic to research"
          required
          className="research-input"
        />
        <button type="submit" className="search-button">
          Search
        </button>
      </form>
      {loading && <LoadingSpinner />}
      {error && <p className="error-message">{error}</p>}
      {results.length > 0 && <ResearchResults results={results} />}
    </div>
  );
};

export default ResearchForm; 