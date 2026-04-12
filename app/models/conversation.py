"""
Conversation data models for MongoDB.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class Message(BaseModel):
    role: str  # "user" or "assistant"
    type: str = "text"  # "text", "image", "voice"
    content: str = ""
    media_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationContext(BaseModel):
    detected_disease: Optional[str] = None
    confidence: Optional[float] = None
    crop: Optional[str] = None
    intent: Optional[str] = None
    weather_data: Optional[dict] = None


class Conversation(BaseModel):
    """Conversation session stored in MongoDB."""
    farmer_phone: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[Message] = []
    context: ConversationContext = ConversationContext()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
