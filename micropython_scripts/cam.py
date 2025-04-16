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

# API endpoint for sending captured images
API_URL = "http://192.168.231.112:5000/api/cam"

# Web server configuration for receiving requests
SERVER_PORT = 80

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

def setup_camera():
    print("Setting up camera...")
    try:
        camera.init()
        print("Camera initialized successfully")
        return True
    except Exception as e:
        print(f"Camera initialization failed: {str(e)}")
        return False

def capture_image():
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
        
        # Generate filename with timestamp
        timestamp = "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(*time.localtime()[:6])
        filename = f"/images/{DEVICE_ID}_img_{timestamp}.jpg"
        
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

def send_image(image_path, image_buf):
    """Send the captured image to the server without sensor data association"""
    if not image_path or not image_buf:
        print("No image to send")
        return False
    
    try:
        # Convert image to base64
        b64_image = ubinascii.b2a_base64(image_buf).decode('utf-8').strip()
        
        # Prepare payload - simplified to avoid database issues
        payload = {
            "device_id": DEVICE_ID,
            "image": b64_image
            # Not including sensor_data_id to simplify and troubleshoot the issue
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
    if "GET /capture" in request:
        print("Capture request received")
        
        # Capture image without attempting to get sensor data first
        image_path, image_buf = capture_image()
        
        if image_path:
            print(f"Successfully captured image: {image_path}")
            
            # Send image to server without sensor data association for now
            success = send_image(image_path, image_buf)
            
            if success:
                return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Image captured and sent successfully!</h1></body></html>"
            else:
                return "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Failed to send image</h1></body></html>"
        else:
            return "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Failed to capture image</h1></body></html>"
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