"""
CNN Model Training Pipeline for Plant Disease Classification.
Uses MobileNetV2 with Transfer Learning on PlantVillage dataset.

Usage:
    python -m app.ml.train_model --data_dir path/to/PlantVillage --epochs 15

Dataset Structure Expected:
    PlantVillage/
    ├── Apple___Apple_scab/
    │   ├── image001.jpg
    │   ├── image002.jpg
    │   └── ...
    ├── Apple___Black_rot/
    ├── ...
    └── Tomato___healthy/
"""

import os
import argparse
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import (
    Dense,
    GlobalAveragePooling2D,
    Dropout,
    BatchNormalization,
)
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    ReduceLROnPlateau,
    TensorBoard,
)
from tensorflow.keras.preprocessing.image import ImageDataGenerator


# ── Configuration ───────────────────────────────────────

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
NUM_CLASSES = 38
INITIAL_LR = 0.001
FINE_TUNE_LR = 0.0001


def create_model(num_classes: int = NUM_CLASSES) -> Model:
    """
    Create a MobileNetV2-based model for plant disease classification.
    
    Architecture:
    - MobileNetV2 base (pretrained on ImageNet, frozen)
    - Global Average Pooling
    - BatchNorm → Dense(256) → ReLU → Dropout(0.3)
    - BatchNorm → Dense(128) → ReLU → Dropout(0.2)
    - Dense(num_classes) → Softmax
    """
    # Load pretrained MobileNetV2 (exclude top classification layers)
    base_model = MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet",
    )

    # Freeze base model layers for transfer learning
    base_model.trainable = False

    # Build classifier head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(256, activation="relu")(x)
    x = Dropout(0.3)(x)
    x = BatchNormalization()(x)
    x = Dense(128, activation="relu")(x)
    x = Dropout(0.2)(x)
    outputs = Dense(num_classes, activation="softmax")(x)

    model = Model(inputs=base_model.input, outputs=outputs)

    print(f"\n📊 Model Summary:")
    print(f"   Total params: {model.count_params():,}")
    print(f"   Trainable params: {sum(tf.keras.backend.count_params(w) for w in model.trainable_weights):,}")
    print(f"   Non-trainable params: {sum(tf.keras.backend.count_params(w) for w in model.non_trainable_weights):,}")

    return model


def create_data_generators(data_dir: str) -> tuple:
    """
    Create training and validation data generators with augmentation.
    
    Augmentation applied to training data:
    - Rotation (±20°)
    - Width/Height shift (±20%)
    - Shear (±15%)
    - Zoom (±20%)
    - Horizontal flip
    - Brightness adjustment
    """
    # Training data generator WITH augmentation
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.15,
        zoom_range=0.2,
        horizontal_flip=True,
        brightness_range=[0.8, 1.2],
        fill_mode="nearest",
        validation_split=0.2,  # 80/20 split
    )

    # Validation data generator WITHOUT augmentation
    val_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=0.2,
    )

    print(f"\n📁 Loading data from: {data_dir}")

    # Training generator
    train_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
    )

    # Validation generator
    val_generator = val_datagen.flow_from_directory(
        data_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
    )

    print(f"   Training samples: {train_generator.samples}")
    print(f"   Validation samples: {val_generator.samples}")
    print(f"   Classes: {len(train_generator.class_indices)}")
    print(f"   Class labels: {list(train_generator.class_indices.keys())[:5]}...")

    return train_generator, val_generator


