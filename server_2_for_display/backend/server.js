require('dotenv').config();
const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const fetch = require('node-fetch'); // For camera trigger
const app = express();

// Middleware setup
app.use(cors());
app.use(express.json());

// Configure PostgreSQL connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

// Database connection test
pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('Database connection error:', err);
  } else {
    console.log('Database connected at:', res.rows[0].now);
  }
});

// Fire prediction logic
async function predictFire(temperature, humidity, pressure) {
  try {
    const previousReadings = await pool.query(
      'SELECT temperature FROM sensor_data ORDER BY date_created DESC LIMIT 1 OFFSET 1'
    );

    if (previousReadings.rows.length === 0) {
      console.log("No prev data");
      if (temperature > 60 || (temperature > 50 && humidity < 30)) {
        return { risk: 'HIGH', message: 'Immediate fire risk detected!' };
      }
      if (temperature > 45 || humidity < 40) {
        return { risk: 'MEDIUM', message: 'Potential fire risk' };
      }
      return { risk: 'LOW', message: 'Normal conditions' };
    }

    const previousTemp = previousReadings.rows[0].temperature;
    const tempChange = temperature - previousTemp;

    if (tempChange >= 5) {
      return { risk: 'HIGH', message: `Sudden temperature rise of ${tempChange.toFixed(1)}°` };
    }
    if (tempChange >= 2) {
      return { risk: 'MEDIUM', message: `Temperature increased by ${tempChange.toFixed(1)}°` };
    }

    if (temperature > 55 || humidity < 25) {
      return { risk: 'MEDIUM', message: 'Extreme conditions may indicate fire risk' };
    }

    return {
      risk: 'LOW',
      message: `Normal conditions. Temperature change: ${tempChange.toFixed(1)}°`
    };
  } catch (err) {
    console.error('Error comparing temperature data:', err);
    return { risk: 'UNKNOWN', message: 'Unable to determine risk level due to error' };
  }
}

// Trigger ESP32-CAM capture
async function triggerCamera() {
  try {
    const response = await fetch('http://192.168.231.110/capture'); // Replace IP with your ESP32-CAM
    console.log('Camera triggered. Response status:', response.status);
  } catch (err) {
    console.error('Failed to trigger camera:', err.message);
  }
}

// API endpoint to fetch all sensor data
app.get('/api/data', async (req, res) => {
  try {
    console.log('Attempting to fetch data from Neon DB...');
    const result = await pool.query(
      'SELECT * FROM sensor_data ORDER BY date_created DESC'
    );
    console.log(`Fetched ${result.rowCount} rows`);
    res.json(result.rows);
  } catch (err) {
    console.error('Full error details:', err);
    res.status(500).json({
      error: 'Failed to fetch data',
      details: err.message
    });
  }
});

// Fire prediction and camera trigger endpoint
app.get('/api/predict', async (req, res) => {
  try {
    const latest = await pool.query(
      'SELECT * FROM sensor_data ORDER BY date_created DESC LIMIT 1'
    );

    if (latest.rows.length === 0) {
      return res.status(404).json({ error: 'No sensor data available' });
    }

    const { temperature, humidity, pressure } = latest.rows[0];
    const prediction = await predictFire(temperature, humidity, pressure);

    // Trigger camera for MEDIUM or HIGH
    if (['HIGH', 'MEDIUM'].includes(prediction.risk)) {
      console.log(`Triggering camera due to ${prediction.risk} risk`);
      await triggerCamera();
    }

    res.json({
      reading: latest.rows[0],
      prediction
    });
  } catch (err) {
    console.error('Prediction error:', err);
    res.status(500).json({
      error: 'Prediction failed',
      details: err.message
    });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    details: err.message
  });
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`API endpoints:
  - GET /api/data
  - GET /api/predict`);
});
