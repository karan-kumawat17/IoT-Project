from flask import Blueprint, Response, jsonify
from app.db import get_conn, return_conn
from app.yolo import detect_fire

bp = Blueprint("routes", __name__)

@bp.route("/latest-image")
def latest_image():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT image_binary FROM image_data ORDER BY timestamp DESC LIMIT 1;")
        result = cur.fetchone()
        if result and result[0]:
            image_bytes = bytes(result[0]) 
            processed = detect_fire(image_bytes)
            return Response(processed, mimetype="image/jpeg")
        else:
            return jsonify({"error": "No image found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        return_conn(conn)

@bp.route("/upload-test-image", methods=["POST"])
def upload_test_image():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        image_bytes = file.read()
        processed = detect_fire(image_bytes)
        return Response(processed, mimetype="image/jpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

