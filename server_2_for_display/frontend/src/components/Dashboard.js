import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { Grid, Card, CardContent, Typography, CircularProgress, CardMedia } from '@mui/material';

function Dashboard() {
  const [data, setData] = useState([]);
  const [latest, setLatest] = useState(null);
  const [loading, setLoading] = useState(true);

  const sortedData = [...data].sort((a, b) => new Date(a.date_created) - new Date(b.date_created));

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/data');
        const latestResponse = await axios.get('http://localhost:5000/api/predict');

        setData(response.data);
        setLatest(latestResponse.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <CircularProgress style={{ margin: '20% 50%' }} />;
  }

  return (
    <div style={{ padding: '20px', backgroundColor: '#f5f5f5' }}>

      <Typography variant="h4" gutterBottom style={{ color: '#2c3e50', marginBottom: 30 }}>
        Fire Detection Dashboard
      </Typography>

      {/* <Card 
        style={{
            marginBottom: 30, 
            borderRadius: 15, 
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)', 
            width: '700px' 
        }}
        >
        <CardMedia
            component="img"
            alt="Fire Detection"
            height="400" 
            image="https://media.istockphoto.com/id/507185368/photo/fire-in-a-house.jpg?s=1024x1024&w=is&k=20&c=FfOWMzgl70ujTWn-iXENhjcp52VmjA3IxKzVYbLsKoY="
            title="Fire Detection"
            style={{ borderRadius: '15px 15px 0 0', width: '100%' }}
        />
        </Card> */}



      <Grid container spacing={3} style={{ marginBottom: 30 }}>
        <Grid item xs={12} md={3}>
          <Card style={{ background: '#fff', borderRadius: 15, boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}>
            <CardContent>
              <Typography variant="h6" color="textSecondary">Temperature</Typography>
              <Typography variant="h4" style={{ color: '#e74c3c' }}>
                {latest?.reading?.temperature}°C
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card style={{
        background: latest?.prediction?.risk === 'HIGH' ? '#ffebee' :
                   latest?.prediction?.risk === 'MEDIUM' ? '#fff3e0' : '#e8f5e9',
        borderLeft: `5px solid ${latest?.prediction?.risk === 'HIGH' ? '#e53935' :
                    latest?.prediction?.risk === 'MEDIUM' ? '#fb8c00' : '#43a047'}`,
        marginBottom: 30
      }}>
        <CardContent>
          <Typography variant="h6">Fire Risk Status</Typography>
          <Typography variant="h4" style={{
            color: latest?.prediction?.risk === 'HIGH' ? '#e53935' :
                   latest?.prediction?.risk === 'MEDIUM' ? '#fb8c00' : '#43a047'
          }}>
            {latest?.prediction?.risk}
          </Typography>
          <Typography>{latest?.prediction?.message}</Typography>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        <Grid item xs={12} md={12}>
          <Card style={{ padding: 20, height: 400, borderRadius: 15, width: '100%' }}>
            <Typography variant="h6" gutterBottom>Temperature Trend</Typography>
            <ResponsiveContainer width="100%" height="90%">
              <LineChart data={sortedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date_created"
                  tickFormatter={time => new Date(time).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="temperature" stroke="#e74c3c" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Grid>

        <Grid item xs={12} md={12}>
          <Card style={{ padding: 20, height: 400, borderRadius: 15, width: '100%' }}>
            <Typography variant="h6" gutterBottom>Humidity Trend</Typography>
            <ResponsiveContainer width="100%" height="90%">
              <LineChart data={sortedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date_created"
                  tickFormatter={time => new Date(time).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="humidity" stroke="#3498db" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Grid>

        <Grid item xs={12} md={12}>
          <Card style={{ padding: 20, height: 400, borderRadius: 15, width: '100%' }}>
            <Typography variant="h6" gutterBottom>Pressure Trend</Typography>
            <ResponsiveContainer width="100%" height="90%">
              <LineChart data={sortedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date_created"
                  tickFormatter={time => new Date(time).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="pressure" stroke="#2ecc71" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
}

export default Dashboard;
