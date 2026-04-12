"""
Utility helper functions.
"""

import os
import tempfile
import httpx
from PIL import Image
import numpy as np
from io import BytesIO
from app.utils.logger import logger


async def download_media(url: str, auth: tuple = None) -> bytes:
    """Download media from a URL (e.g., Twilio media URL)."""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            if auth:
                response = await client.get(url, auth=auth, timeout=30.0)
            else:
                response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.content
    except Exception as e:
        logger.error(f"Failed to download media from {url}: {e}")
        raise


async def download_media_to_file(url: str, suffix: str = ".ogg", auth: tuple = None) -> str:
    """Download media to a temporary file and return the file path."""
    content = await download_media(url, auth)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(content)
    tmp.close()
    return tmp.name


def preprocess_image_bytes(image_bytes: bytes, target_size: tuple = (224, 224)) -> np.ndarray:
    """Preprocess image bytes for MobileNetV2 prediction."""
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image = image.resize(target_size)
    img_array = np.array(image) / 255.0  # Normalize to [0, 1]
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    return img_array


def check_image_quality(image_bytes: bytes) -> dict:
    """Check image quality (resolution, blur detection)."""
    try:
        image = Image.open(BytesIO(image_bytes))
        width, height = image.size
        is_acceptable = width >= 100 and height >= 100
        return {
            "width": width,
            "height": height,
            "acceptable": is_acceptable,
            "reason": "" if is_acceptable else "Image resolution too low. Please send a clearer photo.",
        }
    except Exception as e:
        return {
            "width": 0,
            "height": 0,
            "acceptable": False,
            "reason": f"Could not read image: {str(e)}",
        }


def extract_crop_name(disease_class: str) -> str:
    """Extract crop name from PlantVillage class label."""
    # e.g., "Tomato___Early_blight" -> "Tomato"
    crop = disease_class.split("___")[0]
    crop = crop.replace("_", " ").replace(",", ",")
    return crop.strip()


def format_disease_name(disease_class: str) -> str:
    """Format PlantVillage class label into human-readable disease name."""
    # e.g., "Tomato___Early_blight" -> "Early Blight"
    parts = disease_class.split("___")
    if len(parts) == 2:
        disease = parts[1].replace("_", " ").title()
        return disease
    return disease_class.replace("_", " ").title()


def is_healthy(disease_class: str) -> bool:
    """Check if the predicted class indicates a healthy plant."""
    return "healthy" in disease_class.lower()


def cleanup_temp_file(filepath: str):
    """Remove a temporary file safely."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        logger.warning(f"Failed to clean up temp file {filepath}: {e}")
