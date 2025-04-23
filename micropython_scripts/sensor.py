import os, sys, io
import M5
from M5 import *
from hardware import I2C
from hardware import Pin
from unit import ENVUnit
import time
import urequests
import network

# Initialize Sensor:
i2c0 = None
env3_0 = None

# Global variables for UI elements:
tempLabel = None
pressureLabel = None
humidityLabel = None

# Device ID (unique for each device)
DEVICE_ID = "sensor_device_1"  # Change for second device

# WiFi:
SSID = "Karan"
PASSWORD = "qwer1234"

# API URL (corrected to be the same as camera)
API_URL = "http://192.168.151.112:5000/api/sensor"

# Camera device URL - updated for correct IP address
# For direct camera triggering, we need the camera device's IP (not the API server)
# This should be updated with the actual camera device IP once it's connected to WiFi
CAMERA_IP = None  # This will be updated from the API server

# Fire hazard detection thresholds
TEMP_THRESHOLD = 35.0  # °C - adjust based on your environment
TEMP_RISE_THRESHOLD = 5.0  # °C sudden rise within time window
TEMP_WINDOW = 60  # seconds to detect rise

# Variables for monitoring temperature changes
temp_history = []
last_camera_trigger_time = 0
CAMERA_COOLDOWN = 60  # seconds between camera triggers

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("Connected to WiFi! IP:", wlan.ifconfig()[0])

def setup():
    global i2c0, env3_0
    M5.begin()
    Widgets.fillScreen(0x222222)

    connect_wifi()

    i2c0 = I2C(0, scl=Pin(33), sda=Pin(32), freq=100000)
    env3_0 = ENVUnit(i2c=i2c0, type=3)
    
    # Try to get camera IP from the server
    get_camera_ip()

def get_camera_ip():
    """Get camera device IP from the API server"""
    global CAMERA_IP
    try:
        response = urequests.get("http://192.168.151.112:5000/api/devices/camera")
        if response.status_code == 200:
            data = response.json()
            CAMERA_IP = data.get("ip_address")
            print(f"Retrieved camera IP: {CAMERA_IP}")
        response.close()
    except Exception as e:
        print("Failed to get camera IP:", str(e))

def send_data(temperature, humidity, pressure):
    data = {
        "device_id": DEVICE_ID,  # Include device ID
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure
    }

    try:
        response = urequests.post(API_URL, json=data, headers={"Content-Type": "application/json"})
        print("Server Response:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data:", str(e))

def trigger_camera_via_server():
    """Trigger camera through the API server"""
    try:
        print("FIRE HAZARD DETECTED! Triggering camera through server...")
        response = urequests.post(
            "http://192.168.151.112:5000/api/trigger_camera",
            json={"device_id": DEVICE_ID, "reason": "fire_hazard"},
            headers={"Content-Type": "application/json"}
        )
        print("Server Response:", response.text)
        response.close()
        return True
    except Exception as e:
        print("Failed to trigger camera via server:", str(e))
        return False

def trigger_camera_direct():
    """Send request directly to camera device to capture an image"""
    global CAMERA_IP
    
    if not CAMERA_IP:
        print("Camera IP not available, trying to get it...")
        get_camera_ip()
        
    if not CAMERA_IP:
        print("Still no camera IP available, using server method instead")
        return trigger_camera_via_server()
    
    try:
        print(f"FIRE HAZARD DETECTED! Triggering camera directly at {CAMERA_IP}...")
        response = urequests.get(f"http://{CAMERA_IP}/firehazard")
        print("Camera Response:", response.text)
        response.close()
        return True
    except Exception as e:
        print("Failed to trigger camera directly:", str(e))
        print("Trying server method instead...")
        return trigger_camera_via_server()

def check_fire_hazard(temp):
    """Check if current temperature indicates a fire hazard"""
    global temp_history, last_camera_trigger_time
    
    current_time = time.time()
    
    # Store temperature with timestamp
    temp_history.append((current_time, temp))
    
    # Remove old temperature readings outside our window
    temp_history = [t for t in temp_history if current_time - t[0] <= TEMP_WINDOW]
    
    # Check absolute temperature threshold
    if temp >= TEMP_THRESHOLD:
        if current_time - last_camera_trigger_time > CAMERA_COOLDOWN:
            print(f"Temperature above threshold: {temp}°C >= {TEMP_THRESHOLD}°C")
            if trigger_camera_direct():
                last_camera_trigger_time = current_time
            return True
    
    # Check for rapid temperature rise if we have enough history
    if len(temp_history) >= 2:
        oldest_temp = temp_history[0][1]
        if temp - oldest_temp >= TEMP_RISE_THRESHOLD:
            if current_time - last_camera_trigger_time > CAMERA_COOLDOWN:
                print(f"Rapid temperature rise detected: {oldest_temp}°C -> {temp}°C in {TEMP_WINDOW} seconds")
                if trigger_camera_direct():
                    last_camera_trigger_time = current_time
                return True
    
    return False

def loop():
    global i2c0, env3_0, tempLabel, pressureLabel, humidityLabel
    
    while True:
        try:
            temp = env3_0.read_temperature()
            humidity = env3_0.read_humidity()
            pressure = env3_0.read_pressure()
  
            print(f"[{DEVICE_ID}] Temperature: {temp}°C, Humidity: {humidity}%, Pressure: {pressure} hPa")

            # Check for fire hazard
            hazard_detected = check_fire_hazard(temp)
            
            # Update M5Stack screen
            Widgets.fillScreen(0x222222)  # Clear screen
            
            device_info = f"Device: {DEVICE_ID}"
            temp_hehe = f"Temperature: {temp} C"
            humid_hehe = f"Humidity: {humidity}%"
            pressure_hehe = f"Pressure: {pressure} hPa"
            
            deviceLabel = Widgets.Label(device_info, 10, 10, 1.0, 0xffffff, 0x222222, Widgets.FONTS.DejaVu18)
            tempLabel = Widgets.Label(temp_hehe, 10, 50, 1.0, 0xffffff, 0x222222, Widgets.FONTS.DejaVu18)
            humidityLabel = Widgets.Label(humid_hehe, 10, 100, 1.0, 0xffffff, 0x222222, Widgets.FONTS.DejaVu18)
            pressureLabel = Widgets.Label(pressure_hehe, 10, 150, 1.0, 0xffffff, 0x222222, Widgets.FONTS.DejaVu18)
            
            # Add hazard indicator if fire hazard is detected
            if hazard_detected:
                hazardLabel = Widgets.Label("FIRE HAZARD ALERT!", 10, 200, 1.0, 0xff0000, 0x222222, Widgets.FONTS.DejaVu18)

            M5.update()

            # Send data to Flask backend
            send_data(temp, humidity, pressure)

            # Wait for 5 seconds before next reading
            time.sleep(5)

        except Exception as e:
            print("Error:", str(e))
          

if __name__ == '__main__':
    try:
        setup()
        loop()
    except (Exception, KeyboardInterrupt) as e:
        try:
            from utility import print_error_msg
            print_error_msg(e)
        except ImportError:
            print("please update to latest firmware")