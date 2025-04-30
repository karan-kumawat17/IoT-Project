require('dotenv').config();
const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// PostgreSQL setup
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

// DB connection test
pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('Database connection error:', err);
  } else {
    console.log('Database connected at:', res.rows[0].now);
  }
});

// Predict fire logic
async function predictFire(temperature, humidity, pressure) {
  try {
    const previousReadings = await pool.query(
      'SELECT temperature FROM sensor_data ORDER BY date_created DESC LIMIT 1 OFFSET 1'
    );

    let previousTemp = previousReadings.rows.length ? previousReadings.rows[0].temperature : null;
    const tempChange = previousTemp !== null ? temperature - previousTemp : null;

    if (previousTemp === null) {
      if (temperature > 60 || (temperature > 50 && humidity < 30)) {
        return { risk: 'HIGH', message: 'Immediate fire risk detected!' };
      }
      if (temperature > 45 || humidity < 40) {
        return { risk: 'MEDIUM', message: 'Potential fire risk' };
      }
      return { risk: 'LOW', message: 'Normal conditions' };
    }

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

// Fetch all sensor data
app.get('/api/data', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM sensor_data ORDER BY date_created DESC');
    res.json(result.rows);
  } catch (err) {
    console.error('Error fetching data:', err);
    res.status(500).json({ error: 'Failed to fetch data', details: err.message });
  }
});

// Fire prediction endpoint
app.get('/api/predict', async (req, res) => {
  try {
    const latest = await pool.query('SELECT * FROM sensor_data ORDER BY date_created DESC LIMIT 1');

    if (latest.rows.length === 0) {
      return res.status(404).json({ error: 'No sensor data available' });
    }

    const { temperature, humidity, pressure } = latest.rows[0];
    const prediction = await predictFire(temperature, humidity, pressure);

    res.json({ reading: latest.rows[0], prediction });
  } catch (err) {
    console.error('Prediction error:', err);
    res.status(500).json({ error: 'Prediction failed', details: err.message });
  }
});

// Fetch image data
app.get('/api/images', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM image_data ORDER BY date_created DESC');
    res.json(result.rows);
  } catch (err) {
    console.error('Error fetching image data:', err);
    res.status(500).json({ error: 'Failed to fetch image data', details: err.message });
  }
});

// Global error handler
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error', details: err.message });
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🔥 Server running on port ${PORT}`);
  console.log(`Endpoints:
  - GET /api/data
  - GET /api/predict
  - GET /api/images`);
});
