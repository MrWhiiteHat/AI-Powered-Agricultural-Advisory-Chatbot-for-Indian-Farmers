"""
API request/response schemas.
"""

from pydantic import BaseModel
from typing import Optional


class DiseaseDetectionRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None


class DiseaseDetectionResponse(BaseModel):
    disease: str
    confidence: float
    crop: str
    is_healthy: bool
    top_predictions: list[dict]
    treatment: Optional[str] = None


class WeatherResponse(BaseModel):
    location: str
    temperature: float
    humidity: float
    description: str
    wind_speed: float
    forecast: list[dict] = []
    advisory: Optional[str] = None


class MarketPriceResponse(BaseModel):
    commodity: str
    prices: list[dict]
    average_price: float
    best_market: Optional[str] = None


class WhatsAppMessage(BaseModel):
    """Parsed WhatsApp incoming message."""
    from_number: str
    to_number: str
    body: str = ""
    num_media: int = 0
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    message_sid: str = ""


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    db_connected: bool
    model_loaded: bool
