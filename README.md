# IoT Fire Detection Project

This project implements a comprehensive fire detection system using IoT devices, including environmental sensors and cameras, connected to a central server for monitoring and alerting.

## Project Components

### 1. Hardware Components
- M5Stack device with environmental sensors (Temperature, Humidity, Pressure)
- ESP32-S3 Camera module
- LED indicator (built into ESP32-S3)

### 2. Software Components
- Micropython scripts for sensor and camera devices
- Flask backend server
- Display server for visualization

## Prerequisites

### Hardware Requirements
- M5Stack device
- ESP32-S3 Camera module

## Setup Instructions

### 1. Hardware Setup
1. Connect the M5Stack device to your computer via USB
2. Connect the ESP32-S3 Camera module to your computer via USB
3. Ensure both devices are powered and in programming mode

### 2. Software Setup

#### M5Stack Sensor Setup
1. Flash Micropython firmware to the M5Stack device
2. Copy the `sensor.py` script to the M5Stack device
3. Update the following variables in `sensor.py`:
   - `DEVICE_ID`: Unique identifier for your sensor
   - `SSID`: Your WiFi network name
   - `PASSWORD`: Your WiFi password
   - `API_URL`: Your Flask server's API endpoint

#### ESP32-S3 Camera Setup
1. Flash Micropython firmware to the ESP32-S3 device
2. Copy the `cam.py` script to the ESP32-S3 device
3. Update the following variables in `cam.py`:
   - `DEVICE_ID`: Unique identifier for your camera
   - `SSID`: Your WiFi network name
   - `PASSWORD`: Your WiFi password
   - `API_URL`: Your Flask server's API endpoint

#### Backend Server Setup
1. Navigate to the `fire_hazard_backend` directory
2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure the server settings in the appropriate configuration files
4. Start the server:
   ```bash
   python app.py
   ```


#### Micropython scripts
1. Run cam.py
2. Run sensor.py

Both are in micropython_scripts

#### Display Server Setup
1. Navigate to the `server_2_for_display` directory
2. cd frontend, npm start
3. cd backend, node server.js
4. cd python_backend
5. Start the display server:
   ```bash
   python server.py
   ```



### Accessing the System
1. Sensor data can be viewed on the M5Stack's display
2. Camera interface is accessible via web browser at `http://<device-ip>:80`
3. Backend server dashboard is accessible at `http://<server-ip>:5000`
