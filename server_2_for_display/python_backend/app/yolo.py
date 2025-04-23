import cv2
import numpy as np
import os
from io import BytesIO
from PIL import Image
from ultralytics import YOLO

# Load the YOLO model once (ensure the path is correct)
Valid_model = YOLO('fire_detection.pt')

def detect_fire(image_bytes):
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image_array = np.array(image)
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

        # Save temp image to disk for YOLOv8 to read
        temp_path = "temp.jpg"
        cv2.imwrite(temp_path, image_bgr)

        # Run inference
        result_predict = Valid_model.predict(source=temp_path, imgsz=640, iou=0.4, conf=0.25)

        # Convert result to a plot
        annotated = result_predict[0].plot()  # This is an image (numpy array) with drawn boxes

        # Convert to JPEG bytes
        _, buffer = cv2.imencode(".jpg", annotated)
        return buffer.tobytes()
    except Exception as e:
        print(f"[detect_fire] Error: {e}")
        raise
