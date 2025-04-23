import binascii
from io import BytesIO
from PIL import Image

def decode_image_from_hex(image_hex):
    if image_hex.startswith('\\x'):
        image_hex = image_hex[2:]
    image_hex = image_hex.replace('\\x', '')
    image_bytes = binascii.unhexlify(image_hex)

    with BytesIO(image_bytes) as stream:
        img = Image.open(stream).convert("RGB")
        return img
