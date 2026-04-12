"""
WhatsApp Webhook Routes — The main entry point for all farmer interactions.
Handles incoming messages from Twilio, processes them through the AI pipeline,
and sends responses back via WhatsApp.
"""

from datetime import datetime
from fastapi import APIRouter, Request, Response, BackgroundTasks
from app.config import get_settings
from app.database import (
    get_farmers_collection,
    get_conversations_collection,
    get_disease_logs_collection,
)
from app.services.whatsapp import WhatsAppService
from app.services.whisper_stt import WhisperService
from app.services.disease_detector import DiseaseDetector
from app.services.gemini_llm import GeminiService
from app.services.weather import WeatherService
from app.services.market import MarketService
from app.services.rag_engine import RAGEngine
from app.services.response_formatter import ResponseFormatter
from app.utils.helpers import (
    download_media,
    check_image_quality,
)
from app.utils.logger import logger

router = APIRouter(tags=["Webhook"])
settings = get_settings()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TWILIO WHATSAPP WEBHOOK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/webhook/whatsapp")
async def verify_webhook():
    """Webhook verification endpoint for Twilio."""
    return {"status": "webhook active", "app": settings.APP_NAME}


@router.post("/webhook/whatsapp")
async def handle_whatsapp_message(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook handler for incoming WhatsApp messages.
    Twilio sends a POST request with form data for each incoming message.
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        form_dict = dict(form_data)

        # Parse the incoming message
        message = WhatsAppService.parse_incoming_message(form_dict)
        from_number = message["from_number"]
        body = message["body"]
        num_media = message["num_media"]
        media_url = message["media_url"]
        media_type = message["media_type"]

        logger.info(
            f"📩 Message from {from_number}: "
            f"text='{body[:80]}' media={num_media} type={media_type}"
        )

        # Process in background to respond to Twilio quickly
        background_tasks.add_task(
            process_message,
            from_number=from_number,
            body=body,
            num_media=num_media,
            media_url=media_url,
            media_type=media_type,
            profile_name=message.get("profile_name", ""),
        )

        # Return empty TwiML response immediately
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
        return Response(content=twiml, media_type="application/xml")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MESSAGE PROCESSING PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def process_message(
    from_number: str,
    body: str,
    num_media: int,
    media_url: str,
    media_type: str,
    profile_name: str = "",
):
    """
    Main message processing pipeline.
    Routes messages to appropriate handlers based on type and intent.
    """
    try:
        # ── Step 1: Get or create farmer profile ────────
        farmer = await get_or_create_farmer(from_number, profile_name)
        language = farmer.get("language", "en")
        lang_name = "Hindi" if language == "hi" else "English"

        # ── Step 2: Handle message by type ──────────────
        if num_media > 0 and media_type:
            if "image" in media_type:
                # Image message → Disease Detection
                await handle_image_message(from_number, media_url, farmer, lang_name)
            elif "audio" in media_type or "ogg" in media_type:
                # Voice message → Whisper STT → Process text
                await handle_voice_message(from_number, media_url, farmer, lang_name)
            else:
                WhatsAppService.send_message(
                    from_number,
                    ResponseFormatter.format_error_response("general", language),
                )
        elif body:
            # Text message → Intent-based processing
            await handle_text_message(from_number, body, farmer, lang_name)
        else:
            WhatsAppService.send_message(
                from_number,
                "🙏 Please send a text message, photo, or voice note.",
            )

        # Update last active timestamp
        await get_farmers_collection().update_one(
            {"phone": from_number},
            {"$set": {"last_active": datetime.utcnow()}},
        )

    except Exception as e:
        logger.error(f"❌ Message processing error for {from_number}: {e}")
        try:
            WhatsAppService.send_message(
                from_number,
                ResponseFormatter.format_error_response("general"),
            )
        except Exception:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HANDLER: IMAGE MESSAGES (Disease Detection)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def handle_image_message(
    from_number: str,
    media_url: str,
    farmer: dict,
    language: str,
):
    """Process image messages for disease detection."""
    try:
        # Download image from Twilio
        auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        image_bytes = await download_media(media_url, auth=auth)

        # Check image quality
        quality = check_image_quality(image_bytes)
        if not quality["acceptable"]:
            WhatsAppService.send_message(
                from_number,
                ResponseFormatter.format_error_response("image_quality", farmer.get("language", "en")),
            )
            return

        # Run disease detection CNN
        prediction = DiseaseDetector.predict(image_bytes)

        # Get treatment info from RAG
        treatment_query = f"{prediction['crop']} {prediction['disease_name']} treatment"
        treatments = RAGEngine.search_treatments(treatment_query)
        treatment_context = "\n".join(treatments) if treatments else ""

        # Generate response via Gemini
        llm_response = await GeminiService.generate_disease_response(
            crop=prediction["crop"],
            disease_name=prediction["disease_name"],
            confidence=prediction["confidence"],
            top_predictions=prediction["top_predictions"],
            language=language,
        )

        # Format response
        response = ResponseFormatter.format_disease_response(prediction, llm_response)
        response = ResponseFormatter.truncate_for_whatsapp(response)

        # Send response
        WhatsAppService.send_long_message(from_number, response)

        # Log disease detection
        await log_disease_detection(from_number, media_url, prediction, llm_response)

    except Exception as e:
        logger.error(f"❌ Image processing error: {e}")
        WhatsAppService.send_message(
            from_number,
            ResponseFormatter.format_error_response("general", farmer.get("language", "en")),
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HANDLER: VOICE MESSAGES (Whisper STT)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def handle_voice_message(
    from_number: str,
    media_url: str,
    farmer: dict,
    language: str,
):
    """Process voice messages via Whisper, then handle as text."""
    try:
        # Acknowledge receipt
        WhatsAppService.send_message(from_number, "🎙️ Processing your voice message...")

        # Transcribe with Whisper
        auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        transcription = await WhisperService.transcribe_from_url(
            media_url, auth=auth, language=farmer.get("language")
        )

        text = transcription.get("text", "")
        detected_lang = transcription.get("language", "en")

        if not text:
            WhatsAppService.send_message(
                from_number,
                "⚠️ Sorry, I couldn't understand the voice message. Please try again or type your question.",
            )
            return

        # Update language preference if detected
        if detected_lang in ["hi", "en"]:
            await get_farmers_collection().update_one(
                {"phone": from_number},
                {"$set": {"language": detected_lang}},
            )

        logger.info(f"🎙️ Transcribed ({detected_lang}): {text}")

        # Process the transcribed text
        lang_name = "Hindi" if detected_lang == "hi" else "English"
        await handle_text_message(from_number, text, farmer, lang_name)

    except Exception as e:
        logger.error(f"❌ Voice processing error: {e}")
        WhatsAppService.send_message(
            from_number,
            "⚠️ Voice processing failed. Please type your question instead.",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HANDLER: TEXT MESSAGES (Intent-based routing)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def handle_text_message(
    from_number: str,
    body: str,
    farmer: dict,
    language: str,
):
    """Process text messages based on intent classification."""
    try:
        body_lower = body.lower().strip()

        # ── Quick commands (no LLM needed) ──────────────
        if body_lower in ["hi", "hello", "hey", "namaskar", "namaste", "नमस्कार", "नमस्ते"]:
            response = await GeminiService.get_greeting(
                farmer.get("name", ""), language
            )
            WhatsAppService.send_message(from_number, response)
            return

        if body_lower in ["help", "menu", "मदद", "सहायता"]:
            response = await GeminiService.get_help_message(language)
            WhatsAppService.send_message(from_number, response)
            return

        # ── Profile commands ────────────────────────────
        if await handle_profile_commands(from_number, body_lower, farmer):
            return

        # ── Classify intent via Gemini ──────────────────
        intent = await GeminiService.classify_intent(body)

        if intent == "weather":
            await handle_weather_intent(from_number, body, farmer, language)
        elif intent == "price":
            await handle_price_intent(from_number, body, farmer, language)
        elif intent == "scheme":
            await handle_scheme_intent(from_number, body, farmer, language)
        elif intent == "disease":
            # Text-based disease query (no image)
            response = await GeminiService.generate_general_response(
                body,
                context={
                    "location": farmer.get("location", {}).get("district", ""),
                    "crops": farmer.get("crops", []),
                },
                language=language,
            )
            WhatsAppService.send_long_message(from_number, response)
        else:
            # General agricultural question
            response = await GeminiService.generate_general_response(
                body,
                context={
                    "location": farmer.get("location", {}).get("district", ""),
                    "crops": farmer.get("crops", []),
                },
                language=language,
            )
            WhatsAppService.send_long_message(from_number, response)

    except Exception as e:
        logger.error(f"❌ Text processing error: {e}")
        WhatsAppService.send_message(
            from_number,
            ResponseFormatter.format_error_response("general", farmer.get("language", "en")),
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTENT HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def handle_weather_intent(from_number: str, body: str, farmer: dict, language: str):
    """Handle weather queries."""
    location = farmer.get("location", {})
    lat = location.get("lat")
    lon = location.get("lon")
    district = location.get("district", "")

    if lat and lon:
        weather_data = await WeatherService.get_current_weather(lat, lon)
        forecast = await WeatherService.get_forecast(lat, lon)
        weather_data["forecast"] = forecast
    elif district:
        weather_data = await WeatherService.get_weather_by_city(district)
    else:
        WhatsAppService.send_message(
            from_number,
            ResponseFormatter.format_error_response("no_location", farmer.get("language", "en")),
        )
        return

    crops = farmer.get("crops", [])
    llm_response = await GeminiService.generate_weather_response(
        weather_data, crops, language
    )
    response = ResponseFormatter.format_weather_response(weather_data, llm_response)
    WhatsAppService.send_long_message(from_number, response)


async def handle_price_intent(from_number: str, body: str, farmer: dict, language: str):
    """Handle market price queries."""
    # Extract commodity from message
    commodity = extract_commodity(body, farmer.get("crops", []))

    if not commodity:
        WhatsAppService.send_message(
            from_number,
            "💰 Which crop's price would you like to know?\n\n"
            "Examples:\n• tomato price\n• टमाटर का भाव\n• potato rate",
        )
        return

    price_data = await MarketService.get_prices(commodity)
    prices_text = MarketService.format_prices_text(price_data)
    llm_response = await GeminiService.generate_market_response(
        commodity, prices_text, language
    )
    response = ResponseFormatter.format_price_response(price_data, llm_response)
    WhatsAppService.send_long_message(from_number, response)


async def handle_scheme_intent(from_number: str, body: str, farmer: dict, language: str):
    """Handle government scheme queries."""
    # Search schemes via RAG
    schemes = RAGEngine.search_schemes(body)
    schemes_text = "\n\n".join(schemes)

    location = farmer.get("location", {})
    location_str = f"{location.get('district', '')}, {location.get('state', '')}"
    crops = farmer.get("crops", [])
    land_size = farmer.get("land_size_acres", 0)

    llm_response = await GeminiService.generate_scheme_response(
        schemes_text, location_str, crops, land_size, language
    )
    response = ResponseFormatter.format_scheme_response(llm_response)
    WhatsAppService.send_long_message(from_number, response)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROFILE & UTILITY FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def handle_profile_commands(from_number: str, body: str, farmer: dict) -> bool:
    """Handle profile setting commands. Returns True if handled."""
    collection = get_farmers_collection()
    language = farmer.get("language", "en")

    # Language change
    if body.startswith("language ") or body.startswith("भाषा "):
        lang = body.split(" ", 1)[1].strip().lower()
        lang_code = "hi" if lang in ["hindi", "हिंदी", "hi"] else "en"
        await collection.update_one(
            {"phone": from_number},
            {"$set": {"language": lang_code, "preferences.language": lang_code}},
        )
        msg = "✅ भाषा हिंदी में बदल दी गई!" if lang_code == "hi" else "✅ Language set to English!"
        WhatsAppService.send_message(from_number, msg)
        return True

    # Name
    for prefix in ["my name is ", "मेरा नाम ", "name "]:
        if body.startswith(prefix):
            name = body[len(prefix):].strip().title()
            await collection.update_one(
                {"phone": from_number}, {"$set": {"name": name}}
            )
            msg = f"✅ Name set to: {name}" if language == "en" else f"✅ नाम सेट: {name}"
            WhatsAppService.send_message(from_number, msg)
            return True

    # Location
    for prefix in ["location ", "my location ", "मेरा गांव ", "मेरा शहर "]:
        if body.startswith(prefix):
            loc = body[len(prefix):].strip().title()
            await collection.update_one(
                {"phone": from_number},
                {"$set": {"location.district": loc}},
            )
            msg = f"📍 Location set to: {loc}" if language == "en" else f"📍 स्थान: {loc}"
            WhatsAppService.send_message(from_number, msg)
            return True

    # Crops
    for prefix in ["my crop ", "my crops ", "मेरी फसल "]:
        if body.startswith(prefix):
            crops_str = body[len(prefix):].strip()
            crops = [c.strip().lower() for c in crops_str.replace(",", " ").split()]
            await collection.update_one(
                {"phone": from_number}, {"$set": {"crops": crops}}
            )
            msg = f"🌾 Crops set: {', '.join(crops)}" if language == "en" else f"🌾 फसलें: {', '.join(crops)}"
            WhatsAppService.send_message(from_number, msg)
            return True

    return False


async def get_or_create_farmer(phone: str, profile_name: str = "") -> dict:
    """Get existing farmer or create new profile."""
    collection = get_farmers_collection()
    farmer = await collection.find_one({"phone": phone})

    if farmer:
        return farmer

    # Create new farmer profile
    new_farmer = {
        "phone": phone,
        "name": profile_name or "",
        "language": "en",
        "location": {"state": "", "district": "", "lat": None, "lon": None},
        "crops": [],
        "land_size_acres": 0,
        "registered_at": datetime.utcnow(),
        "last_active": datetime.utcnow(),
        "preferences": {"notifications": True, "language": "en"},
        "onboarding_complete": False,
        "onboarding_step": 0,
    }

    await collection.insert_one(new_farmer)
    logger.info(f"👨‍🌾 New farmer registered: {phone} ({profile_name})")
    return new_farmer


async def log_disease_detection(
    phone: str, image_url: str, prediction: dict, treatment: str
):
    """Log disease detection to MongoDB."""
    try:
        collection = get_disease_logs_collection()
        await collection.insert_one({
            "farmer_phone": phone,
            "image_url": image_url,
            "predicted_class": prediction["disease_class"],
            "disease_name": prediction["disease_name"],
            "crop": prediction["crop"],
            "confidence": prediction["confidence"],
            "is_healthy": prediction["is_healthy"],
            "top_3": prediction["top_predictions"],
            "treatment_provided": treatment[:500],
            "timestamp": datetime.utcnow(),
        })
    except Exception as e:
        logger.error(f"❌ Failed to log disease detection: {e}")


def extract_commodity(text: str, farmer_crops: list = None) -> str:
    """Extract commodity name from a price query message."""
    text_lower = text.lower()

    # Direct commodity keywords
    commodities = [
        "tomato", "potato", "onion", "wheat", "rice", "cotton",
        "soybean", "maize", "corn", "sugarcane", "chilli",
        "टमाटर", "आलू", "प्याज", "गेहूं", "चावल", "कपास",
    ]

    for commodity in commodities:
        if commodity in text_lower:
            return commodity

    # Check farmer's registered crops
    if farmer_crops:
        return farmer_crops[0]

    return ""
