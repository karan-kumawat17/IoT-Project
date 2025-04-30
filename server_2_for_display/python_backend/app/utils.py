import binascii
from io import BytesIO
from PIL import Image

def decode_image_from_hex(image_hex):
    # Convert memoryview to bytes if needed
    if isinstance(image_hex, memoryview):
        image_hex = image_hex.tobytes()
    
    # Convert bytes to string if needed
    if isinstance(image_hex, bytes):
        try:
            # Try to directly convert to image first
            with BytesIO(image_hex) as stream:
                img = Image.open(stream).convert("RGB")
                return img
        except Exception:
            # If that fails, try to decode it as a hex string
            image_hex = image_hex.decode('utf-8', errors='ignore')
    
    # Handle string hex representation
    if isinstance(image_hex, str):
        if image_hex.startswith('\\x'):
            image_hex = image_hex[2:]
        image_hex = image_hex.replace('\\x', '')
        
        try:
            image_bytes = binascii.unhexlify(image_hex)
            with BytesIO(image_bytes) as stream:
                img = Image.open(stream).convert("RGB")
                return img
        except binascii.Error:
            raise ValueError("Invalid hex data provided")
    
    raise TypeError("Unsupported data type for image decoding")