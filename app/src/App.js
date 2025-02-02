import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import ResearchForm from './components/ResearchForm';
import './styles/App.css';

const App = () => {
  return (
    <Router>
      <div className="app-container">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<ResearchForm />} />
            <Route
              path="/about"
              element={
                <div className="about-page">
                  <h2>About Research Assistant</h2>
                  <p>This app allows you to research topics by searching the web, extracting content, and synthesizing findings.</p>
                </div>
              }
            />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
};

export default App; 