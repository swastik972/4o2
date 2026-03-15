"""
Inference service — load trained models and run predictions.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import torch
from loguru import logger
from PIL import Image
from torchvision import models, transforms

from app.core.config import settings
from app.services.data_preprocessing import IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD
from app.services.model_versioning import ModelVersioning


# ── Inference Transform ─────────────────────────────────────────
def get_inference_transform() -> transforms.Compose:
    """Transform for inference — must match training validation transforms."""
    return transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


class InferenceService:
    """
    Load a trained model and run predictions on images.

    Caches the loaded model to avoid reloading on every request.
    """

    CLASS_NAMES = ["normal", "pothole"]

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir or str(settings.model_path)
        self.versioning = ModelVersioning(self.model_dir)
        self.transform = get_inference_transform()

        # Cached model state
        self._model: Optional[torch.nn.Module] = None
        self._loaded_version: Optional[int] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    # ── Model Loading ───────────────────────────────────────────
    def _build_model(self) -> torch.nn.Module:
        """Build a ResNet18 model with 2-class output (matching training)."""
        model = models.resnet18(weights=None)
        # Must match the architecture used in training_pipeline.py
        model.fc = torch.nn.Sequential(
            torch.nn.Dropout(0.3),
            torch.nn.Linear(model.fc.in_features, 2),
        )
        return model

    def load_model(self, version: Optional[int] = None) -> None:
        """
        Load a specific model version, or the latest.

        Skips loading if the requested version is already cached.
        """
        if version is None:
            version = self.versioning.get_latest_version()
            if version is None:
                raise FileNotFoundError("No trained models found. Run training first.")

        # Skip if already loaded
        if self._model is not None and self._loaded_version == version:
            return

        checkpoint = self.versioning.load_model_weights(version)
        model = self._build_model()
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(self.device)
        model.eval()

        self._model = model
        self._loaded_version = version
        logger.info("Inference model loaded — v{} on {}", version, self.device)

    # ── Prediction ──────────────────────────────────────────────
    def predict(
        self,
        image_path: str,
        version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run inference on a single image.

        Args:
            image_path: Path to the image file.
            version: Model version to use (None = latest).

        Returns:
            Dict with label, confidence, class_name, and version.
        """
        self.load_model(version)

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Load and preprocess
        image = Image.open(str(path)).convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        # Inference
        with torch.no_grad():
            outputs = self._model(tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)

        label = predicted.item()
        conf = round(confidence.item(), 4)
        class_name = self.CLASS_NAMES[label]

        logger.info(
            "Prediction: {} (confidence={:.4f}) for {}",
            class_name, conf, path.name,
        )

        return {
            "label": label,
            "class_name": class_name,
            "confidence": conf,
            "probabilities": {
                name: round(p, 4)
                for name, p in zip(self.CLASS_NAMES, probabilities[0].cpu().tolist())
            },
            "model_version": self._loaded_version,
            "image_path": str(path),
        }

    def predict_from_bytes(
        self,
        image_bytes: bytes,
        version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run inference from raw image bytes (e.g., from file upload).

        Returns:
            Dict with label, confidence, class_name, and version.
        """
        import io

        self.load_model(version)

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self._model(tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)

        label = predicted.item()
        conf = round(confidence.item(), 4)
        class_name = self.CLASS_NAMES[label]

        return {
            "label": label,
            "class_name": class_name,
            "confidence": conf,
            "probabilities": {
                name: round(p, 4)
                for name, p in zip(self.CLASS_NAMES, probabilities[0].cpu().tolist())
            },
            "model_version": self._loaded_version,
        }

    # ── Status ──────────────────────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        """Return current inference service status."""
        return {
            "model_loaded": self._model is not None,
            "loaded_version": self._loaded_version,
            "device": self.device,
            "available_versions": [
                v["version"] for v in self.versioning.list_versions()
            ],
        }
