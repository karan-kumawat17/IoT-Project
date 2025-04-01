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

        # Store Data in Neon SQL
        sensor_entry = SensorData(
            temperature=data["temperature"],
            humidity=data["humidity"],
            pressure=data["pressure"]
        )
        db.session.add(sensor_entry)
        db.session.commit()

        return jsonify({"message": "Data stored successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500