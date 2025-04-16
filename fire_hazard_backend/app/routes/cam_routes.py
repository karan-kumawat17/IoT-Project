from flask import Flask, Blueprint, request, jsonify, send_file, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import datetime
import uuid
from app import db
from app.models import ImageData, SensorData
import base64


cam_bp = Blueprint('cam_bp', __name__)

UPLOAD_FOLDER = 'static/uploads'

def ensure_upload_folder_exists():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)


@cam_bp.route('/api/cam', methods=['POST'])
def receive_cam_data():
    if not request.is_json:
        return jsonify({"error": "Invalid data format"}), 400
    
    data = request.get_json()

    sensor_data_id = data.get('sensor_data_id')
    device_id = data.get('device_id', 'unknown_device')  # Get device ID or use default
    image_data = data.get('image')  # Base64 encoded image

    if not image_data:
        return jsonify({"error": "No image data provided"}), 400
    
    try:
        if sensor_data_id:
            sensor_data = SensorData.query.get(sensor_data_id)
            if not sensor_data:
                return jsonify({"error": "Sensor data not found"}), 404
            

        ensure_upload_folder_exists()

        device_dir = os.path.join(UPLOAD_FOLDER, device_id)
        if not os.path.exists(device_dir):
            os.makedirs(device_dir)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{device_id}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(device_dir, filename)

        image_bytes = base64.b64decode(image_data)
        with open(filepath, 'wb') as image_file:
            image_file.write(image_bytes)

        
        new_image = ImageData(
            device_id=device_id,
            filename=filename,
            filepath=filepath,
            sensor_data_id=sensor_data_id
        )

        db.session.add(new_image)
        db.session.commit()

        return jsonify({"message": "Image stored successfully!", "image_id": new_image.id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error storing image: {e}")
        return jsonify({"error": str(e)}), 500
    

@cam_bp.route('/api/cam', methods=['GET'])
def get_images():
    try:
        # Get query parameters
        device_id = request.args.get('device_id')
        sensor_data_id = request.args.get('sensor_data_id')
        limit = request.args.get('limit', default=10, type=int)
        
        # Build query
        query = ImageData.query
        
        # Apply filters
        if device_id:
            query = query.filter_by(device_id=device_id)
        
        if sensor_data_id:
            query = query.filter_by(sensor_data_id=sensor_data_id)
        
        # Execute query
        images = query.order_by(ImageData.timestamp.desc()).limit(limit).all()
        
        # Format response
        result = []
        for image in images:
            result.append({
                "id": image.id,
                "device_id": image.device_id,
                "sensor_data_id": image.sensor_data_id,
                "timestamp": image.timestamp.isoformat(),
                "filename": image.filename,
                "filepath": image.filepath
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500