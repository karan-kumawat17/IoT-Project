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

# WiFi:
SSID = "Karan"
PASSWORD = "qwer1234"

# Flask API URL
API_URL = "http://192.168.224.112:5000/api/sensor"

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

def send_data(temperature, humidity, pressure):
    data = {
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

def loop():
    global i2c0, env3_0, tempLabel, pressureLabel, humidityLabel
    
    while True:
        try:
            temp = env3_0.read_temperature()
            humidity = env3_0.read_humidity()
            pressure = env3_0.read_pressure()
  
            print(f"Temperature: {temp}°C, Humidity: {humidity}%, Pressure: {pressure} hPa")

            # Update M5Stack screen
            Widgets.fillScreen(0x222222)  # Clear screen

            temp_hehe = f"Temperature: {temp} C"
            humid_hehe = f"Humidity: {humidity}%"
            pressure_hehe = f"Pressure: {pressure} hPa"
            
            tempLabel = Widgets.Label(temp_hehe, 10, 50, 1.0, 0xffffff, 0x222222, Widgets.FONTS.DejaVu18)
            humidityLabel = Widgets.Label(humid_hehe, 10, 100, 1.0, 0xffffff, 0x222222, Widgets.FONTS.DejaVu18)
            pressureLabel = Widgets.Label(pressure_hehe, 10, 150, 1.0, 0xffffff, 0x222222, Widgets.FONTS.DejaVu18)

            # Widgets.print(f"Temp: {temp}°C\nHumidity: {humidity}%\nPressure: {pressure} hPa")

            M5.update()  # <- Add this back if you're displaying data on the screen

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
