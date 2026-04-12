"""
Farmer data model for MongoDB.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Location(BaseModel):
    state: str = ""
    district: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None


class FarmerPreferences(BaseModel):
    notifications: bool = True
    language: str = "en"


class Farmer(BaseModel):
    """Farmer profile stored in MongoDB."""
    phone: str
    name: str = ""
    language: str = "en"
    location: Location = Location()
    crops: list[str] = []
    land_size_acres: float = 0.0
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    preferences: FarmerPreferences = FarmerPreferences()
    onboarding_complete: bool = False
    onboarding_step: int = 0


class FarmerUpdate(BaseModel):
    """Partial update model for farmer profiles."""
    name: Optional[str] = None
    language: Optional[str] = None
    location: Optional[Location] = None
    crops: Optional[list[str]] = None
    land_size_acres: Optional[float] = None
