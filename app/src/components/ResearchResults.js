import React from 'react';
import '../styles/ResearchResults.css';

const ResearchResults = ({ results }) => {
  return (
    <div className="research-results">
      <h3>Research Results</h3>
      <ul>
        {results.map((result, index) => (
          <li key={index}>
            <a href={result.url} target="_blank" rel="noopener noreferrer">
              {result.title}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ResearchResults; 