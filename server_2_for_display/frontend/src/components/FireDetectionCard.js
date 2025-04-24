import React, { useState, useEffect } from "react";
import { Card, CardMedia, CardContent, Typography } from "@mui/material";

const FireDetectionCard = () => {
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Function to fetch the latest image
    const fetchImage = async () => {
      try {
        setLoading(true);
        // Add timestamp to prevent caching
        const imageEndpoint = `http://127.0.0.1:5000/latest-image?t=${Date.now()}`;
        setImageUrl(imageEndpoint);
        setLoading(false);
      } catch (err) {
        console.error("Error setting image:", err);
        setError("Failed to load image. Please try again.");
        setLoading(false);
      }
    };

    fetchImage();
    
    // Set up a refresh interval every 5 seconds
    const interval = setInterval(fetchImage, 5000);
    
    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, []);

  return (
    <Card style={{ width: 800, borderRadius: 15, boxShadow: "0 4px 20px rgba(0,0,0,0.1)", margin: "20px auto" }}>
      {loading ? (
        <div style={{ height: 500, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Typography>Loading...</Typography>
        </div>
      ) : error ? (
        <div style={{ height: 500, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Typography color="error">{error}</Typography>
        </div>
      ) : (
        <CardMedia
          component="img"
          height="600"
          image={imageUrl}
          alt="Fire Detection Image"
        />
      )}
      <CardContent>
        <Typography variant="h6" align="center">
          Fire Detection Image
        </Typography>
      </CardContent>
    </Card>
  );
};

export default FireDetectionCard;