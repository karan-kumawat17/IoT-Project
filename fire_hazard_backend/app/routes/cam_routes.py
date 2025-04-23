from flask import Flask, Blueprint, request, jsonify, send_file, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import datetime
import uuid
from app import db
from app.models import ImageData, SensorData
import base64
import io


cam_bp = Blueprint('cam_bp', __name__)

UPLOAD_FOLDER = 'static/uploads'

camera_registery = {}

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
    is_fire_hazard = data.get('is_fire_hazard', False)  # Optional field

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
        prefix = "fire_hazard_" if is_fire_hazard else "normal_"
        filename = f"{prefix}{device_id}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(device_dir, filename)

        image_bytes = base64.b64decode(image_data)
        with open(filepath, 'wb') as image_file:
            image_file.write(image_bytes)

        
        new_image = ImageData(
            device_id=device_id,
            filename=filename,
            filepath=filepath,
            image_binary=image_bytes,
            sensor_data_id=sensor_data_id,
            is_fire_hazard=is_fire_hazard
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
        is_fire_hazard = request.args.get('is_fire_hazard', type=bool)
        limit = request.args.get('limit', default=10, type=int)
        
        # Build query
        query = ImageData.query
        
        # Apply filters
        if device_id:
            query = query.filter_by(device_id=device_id)
        
        if sensor_data_id:
            query = query.filter_by(sensor_data_id=sensor_data_id)

        if is_fire_hazard is not None:
            query = query.filter_by(is_fire_hazard=is_fire_hazard)
        
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
                "filepath": image.filepath,
                "is_fire_hazard": getattr(image, 'is_fire_hazard', False)
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@cam_bp.route('/api/register_camera', methods=['POST'])
def register_camera():
    if not request.is_json:
        return jsonify({"error": "Invalid data format"}), 400
    
    data = request.get_json()
    device_id = data.get('device_id')
    ip_address = data.get('ip_address')

    if not device_id or not ip_address:
        return jsonify({"error": "Device ID and IP address are required"}), 400
    
    camera_registery[device_id] = {
        "ip_address": ip_address,
        "last_seen": datetime.datetime.now().isoformat()
    }

    return jsonify({"message": "Camera registered successfully!", "device_id": device_id, "ip_address": ip_address}), 201


@cam_bp.route('/api/devices/camera', methods=['GET'])
def get_camera_info():
    device_id = request.args.get('device_id', 'camera_device_1')
    
    if device_id in camera_registery:
        return jsonify(camera_registery[device_id]), 200
    else:
        return jsonify({"error": "Device not found"}), 404
    

@cam_bp.route('/api/trigger_camera', methods=['POST'])
def trigger_camera():
    if not request.is_json:
        return jsonify({"error": "Invalid data format"}), 400
    
    data = request.get_json()
    sensor_device_id = data.get('device_id')
    reason = data.get('reason')
    cam_device_id = data.get('camera_device_id', 'camera_device_1')
    
    if cam_device_id not in camera_registery:
        return jsonify({"error": "Camera device not found"}), 404
    
    camera_ip = camera_registery[cam_device_id]['ip_address']

    try:
        import requests

        if reason == 'fire_hazard':
            response = requests.post(f'http://{camera_ip}/firehazard')
        else:
            response = requests.post(f'http://{camera_ip}/capture')
        
        if response.status_code == 200:
            return jsonify({"message": "Camera triggered successfully!", "camera_response": response.text}), 200
        else:
            return jsonify({
                "error": "Failed to trigger camera",
                "status_code": response.status_code,
                "response": response.text
            }), 500
    except Exception as e:
        return jsonify({"error": f"Failed to trigger camera: {str(e)}"}), 500
    
@cam_bp.route('/api/test_registry', methods=['GET'])
def test_registry():
    print("Camera Registry:", camera_registery)
    return jsonify(camera_registery), 200

@cam_bp.route('/api/cam/<int:image_id>', methods=['GET'])
def get_image(image_id):
    try:
        image = ImageData.query.get(image_id)
        if not image:
            return jsonify({"error": "Image not found"}), 404
        
        if image.image_binary:
            return send_file(
                io.BytesIO(image.image_binary),
                mimetype='image/jpeg',
                as_attachment=False,
                download_name=image.filename
            )
        elif image.filepath and os.path.exists(image.filepath):
            return send_file(image.filepath, mimetype='image/jpeg', as_attachment=False, download_name=image.filename)
        else:
            return jsonify({"error": "Image file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500