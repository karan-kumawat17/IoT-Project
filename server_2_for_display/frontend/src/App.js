import React from 'react';
import Dashboard from './components/Dashboard';
import FireDetectionCard from './components/FireDetectionCard';

function App() {
  return (
    <div>
      <h>Fire Detection Dashboard</h>

      <FireDetectionCard />

      <Dashboard />
    </div>
  );
}

export default App;