def train_model(
    data_dir: str,
    output_dir: str = "models",
    epochs: int = 15,
    fine_tune_epochs: int = 10,
):
    """
    Full training pipeline:
    
    Phase 1: Train classifier head (base frozen) — `epochs` epochs
    Phase 2: Fine-tune top layers of MobileNetV2 — `fine_tune_epochs` epochs
    """
    os.makedirs(output_dir, exist_ok=True)

    # ── Phase 1: Train classifier head ──────────────────
    print("\n" + "=" * 60)
    print("🚀 Phase 1: Training Classifier Head")
    print("=" * 60)

    model = create_model(NUM_CLASSES)
    train_gen, val_gen = create_data_generators(data_dir)

    model.compile(
        optimizer=Adam(learning_rate=INITIAL_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks_phase1 = [
        ModelCheckpoint(
            os.path.join(output_dir, "plant_disease_model_phase1.h5"),
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
            verbose=1,
        ),
        EarlyStopping(
            monitor="val_accuracy",
            patience=5,
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1,
        ),
        TensorBoard(log_dir=os.path.join(output_dir, "logs_phase1")),
    ]

    history1 = model.fit(
        train_gen,
        epochs=epochs,
        validation_data=val_gen,
        callbacks=callbacks_phase1,
        verbose=1,
    )

    phase1_acc = max(history1.history["val_accuracy"])
    print(f"\n✅ Phase 1 Complete — Best Val Accuracy: {phase1_acc:.4f}")

    # ── Phase 2: Fine-tune top layers ───────────────────
    print("\n" + "=" * 60)
    print("🔧 Phase 2: Fine-tuning Top Layers")
    print("=" * 60)

    # Unfreeze top 30 layers of MobileNetV2
    base_model = model.layers[1] if hasattr(model.layers[1], 'layers') else None
    if base_model is None:
        # Find MobileNetV2 base in the model
        for layer in model.layers:
            if isinstance(layer, tf.keras.Model):
                base_model = layer
                break

    if base_model:
        base_model.trainable = True
        # Freeze all layers except last 30
        for layer in base_model.layers[:-30]:
            layer.trainable = False

        print(f"   Unfrozen top 30 layers of MobileNetV2")
    else:
        print("   ⚠️ Could not find base model for fine-tuning")

    model.compile(
        optimizer=Adam(learning_rate=FINE_TUNE_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks_phase2 = [
        ModelCheckpoint(
            os.path.join(output_dir, "plant_disease_model.h5"),
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
            verbose=1,
        ),
        EarlyStopping(
            monitor="val_accuracy",
            patience=5,
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.3,
            patience=2,
            min_lr=1e-7,
            verbose=1,
        ),
        TensorBoard(log_dir=os.path.join(output_dir, "logs_phase2")),
    ]

    history2 = model.fit(
        train_gen,
        epochs=fine_tune_epochs,
        validation_data=val_gen,
        callbacks=callbacks_phase2,
        verbose=1,
    )

    phase2_acc = max(history2.history["val_accuracy"])
    print(f"\n✅ Phase 2 Complete — Best Val Accuracy: {phase2_acc:.4f}")

    # ── Save final model ────────────────────────────────
    final_path = os.path.join(output_dir, "plant_disease_model.h5")
    model.save(final_path)
    print(f"\n💾 Final model saved to: {final_path}")

    # Save class labels
    import json
    labels_path = os.path.join(output_dir, "class_labels.json")
    with open(labels_path, "w") as f:
        json.dump(train_gen.class_indices, f, indent=2)
    print(f"🏷️ Class labels saved to: {labels_path}")

    # ── Evaluation ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 Final Evaluation")
    print("=" * 60)

    val_loss, val_acc = model.evaluate(val_gen, verbose=0)
    print(f"   Validation Loss:     {val_loss:.4f}")
    print(f"   Validation Accuracy: {val_acc:.4f}")

    return model, history1, history2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Plant Disease CNN Model")
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="Path to PlantVillage dataset directory",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="models",
        help="Directory to save trained model",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=15,
        help="Number of training epochs (Phase 1)",
    )
    parser.add_argument(
        "--fine_tune_epochs",
        type=int,
        default=10,
        help="Number of fine-tuning epochs (Phase 2)",
    )

    args = parser.parse_args()

    print("\n🌾 KrishiMitra — Plant Disease CNN Training Pipeline")
    print("=" * 60)

    train_model(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        fine_tune_epochs=args.fine_tune_epochs,
    )
