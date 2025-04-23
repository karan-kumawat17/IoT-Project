from machine import Pin
import time
import camera
import os
import network
import urequests
import json
import ubinascii
import socket

# Device ID 
DEVICE_ID = "camera_device_1"

# LED for visual feedback
led = Pin(21, Pin.OUT)

# WiFi configuration
SSID = "Karan"
PASSWORD = "qwer1234"

# API endpoint for sending captured images (corrected to consistent URL)
API_URL = "http://192.168.151.112:5000/api/cam"

# URL for registering camera IP to the server
REGISTER_URL = "http://192.168.151.112:5000/api/register_camera"

# Web server configuration for receiving requests
SERVER_PORT = 80

# Flag to indicate if the capture was triggered by fire hazard
fire_hazard_triggered = False

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        max_wait = 20
        while max_wait > 0 and not wlan.isconnected():
            max_wait -= 1
            print("Waiting for connection...")
            time.sleep(1)
            
    if wlan.isconnected():
        print("Connected to WiFi! IP:", wlan.ifconfig()[0])
        return True, wlan.ifconfig()[0]
    else:
        print("Failed to connect to WiFi")
        return False, None

def register_camera_ip(ip):
    """Register camera IP with the server"""
    try:
        data = {
            "device_id": DEVICE_ID,
            "ip_address": ip
        }
        response = urequests.post(REGISTER_URL, json=data, headers={"Content-Type": "application/json"})
        print(f"Registered camera IP with server: {response.text}")
        response.close()
        return True
    except Exception as e:
        print(f"Failed to register camera IP: {str(e)}")
        return False

def setup_camera():
    print("Setting up camera...")
    try:
        camera.init()
        print("Camera initialized successfully")
        return True
    except Exception as e:
        print(f"Camera initialization failed: {str(e)}")
        return False

def capture_image(is_fire_hazard=False):
    """Capture an image and indicate if it was triggered by fire hazard"""
    print("Capturing image...")
    led.value(1)  # Turn on LED to indicate capturing
    
    try:
        # Capture image
        buf = camera.capture()
        
        # Create directory if it doesn't exist
        try:
            os.mkdir('/images')
        except:
            pass  # Directory already exists
        
        # Generate filename with timestamp and fire hazard indicator if applicable
        timestamp = "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(*time.localtime()[:6])
        
        prefix = "FIRE_HAZARD_" if is_fire_hazard else ""
        filename = f"/images/{prefix}{DEVICE_ID}_img_{timestamp}.jpg"
        
        # Save image to file
        with open(filename, 'wb') as f:
            f.write(buf)
            
        print(f"Image saved to {filename}")
        return filename, buf
    except Exception as e:
        print(f"Error capturing image: {str(e)}")
        return None, None
    finally:
        led.value(0)  # Turn off LED

def send_image(image_path, image_buf, is_fire_hazard=False):
    """Send the captured image to the server with fire hazard flag if applicable"""
    if not image_path or not image_buf:
        print("No image to send")
        return False
    
    try:
        # Convert image to base64
        b64_image = ubinascii.b2a_base64(image_buf).decode('utf-8').strip()
        
        # Prepare payload with fire hazard indicator
        payload = {
            "device_id": DEVICE_ID,
            "image": b64_image,
            "is_fire_hazard": is_fire_hazard
        }
        
        # Send to server
        print(f"Sending image to {API_URL}...")
        response = urequests.post(API_URL, 
                                 json=payload,
                                 headers={'Content-Type': 'application/json'})
        
        if response.status_code == 201:
            print("Image sent successfully!")
            result = response.json()
            print(f"Server assigned ID: {result.get('image_id')}")
            response.close()
            return True
        else:
            print(f"Failed to send image. Status: {response.status_code}")
            print(f"Response: {response.text}")
            response.close()
            return False
            
    except Exception as e:
        print(f"Error sending image: {str(e)}")
        return False

def process_request(request):
    """Process incoming HTTP request"""
    global fire_hazard_triggered
    
    if "GET /capture" in request:
        print("Capture request received")
        
        # Check if this was triggered by fire hazard detection
        is_fire_hazard = "firehazard=true" in request
        if is_fire_hazard:
            print("FIRE HAZARD ALERT! Capture triggered by sensor")
            
        # Capture image
        image_path, image_buf = capture_image(is_fire_hazard)
        
        if image_path:
            print(f"Successfully captured image: {image_path}")
            
            # Send image to server with fire hazard flag if applicable
            success = send_image(image_path, image_buf, is_fire_hazard)
            
            if success:
                return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Image captured and sent successfully!</h1></body></html>"
            else:
                return "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Failed to send image</h1></body></html>"
        else:
            return "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Failed to capture image</h1></body></html>"
    elif "GET /firehazard" in request:
        print("FIRE HAZARD ALERT! Capture triggered by sensor")
        
        # Set flag to indicate fire hazard triggered this capture
        image_path, image_buf = capture_image(True)
        
        if image_path:
            print(f"Successfully captured image: {image_path}")
            
            # Send image to server with fire hazard flag
            success = send_image(image_path, image_buf, True)
            
            if success:
                return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Fire hazard image captured and sent successfully!</h1></body></html>"
            else:
                return "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Failed to send fire hazard image</h1></body></html>"
        else:
            return "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Failed to capture fire hazard image</h1></body></html>"
    elif "GET /status" in request:
        return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Camera is online</h1><p>Device ID: " + DEVICE_ID + "</p></body></html>"
    else:
        # Default homepage
        return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body><h1>ESP32-S3 Camera</h1><p>Device ID: " + DEVICE_ID + "</p><p><a href='/capture'>Take Picture</a></p><p><a href='/status'>Check Status</a></p></body></html>"

def start_server(ip):
    """Start a web server to listen for capture requests"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', SERVER_PORT))
    s.listen(5)
    print(f"Server listening on http://{ip}:{SERVER_PORT}")
    print(f"To take a picture, visit http://{ip}:{SERVER_PORT}/capture")
    print(f"For fire hazard capture, visit http://{ip}:{SERVER_PORT}/firehazard")
    print(f"To check status, visit http://{ip}:{SERVER_PORT}/status")
    print(f"For homepage, visit http://{ip}:{SERVER_PORT}/")
    
    while True:
        try:
            conn, addr = s.accept()
            print(f"Connection from {addr}")
            
            request = conn.recv(1024).decode()
            print(f"Request: {request}")
            
            response = process_request(request)
            conn.send(response.encode())
            
            conn.close()
        except Exception as e:
            print(f"Server error: {str(e)}")
            continue

def main():
    print(f"XIAO ESP32-S3 Camera - Device ID: {DEVICE_ID}")
    
    # Connect to WiFi
    wifi_connected, ip = connect_wifi()
    if not wifi_connected:
        print("WiFi connection failed. Exiting.")
        return
    
    # Register camera IP with the server
    register_camera_ip(ip)
    
    # Setup camera
    if not setup_camera():
        print("Failed to initialize camera. Exiting.")
        return
    
    # Wait for camera to warm up
    time.sleep(2)
    
    # Start server to listen for requests
    try:
        start_server(ip)
    except KeyboardInterrupt:
        print("Program stopped by user")
    finally:
        # Clean up
        camera.deinit()
        print("Camera deinitialized")

if __name__ == "__main__":
    main()
