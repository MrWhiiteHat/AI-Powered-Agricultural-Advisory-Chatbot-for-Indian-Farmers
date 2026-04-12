"""
Tests for the WhatsApp webhook endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestWebhook:
    """Test WhatsApp webhook routes."""

    def setup_method(self):
        """Set up test client."""
        # Mock database connection before importing app
        with patch("app.database.Database.connect"), \
             patch("app.services.disease_detector.DiseaseDetector.load_model"), \
             patch("app.services.rag_engine.RAGEngine.initialize"):
            from app.main import app
            self.client = TestClient(app)

    def test_webhook_verification(self):
        """Test GET /webhook/whatsapp returns active status."""
        response = self.client.get("/webhook/whatsapp")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "webhook active"
        assert data["app"] == "KrishiMitra"

    def test_root_endpoint(self):
        """Test GET / returns app info."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "KrishiMitra"
        assert data["status"] == "running"

    def test_health_endpoint(self):
        """Test GET /health returns health status."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "db_connected" in data
        assert "model_loaded" in data

    def test_diseases_list(self):
        """Test GET /api/v1/diseases returns disease list."""
        response = self.client.get("/api/v1/diseases")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 38
        assert len(data["diseases"]) == 38

    @patch("app.routes.webhook.process_message")
    def test_webhook_post_text_message(self, mock_process):
        """Test POST /webhook/whatsapp with text message."""
        form_data = {
            "From": "whatsapp:+919876543210",
            "To": "whatsapp:+14155238886",
            "Body": "Hello",
            "NumMedia": "0",
            "MessageSid": "SM123456",
            "ProfileName": "Test Farmer",
        }
        response = self.client.post("/webhook/whatsapp", data=form_data)
        assert response.status_code == 200
        assert "Response" in response.text

    @patch("app.routes.webhook.process_message")
    def test_webhook_post_image_message(self, mock_process):
        """Test POST /webhook/whatsapp with image message."""
        form_data = {
            "From": "whatsapp:+919876543210",
            "To": "whatsapp:+14155238886",
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/media/test.jpg",
            "MediaContentType0": "image/jpeg",
            "MessageSid": "SM123456",
        }
        response = self.client.post("/webhook/whatsapp", data=form_data)
        assert response.status_code == 200
