"""
Response Formatter Service.
Formats AI responses for WhatsApp delivery with emojis, structure, and readability.
"""

from app.utils.logger import logger


class ResponseFormatter:
    """Format responses for WhatsApp message delivery."""

    @classmethod
    def format_disease_response(cls, disease_data: dict, llm_response: str) -> str:
        """Format disease detection response for WhatsApp."""
        confidence = disease_data.get("confidence", 0)
        disease_name = disease_data.get("disease_name", "Unknown")
        crop = disease_data.get("crop", "Unknown")
        is_healthy = disease_data.get("is_healthy", False)

        if is_healthy:
            header = f"✅ *Your {crop} plant looks healthy!*\n"
            header += f"🔬 Confidence: {confidence:.0%}\n"
            header += "─" * 30 + "\n\n"
            return header + "Great news! Your plant appears to be in good condition. Keep up the good farming practices! 🌱"

        header = f"🔬 *Disease Detected: {disease_name}*\n"
        header += f"🌿 Crop: {crop}\n"
        header += f"📊 Confidence: {confidence:.0%}\n"
        header += "─" * 30 + "\n\n"

        # Add top predictions if confidence is not very high
        if confidence < 0.85:
            top_preds = disease_data.get("top_predictions", [])
            if len(top_preds) > 1:
                header += "📋 *Other possibilities:*\n"
                for pred in top_preds[1:3]:
                    header += f"  • {pred['disease']} ({pred['confidence']:.0%})\n"
                header += "\n"

        return header + llm_response

    @classmethod
    def format_weather_response(cls, weather_data: dict, llm_response: str) -> str:
        """Format weather response for WhatsApp."""
        location = weather_data.get("location", "Your Location")
        temp = weather_data.get("temperature", "N/A")
        humidity = weather_data.get("humidity", "N/A")
        desc = weather_data.get("description", "N/A")

        header = f"☀️ *Weather — {location}*\n"
        header += f"🌡️ Temperature: {temp}°C\n"
        header += f"💧 Humidity: {humidity}%\n"
        header += f"🌤️ Conditions: {desc.title()}\n"
        header += "─" * 30 + "\n\n"

        if weather_data.get("is_fallback"):
            header += "⚠️ _Using estimated data. Set your location for accurate info._\n\n"

        return header + llm_response

    @classmethod
    def format_price_response(cls, price_data: dict, llm_response: str) -> str:
        """Format market price response for WhatsApp."""
        commodity = price_data.get("commodity", "Unknown")
        avg_price = price_data.get("average_price", 0)
        best_market = price_data.get("best_market", "N/A")

        header = f"💰 *Market Prices — {commodity}*\n"
        header += f"📊 Average: ₹{avg_price}/quintal\n"
        header += f"🏆 Best Market: {best_market}\n"
        header += "─" * 30 + "\n\n"

        # Add price table
        prices = price_data.get("prices", [])
        if prices:
            header += "*Mandi-wise Prices:*\n"
            for p in prices:
                header += f"📍 {p['market']}\n"
                header += f"   ₹{p['price_min']} - ₹{p['price_max']}/{p['unit']}\n"
            header += "\n"

        return header + llm_response

    @classmethod
    def format_scheme_response(cls, llm_response: str) -> str:
        """Format government scheme response."""
        header = "📋 *Government Agricultural Schemes*\n"
        header += "─" * 30 + "\n\n"
        return header + llm_response

    @classmethod
    def format_error_response(cls, error_type: str = "general", language: str = "en") -> str:
        """Generate user-friendly error messages."""
        errors = {
            "general": {
                "en": "⚠️ Sorry, something went wrong. Please try again in a moment.\n\nIf the issue persists, type *help* for assistance.",
                "hi": "⚠️ क्षमा करें, कुछ गलत हो गया। कृपया कुछ देर बाद पुनः प्रयास करें।\n\nसमस्या बनी रहे तो *help* लिखें।",
            },
            "image_quality": {
                "en": "📸 The image quality is too low for accurate detection.\n\nPlease send a *clear, close-up photo* of the affected leaf:\n• Good lighting\n• Leaf fills most of the frame\n• Avoid blurry images",
                "hi": "📸 फोटो की गुणवत्ता कम है।\n\n*स्पष्ट, नज़दीकी फोटो* भेजें:\n• अच्छी रोशनी\n• पत्ती पूरे फ्रेम में हो\n• धुंधली फोटो न हो",
            },
            "no_location": {
                "en": "📍 I need your location for weather data.\n\nPlease share:\n• Type your city: *location Pune*\n• Or share your live location",
                "hi": "📍 मौसम के लिए आपका स्थान चाहिए।\n\n• शहर का नाम लिखें: *location पुणे*\n• या लाइव लोकेशन भेजें",
            },
            "model_not_loaded": {
                "en": "🤖 The disease detection model is currently loading. Please try again in a few minutes.",
                "hi": "🤖 रोग पहचान मॉडल लोड हो रहा है। कृपया कुछ मिनट बाद प्रयास करें।",
            },
        }

        lang = "hi" if language.lower() in ["hi", "hindi"] else "en"
        return errors.get(error_type, errors["general"]).get(lang, errors["general"]["en"])

    @classmethod
    def truncate_for_whatsapp(cls, text: str, max_length: int = 4000) -> str:
        """Truncate response to fit WhatsApp message limits."""
        if len(text) <= max_length:
            return text

        # Truncate at last complete paragraph
        truncated = text[:max_length]
        last_newline = truncated.rfind("\n\n")
        if last_newline > max_length * 0.5:
            truncated = truncated[:last_newline]

        truncated += "\n\n_...Response truncated. Type *more* for details._"
        return truncated
