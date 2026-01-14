import React from 'react';
import LandingPage from './components/LandingPage';
import ChatWidget from './components/ChatWidget';
import ChatInterface from './components/ChatInterface';

function App() {
  // Mode 'chat' = Full screen application (like ChatGPT)
  // Mode 'widget' = Landing page + Widget (Showcase)
  // Default to widget if not specified
  const mode = import.meta.env.VITE_APP_MODE || 'widget';

  if (mode === 'chat') {
    return (
      <div className="flex h-screen bg-white overflow-hidden font-sans">
        <div className="flex-1 flex flex-col min-w-0 bg-white">
          <ChatInterface />
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-white font-sans">
      <LandingPage />
      <ChatWidget />
    </div>
  );
}

export default App;
