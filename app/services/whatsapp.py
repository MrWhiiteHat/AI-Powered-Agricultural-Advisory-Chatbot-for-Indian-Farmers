"""
WhatsApp message handling via Twilio.
Sends and receives messages through the Twilio WhatsApp API.
"""

from twilio.rest import Client
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class WhatsAppService:
    """Handles WhatsApp message sending via Twilio."""

    _client: Client = None  # type: ignore

    @classmethod
    def get_client(cls) -> Client:
        if cls._client is None:
            cls._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        return cls._client

    @classmethod
    def send_message(cls, to: str, body: str, media_url: str = None) -> str:
        """
        Send a WhatsApp message via Twilio.
        
        Args:
            to: Recipient phone number (e.g., "whatsapp:+919876543210")
            body: Message text
            media_url: Optional media URL to attach
            
        Returns:
            Message SID
        """
        try:
            client = cls.get_client()
            kwargs = {
                "from_": settings.TWILIO_WHATSAPP_NUMBER,
                "to": to,
                "body": body,
            }
            if media_url:
                kwargs["media_url"] = [media_url]

            message = client.messages.create(**kwargs)
            logger.info(f"📤 Message sent to {to}: SID={message.sid}")
            return message.sid
        except Exception as e:
            if "exceeded the 50 daily messages limit" in str(e):
                logger.info(f"🛑 Outbound text blocked by Twilio's free-tier limits. Delivery simulated locally.")
                return "SIMULATED_SID"
            logger.error(f"❌ Failed to send WhatsApp message to {to}: {e}")
            raise

    @classmethod
    def send_long_message(cls, to: str, body: str, max_length: int = 1500):
        """
        Send a long message split into chunks if needed.
        WhatsApp has a ~4096 char limit, but shorter is better.
        """
        if len(body) <= max_length:
            return cls.send_message(to, body)

        # Split by paragraphs
        paragraphs = body.split("\n\n")
        current_chunk = ""
        chunk_num = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 > max_length:
                if current_chunk:
                    chunk_num += 1
                    cls.send_message(to, current_chunk.strip())
                current_chunk = para + "\n\n"
            else:
                current_chunk += para + "\n\n"

        if current_chunk.strip():
            cls.send_message(to, current_chunk.strip())

    @classmethod
    def parse_incoming_message(cls, form_data: dict) -> dict:
        """
        Parse incoming Twilio webhook form data into a structured dict.
        
        Returns:
            Dict with keys: from_number, body, num_media, media_url, media_type, message_sid
        """
        parsed = {
            "from_number": form_data.get("From", ""),
            "to_number": form_data.get("To", ""),
            "body": form_data.get("Body", "").strip(),
            "num_media": int(form_data.get("NumMedia", 0)),
            "media_url": None,
            "media_type": None,
            "message_sid": form_data.get("MessageSid", ""),
            "profile_name": form_data.get("ProfileName", ""),
        }

        # Extract media if present
        if parsed["num_media"] > 0:
            parsed["media_url"] = form_data.get("MediaUrl0", "")
            parsed["media_type"] = form_data.get("MediaContentType0", "")

        return parsed
