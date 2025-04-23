import requests
from PIL import Image
import torch
import io
from torchvision.transforms import ToTensor, ToPILImage

# Load YOLO model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='fire_detection.pt', force_reload=True)

def fetch_and_infer(image_url):
    response = requests.get(image_url)
    img = Image.open(io.BytesIO(response.content)).convert("RGB")
    
    results = model(img, size=640)
    results.render()  # draws bounding boxes on the image

    # Convert to PIL Image
    img_with_boxes = Image.fromarray(results.ims[0])
    img_with_boxes.save("static/predicted.jpg")
    
    fire_detected = any(['fire' in result['name'].lower() for result in results.pandas().xyxy[0].to_dict(orient="records")])
    return fire_detected
