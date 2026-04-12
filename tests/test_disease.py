"""
Tests for the Disease Detector service.
"""

import pytest
import numpy as np
from app.services.disease_detector import DiseaseDetector
from app.utils.helpers import extract_crop_name, format_disease_name, is_healthy


class TestDiseaseDetector:
    """Test CNN disease detection service."""

    def test_simulated_prediction(self):
        """Test simulated prediction when model is not loaded."""
        result = DiseaseDetector._simulated_prediction()

        assert result["disease_class"] == "Tomato___Early_blight"
        assert result["disease_name"] == "Early Blight"
        assert result["crop"] == "Tomato"
        assert result["confidence"] > 0.9
        assert result["is_healthy"] is False
        assert len(result["top_predictions"]) == 3

    def test_extract_crop_name(self):
        """Test crop name extraction from class labels."""
        assert extract_crop_name("Tomato___Early_blight") == "Tomato"
        assert extract_crop_name("Apple___Apple_scab") == "Apple"
        assert extract_crop_name("Corn_(maize)___Common_rust_") == "Corn (maize)"
        assert extract_crop_name("Potato___healthy") == "Potato"

    def test_format_disease_name(self):
        """Test disease name formatting."""
        assert format_disease_name("Tomato___Early_blight") == "Early Blight"
        assert format_disease_name("Apple___Apple_scab") == "Apple Scab"
        assert format_disease_name("Tomato___healthy") == "Healthy"

    def test_is_healthy(self):
        """Test healthy class detection."""
        assert is_healthy("Tomato___healthy") is True
        assert is_healthy("Apple___healthy") is True
        assert is_healthy("Tomato___Early_blight") is False
        assert is_healthy("Grape___Black_rot") is False


class TestResponseFormatter:
    """Test response formatting utilities."""

    def test_format_disease_response_healthy(self):
        """Test formatting for healthy plant response."""
        from app.services.response_formatter import ResponseFormatter

        disease_data = {
            "disease_name": "Healthy",
            "crop": "Tomato",
            "confidence": 0.96,
            "is_healthy": True,
        }
        response = ResponseFormatter.format_disease_response(disease_data, "")
        assert "healthy" in response.lower()
        assert "Tomato" in response

    def test_format_disease_response_diseased(self):
        """Test formatting for diseased plant response."""
        from app.services.response_formatter import ResponseFormatter

        disease_data = {
            "disease_name": "Early Blight",
            "crop": "Tomato",
            "confidence": 0.94,
            "is_healthy": False,
            "top_predictions": [],
        }
        response = ResponseFormatter.format_disease_response(disease_data, "Treatment info here.")
        assert "Early Blight" in response
        assert "94%" in response

    def test_truncate_for_whatsapp(self):
        """Test message truncation for WhatsApp limits."""
        from app.services.response_formatter import ResponseFormatter

        short_msg = "Hello"
        assert ResponseFormatter.truncate_for_whatsapp(short_msg) == short_msg

        long_msg = "A" * 5000
        truncated = ResponseFormatter.truncate_for_whatsapp(long_msg)
        assert len(truncated) < 4200

    def test_format_error_response(self):
        """Test error message generation."""
        from app.services.response_formatter import ResponseFormatter

        en_error = ResponseFormatter.format_error_response("general", "en")
        assert "Sorry" in en_error or "sorry" in en_error.lower()

        hi_error = ResponseFormatter.format_error_response("general", "hi")
        assert "क्षमा" in hi_error
