from flask import Blueprint, request, jsonify
from app import db
from app.models import SensorData

sensor_bp = Blueprint('sensor_bp', __name__)

@sensor_bp.route('/api/sensor', methods=['POST'])
def recieve_sensor_data():
    try:
        data = request.get_json()

        if not data or "temperature" not in data or "humidity" not in data or "pressure" not in data:
            return jsonify({"error": "Invalid data"}), 400
        
        device_id = data.get("device_id", "unknown_device")

        # Store Data in Neon SQL
        sensor_entry = SensorData(
            device_id = device_id,
            temperature=data["temperature"],
            humidity=data["humidity"],
            pressure=data["pressure"]
        )
        db.session.add(sensor_entry)
        db.session.commit()

        return jsonify({"message": "Data stored successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@sensor_bp.route('/api/sensor', methods=['GET'])
def get_sensor_data():
    try:
        device_id = request.args.get('device_id')
        limit = request.args.get('limit', default=10, type=int)

        query = SensorData.query

        if device_id:
            query = query.filter(SensorData.device_id == device_id)
        
        sensors = query.order_by(SensorData.date_created.desc()).limit(limit).all()

        result = []
        for sensor in sensors:
            result.append({
                "id": sensor.id,
                "device_id": sensor.device_id,
                "temperature": sensor.temperature,
                "humidity": sensor.humidity,
                "pressure": sensor.pressure,
                "date_created": sensor.date_created.isoformat()
            })

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@sensor_bp.route('/api/sensor/latest', methods=['GET'])
def get_latest_sensor_data():
    try:
        # Get device ID from query parameters
        device_id = request.args.get('device_id')
        
        # Build query
        query = SensorData.query
        
        # Filter by device if provided
        if device_id:
            query = query.filter_by(device_id=device_id)
        
        # Get latest reading
        latest = query.order_by(SensorData.date_created.desc()).first()
        
        if not latest:
            return jsonify({"error": "No sensor data found"}), 404
        
        # Format response
        result = {
            "id": latest.id,
            "device_id": latest.device_id,
            "temperature": latest.temperature,
            "humidity": latest.humidity,
            "pressure": latest.pressure,
            "timestamp": latest.date_created.isoformat()
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500