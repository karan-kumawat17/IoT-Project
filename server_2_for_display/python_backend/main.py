from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
import io
from PIL import Image
import base64
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL connection
conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')
cursor = conn.cursor()

@app.get("/api/images")
def get_images():
    try:
        cursor.execute("SELECT id, device_id, filename, timestamp, filepath, sensor_data_id, is_fire_hazard FROM image_data ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images/latest")
def get_latest_image():
    try:
        cursor.execute("SELECT image_binary, is_fire_hazard FROM image_data ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No image data found")

        image_binary, is_fire_hazard = row
        image = Image.open(io.BytesIO(image_binary))
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        buf.seek(0)

        return StreamingResponse(buf, media_type="image/jpeg", headers={"X-Fire-Hazard": str(is_fire_hazard)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images/latest/meta")
def get_latest_image_meta():
    try:
        cursor.execute("SELECT id, device_id, filename, timestamp, filepath, sensor_data_id, is_fire_hazard FROM image_data ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No image metadata found")
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
