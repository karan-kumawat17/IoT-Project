import React, { useEffect, useState } from "react";
import { Card, CardMedia, CardContent, Typography } from "@mui/material";

const FireDetectionCard = () => {
  const [imageUrl, setImageUrl] = useState(null);
  const [fireDetected, setFireDetected] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/detect-fire")
      .then((res) => res.json())
      .then((data) => {
        setImageUrl(`http://localhost:8000${data.image_path}`);
        setFireDetected(data.fire_detected);
      });
  }, []);

  return (
    <Card style={{ width: 400, borderRadius: 15, boxShadow: "0 4px 20px rgba(0,0,0,0.1)", margin: "20px auto" }}>
      {imageUrl && (
        <CardMedia
          component="img"
          height="300"
          image={imageUrl}
          alt="Fire Detection Result"
        />
      )}
      <CardContent>
        <Typography variant="h6" align="center">
          Fire Detected: {fireDetected ? "🔥 Yes" : "✅ No"}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default FireDetectionCard;
