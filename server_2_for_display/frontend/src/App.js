import React from 'react';
import Dashboard from './components/Dashboard';
import FireDetectionCard from './components/FireDetectionCard';
import { Typography } from '@mui/material';

function App() {
  return (
    <div>
      <Typography variant="h4" gutterBottom style={{ color: '#2c3e50', marginBottom: 30 }}>
        Fire Detection Dashboard
      </Typography>

      <FireDetectionCard />

      <Dashboard />
    </div>
  );
}

export default App;
