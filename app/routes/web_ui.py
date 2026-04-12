"""
Web UI Routes.
Provides a beautiful, interactive web interface to chat with KrishiMitra.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os

from app.services.gemini_llm import GeminiService
from app.services.weather import WeatherService
from app.services.market import MarketService
from app.services.rag_engine import RAGEngine
from app.services.response_formatter import ResponseFormatter
from app.routes.webhook import get_or_create_farmer, extract_commodity
from app.utils.logger import logger

router = APIRouter(tags=["Web UI"])


class ChatRequest(BaseModel):
    message: str
    phone: str = "web_user"


@router.get("/chat", response_class=HTMLResponse)
async def get_web_ui():
    """Serve the Web Chat Interface."""
    # Build absolute path to templates dir
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    template_path = os.path.join(base_dir, "templates", "index.html")
    
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)


@router.post("/api/chat")
async def process_web_message(request: ChatRequest):
    """Process message and return response directly to the web client."""
    from_number = request.phone
    body = request.message
    body_lower = body.lower().strip()
    
    try:
        farmer = await get_or_create_farmer(from_number, "Web User")
        language = farmer.get("language", "en")
        
        # ── Quick commands ──────────────
        if body_lower in ["hi", "hello", "hey", "namaskar", "namaste", "नमस्कार", "नमस्ते"]:
            response = await GeminiService.get_greeting(farmer.get("name", ""), language)
            return {"reply": response}

        if body_lower in ["help", "menu", "मदद", "सहायता"]:
            response = await GeminiService.get_help_message(language)
            return {"reply": response}
            
        # ── Classify intent ──────────────
        intent = await GeminiService.classify_intent(body)
        
        if intent == "weather":
            # Just use a default location for web demo
            weather_data = await WeatherService.get_weather_by_city("Pune")
            llm_response = await GeminiService.generate_weather_response(
                weather_data, farmer.get("crops", []), language
            )
            response = ResponseFormatter.format_weather_response(weather_data, llm_response)
            
        elif intent == "price":
            commodity = extract_commodity(body, farmer.get("crops", []))
            if not commodity:
                response = "💰 Which crop's price would you like to know?\nExamples:\n• tomato price\n• potato rate"
            else:
                price_data = await MarketService.get_prices(commodity)
                prices_text = MarketService.format_prices_text(price_data)
                llm_response = await GeminiService.generate_market_response(commodity, prices_text, language)
                response = ResponseFormatter.format_price_response(price_data, llm_response)
                
        elif intent == "scheme":
            schemes = RAGEngine.search_schemes(body)
            schemes_text = "\n\n".join(schemes)
            llm_response = await GeminiService.generate_scheme_response(
                schemes_text, "India", [], 0, language
            )
            response = ResponseFormatter.format_scheme_response(llm_response)
            
        else:
            response = await GeminiService.generate_general_response(
                body,
                context={"location": "Pune", "crops": []},
                language=language,
            )
            
        return {"reply": response}

    except Exception as e:
        logger.error(f"❌ Web chat error: {e}")
        return {"reply": "🙏 Sorry, I'm having trouble connecting to my database right now. Please try again."}
