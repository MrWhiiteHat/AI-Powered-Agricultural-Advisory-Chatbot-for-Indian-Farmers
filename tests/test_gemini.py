"""
Tests for the Gemini LLM service.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestGeminiService:
    """Test Gemini LLM integration."""

    @pytest.mark.asyncio
    async def test_classify_intent_weather(self):
        """Test intent classification for weather queries."""
        from app.services.gemini_llm import GeminiService

        with patch("google.generativeai.GenerativeModel") as MockModel:
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "weather"
            mock_instance.generate_content.return_value = mock_response
            MockModel.return_value = mock_instance

            intent = await GeminiService.classify_intent("What's the weather today?")
            assert intent == "weather"

    @pytest.mark.asyncio
    async def test_classify_intent_price(self):
        """Test intent classification for price queries."""
        from app.services.gemini_llm import GeminiService

        with patch("google.generativeai.GenerativeModel") as MockModel:
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "price"
            mock_instance.generate_content.return_value = mock_response
            MockModel.return_value = mock_instance

            intent = await GeminiService.classify_intent("tomato ka bhav kya hai")
            assert intent == "price"

    @pytest.mark.asyncio
    async def test_get_greeting_english(self):
        """Test English greeting generation."""
        from app.services.gemini_llm import GeminiService
        greeting = await GeminiService.get_greeting("Ram", "English")
        assert "KrishiMitra" in greeting
        assert "Ram" in greeting

    @pytest.mark.asyncio
    async def test_get_greeting_hindi(self):
        """Test Hindi greeting generation."""
        from app.services.gemini_llm import GeminiService
        greeting = await GeminiService.get_greeting("राम", "hi")
        assert "कृषि मित्र" in greeting

    @pytest.mark.asyncio
    async def test_get_help_english(self):
        """Test English help message."""
        from app.services.gemini_llm import GeminiService
        help_msg = await GeminiService.get_help_message("English")
        assert "Disease Detection" in help_msg
        assert "Weather" in help_msg

    @pytest.mark.asyncio
    async def test_get_help_hindi(self):
        """Test Hindi help message."""
        from app.services.gemini_llm import GeminiService
        help_msg = await GeminiService.get_help_message("Hindi")
        assert "फसल रोग" in help_msg
