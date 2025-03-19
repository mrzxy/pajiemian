import hashlib

import imagehash
from PIL import Image

def calculate_image_hash(file):
    with open(file, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()
