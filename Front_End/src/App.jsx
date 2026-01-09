import React from 'react';
import ChatInterface from './components/ChatInterface';

function App() {
  return (
    <div className="flex h-screen bg-white overflow-hidden font-sans">
      <main className="flex-1 flex flex-col min-w-0 bg-white">
        <ChatInterface />
      </main>
    </div>
  );
}

export default App;
