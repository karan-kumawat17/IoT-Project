from machine import Pin
from time import sleep
import time
import camera
import os

led = Pin(21, Pin.OUT)

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
        filename = f"/images/img_{timestamp}.jpg"
        
        # Save image to file
        with open(filename, 'wb') as f:
            f.write(buf)
        
        print(f"Image saved to {filename}")
        return filename
    except Exception as e:
        print(f"Error capturing image: {str(e)}")
        return None
    finally:
        led.value(0)  # Turn off LED


def main():
    print("XIAO ESP32-S3 Camera Test")
    
    # Setup camera
    if not setup_camera():
        print("Failed to initialize camera. Exiting.")
        return
    
    # Wait for camera to warm up
    time.sleep(2)
    
    try:
        while True:
            # Capture image every 10 seconds
            image_path = capture_image()
            
            if image_path:
                print(f"Successfully captured image: {image_path}")
            else:
                print("Failed to capture image")
            
            # Wait before next capture
            print("Waiting 10 seconds before next capture...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("Program stopped by user")
    finally:
        # Clean up
        camera.deinit()
        print("Camera deinitialized")

if _name_ == "_main_":
    main()