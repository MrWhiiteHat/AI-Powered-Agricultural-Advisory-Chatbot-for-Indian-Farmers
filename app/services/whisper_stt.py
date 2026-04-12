"""
Whisper Speech-to-Text Service.
Transcribes voice messages from WhatsApp.
Uses lazy imports so the app starts even without whisper installed.
"""

import os
from app.config import get_settings
from app.utils.logger import logger
from app.utils.helpers import cleanup_temp_file

settings = get_settings()


class WhisperService:
    """OpenAI Whisper speech-to-text service."""

    _model = None
    _available = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if Whisper is installed."""
        if cls._available is None:
            try:
                import whisper  # noqa: F401
                cls._available = True
            except ImportError:
                cls._available = False
                logger.warning("⚠️ openai-whisper not installed. Voice input disabled.")
        return cls._available

    @classmethod
    def load_model(cls):
        """Load Whisper model (lazy loading)."""
        if not cls.is_available():
            return None

        if cls._model is None:
            import whisper
            logger.info(f"🎙️ Loading Whisper model: {settings.WHISPER_MODEL_SIZE}")
            cls._model = whisper.load_model(settings.WHISPER_MODEL_SIZE)
            logger.info("✅ Whisper model loaded")
        return cls._model

    @classmethod
    def transcribe(cls, audio_path: str, language: str = None) -> dict:
        """Transcribe an audio file using Gemini natively."""
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            logger.info("🎙️ Uploading audio to Gemini for native transcription...")
            audio_file = client.files.upload(file=audio_path)
            
            # Gemini 2.5 Flash Lite natively supports audio!
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=["Please transcribe this audio into Hindi text perfectly. Output ONLY the transcribed text, without any english translations.", audio_file]
            )
            
            text = response.text.strip()
            
            transcription = {
                "text": text,
                "language": "hi",
                "segments": []
            }

            logger.info(f"🎙️ Transcribed via Gemini: {text[:100]}...")
            return transcription

        except Exception as e:
            logger.error(f"❌ Gemini transcription failed: {e}")
            return {
                "text": "",
                "language": "unknown",
                "segments": [],
                "error": str(e),
            }
        finally:
            cleanup_temp_file(audio_path)

    @classmethod
    async def transcribe_from_url(cls, audio_url: str, auth: tuple = None, language: str = None) -> dict:
        """
        Download audio from URL and transcribe.

        Args:
            audio_url: URL of the audio file (e.g., Twilio media URL)
            auth: Optional (username, password) tuple for authentication
            language: Optional language hint

        Returns:
            Transcription result dict
        """
        if not cls.is_available():
            return {
                "text": "",
                "language": "unknown",
                "segments": [],
                "error": "Whisper not installed",
            }

        from app.utils.helpers import download_media_to_file

        audio_path = await download_media_to_file(audio_url, suffix=".ogg", auth=auth)
        return cls.transcribe(audio_path, language)
