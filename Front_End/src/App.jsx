import React from 'react';
import LandingPage from './components/LandingPage';
import ChatWidget from './components/ChatWidget';

function App() {
  return (
    <div className="relative min-h-screen bg-white font-sans">
      <LandingPage />
      <ChatWidget />
    </div>
  );
}

export default App;
