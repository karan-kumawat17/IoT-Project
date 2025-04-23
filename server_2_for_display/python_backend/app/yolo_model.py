import os
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image

# Load your model (make sure the path is accessible in your production environment)
model_path = "fire_detection.pt"
Valid_model = YOLO(model_path)

def run_yolo_on_image(pil_img):
    # Convert PIL image to numpy array (OpenCV format)
    img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # Run YOLO prediction
    results = Valid_model.predict(source=img_bgr, imgsz=640, iou=0.4, conf=0.3)

    # Generate the plot with bounding boxes
    plot = results[0].plot()
    plot_rgb = cv2.cvtColor(plot, cv2.COLOR_BGR2RGB)

    # Convert back to PIL for saving or FastAPI use
    pil_result = Image.fromarray(plot_rgb)

    # Determine if "fire" or "smoke" is detected
    fire_detected = any([r for r in results[0].names.values() if r.lower() in ['fire', 'smoke']])
    
    return pil_result, fire_detected
