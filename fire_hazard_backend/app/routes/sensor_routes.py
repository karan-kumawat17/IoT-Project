from flask import Blueprint, request, jsonify
from app import db
from app.models import SensorData
import datetime
import requests

sensor_bp = Blueprint('sensor_bp', __name__)

TEMP_THRESHOLD = 35.0
TEMP_RISE_THRESHOLD = 5.0
TEMP_WINDOW = 60  # seconds

temp_history = {}

@sensor_bp.route('/api/sensor', methods=['POST'])
def recieve_sensor_data():
    try:
        data = request.get_json()

        if not data or "temperature" not in data or "humidity" not in data or "pressure" not in data:
            return jsonify({"error": "Invalid data"}), 400
        
        device_id = data.get("device_id", "unknown_device")
        temperature = data["temperature"]

        # Store Data in Neon SQL
        sensor_entry = SensorData(
            device_id = device_id,
            temperature=data["temperature"],
            humidity=data["humidity"],
            pressure=data["pressure"]
        )
        db.session.add(sensor_entry)
        db.session.commit()

        current_time = datetime.datetime.now().timestamp()
        if device_id not in temp_history:
            temp_history[device_id] = []

        temp_history[device_id].append((current_time, temperature))

        temp_history[device_id] = [
            reading for reading in temp_history[device_id]
            if current_time - reading[0] <= TEMP_WINDOW
        ]

        fire_hazard = False
        fire_hazard_reason = None

        if temperature >= TEMP_THRESHOLD:
            fire_hazard = True
            fire_hazard_reason = f"Temperature above threshold: {temperature}C >= {TEMP_THRESHOLD}C"
            

        if len(temp_history[device_id]) >= 2:
            oldest_temp = temp_history[device_id][0][1]
            if temperature - oldest_temp >= TEMP_RISE_THRESHOLD:
                fire_hazard = True
                fire_hazard_reason = f"Rapid temperature rise: {oldest_temp}C -> {temperature}C in {TEMP_WINDOW} seconds"

        response_data = {
            "message": "Data stored successfully!",
            "sensor_data_id": sensor_entry.id
        }

        if fire_hazard:
            response_data["fire_hazard"] = True
            response_data["fire_hazard_reason"] = fire_hazard_reason

            try:
                camera_response = requests.get("http://192.168.151.112:5000/api/devices/camera")
                if camera_response.status_code == 200:
                    camera_info = camera_response.json()
                    camera_ip = camera_info.get("ip_address")

                    if camera_ip:
                        try:
                            fire_response = requests.get(f"http://{camera_ip}/firehazard", timeout=5)
                            if fire_response.status_code == 200:
                                response_data["camera_response"] = fire_response.text
                                response_data["camera_triggered"] = "direct"
                            else:
                                trigger_response = requests.post(
                                    "http://192.168.151.112:5000/api/trigger_camera",
                                    json={
                                        "device_id": device_id,
                                        "reason": "fire_hazard",
                                        "camera_device_id": camera_info.get("device_id")
                                    },
                                    headers={"Content-Type": "application/json"},
                                    timeout=5
                                )
                                response_data["camera_triggered"] = "server"
                                response_data["camera_response"] = trigger_response.text
                        except:
                            trigger_response = requests.post(
                                    "http://192.168.151.112:5000/api/trigger_camera",
                                    json={
                                        "device_id": device_id,
                                        "reason": "fire_hazard",
                                        "camera_device_id": camera_info.get("device_id")
                                    },
                                    headers={"Content-Type": "application/json"},
                                    timeout=5
                                )
                            response_data["camera_triggered"] = "server_fallback"
                            response_data["camera_response"] = trigger_response.text
                    else:
                        trigger_response = requests.post(
                                    "http://192.168.151.112:5000/api/trigger_camera",
                                    json={
                                        "device_id": device_id,
                                        "reason": "fire_hazard",
                                        "camera_device_id": camera_info.get("device_id")
                                    },
                                    headers={"Content-Type": "application/json"},
                                    timeout=5
                                )
                        response_data["camera_triggered"] = "server_only"
                        response_data["camera_response"] = trigger_response.text
            except Exception as e:
                response_data["camera_triggered_error"] = str(e)

        return jsonify(response_data), 201
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
    

@sensor_bp.route('/api/thresholds', methods=['GET'])
def get_thresholds():
    return jsonify({
        "temp_threshold": TEMP_THRESHOLD,
        "temp_rise_threshold": TEMP_RISE_THRESHOLD,
        "temp_window": TEMP_WINDOW
    })


@sensor_bp.route('/api/thresholds', methods=['POST'])
def update_thresholds():
    global TEMP_THRESHOLD, TEMP_RISE_THRESHOLD, TEMP_WINDOW

    if not request.is_json:
        return jsonify({"error": "Invalid data format"}), 400
    
    data = request.get_json()

    if 'temp_threshold' in data:
        TEMP_THRESHOLD = float(data['temp_threshold'])

    if 'temp_rise_threshold' in data:
        TEMP_RISE_THRESHOLD = float(data['temp_rise_threshold'])

    if 'temp_window' in data:
        TEMP_WINDOW = float(data['temp_window'])

    return jsonify({
        "message": "Thresholds updated successfully",
        "temp_threshold": TEMP_THRESHOLD,
        "temp_rise_threshold": TEMP_RISE_THRESHOLD,
        "temp_window": TEMP_WINDOW
    })