"""
Standalone prediction utility for the trained CNN model.
Used for testing and API direct calls.

Usage:
    python -m app.ml.predict --image path/to/leaf.jpg
"""

import argparse
import os
import sys
import numpy as np
from PIL import Image


def predict_image(image_path: str, model_path: str = "models/plant_disease_model.h5"):
    """
    Predict disease from a local image file.
    """
    import tensorflow as tf

    # Load model
    print(f"🧠 Loading model from: {model_path}")
    model = tf.keras.models.load_model(model_path)

    # Class labels (38 PlantVillage classes)
    class_labels = [
        "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust",
        "Apple___healthy", "Blueberry___healthy",
        "Cherry_(including_sour)___Powdery_mildew", "Cherry_(including_sour)___healthy",
        "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
        "Corn_(maize)___Common_rust_", "Corn_(maize)___Northern_Leaf_Blight",
        "Corn_(maize)___healthy", "Grape___Black_rot",
        "Grape___Esca_(Black_Measles)",
        "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Grape___healthy",
        "Orange___Haunglongbing_(Citrus_greening)", "Peach___Bacterial_spot",
        "Peach___healthy", "Pepper,_bell___Bacterial_spot",
        "Pepper,_bell___healthy", "Potato___Early_blight",
        "Potato___Late_blight", "Potato___healthy", "Raspberry___healthy",
        "Soybean___healthy", "Squash___Powdery_mildew",
        "Strawberry___Leaf_scorch", "Strawberry___healthy",
        "Tomato___Bacterial_spot", "Tomato___Early_blight",
        "Tomato___Late_blight", "Tomato___Leaf_Mold",
        "Tomato___Septoria_leaf_spot",
        "Tomato___Spider_mites Two-spotted_spider_mite",
        "Tomato___Target_Spot", "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
        "Tomato___Tomato_mosaic_virus", "Tomato___healthy",
    ]

    # Preprocess image
    print(f"📸 Processing image: {image_path}")
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    # Predict
    predictions = model.predict(img_array, verbose=0)
    top_idx = np.argsort(predictions[0])[-5:][::-1]

    print("\n" + "=" * 50)
    print("🔬 Prediction Results")
    print("=" * 50)

    for i, idx in enumerate(top_idx):
        label = class_labels[idx]
        confidence = predictions[0][idx]
        crop = label.split("___")[0].replace("_", " ")
        disease = label.split("___")[1].replace("_", " ").title() if "___" in label else "Unknown"
        marker = "  ←  TOP PREDICTION" if i == 0 else ""
        print(f"  {i+1}. {crop} — {disease}: {confidence:.4f} ({confidence:.1%}){marker}")

    return {
        "top_class": class_labels[top_idx[0]],
        "confidence": float(predictions[0][top_idx[0]]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict plant disease from image")
    parser.add_argument("--image", type=str, required=True, help="Path to leaf image")
    parser.add_argument("--model", type=str, default="models/plant_disease_model.h5")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"❌ Image not found: {args.image}")
        sys.exit(1)

    predict_image(args.image, args.model)
