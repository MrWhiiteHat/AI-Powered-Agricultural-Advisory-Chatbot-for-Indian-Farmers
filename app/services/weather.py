"""
Weather API Service using OpenWeatherMap.
Fetches current weather and 5-day forecast for farmer locations.
"""

import aiohttp
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()

BASE_URL = "https://api.openweathermap.org/data/2.5"


class WeatherService:
    """OpenWeatherMap weather data service."""

    @classmethod
    async def get_current_weather(cls, lat: float, lon: float) -> dict:
        """
        Get current weather for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Weather data dict
        """
        try:
            url = f"{BASE_URL}/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": settings.OPENWEATHER_API_KEY,
                "units": "metric",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        logger.error(f"Weather API error: {resp.status}")
                        return cls._fallback_weather()
                    
                    data = await resp.json()

            weather = {
                "location": data.get("name", "Unknown"),
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"] * 3.6,  # Convert m/s to km/h
                "clouds": data.get("clouds", {}).get("all", 0),
                "rain": data.get("rain", {}).get("1h", 0),
            }

            logger.info(f"🌤️ Weather fetched for {weather['location']}: {weather['temperature']}°C")
            return weather

        except Exception as e:
            logger.error(f"❌ Weather API failed: {e}")
            return cls._fallback_weather()

    @classmethod
    async def get_forecast(cls, lat: float, lon: float) -> list:
        """Get 5-day weather forecast."""
        try:
            url = f"{BASE_URL}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": settings.OPENWEATHER_API_KEY,
                "units": "metric",
                "cnt": 8,  # Next 24 hours (3-hour intervals)
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()

            forecast = []
            for item in data.get("list", []):
                forecast.append({
                    "datetime": item["dt_txt"],
                    "temp": item["main"]["temp"],
                    "humidity": item["main"]["humidity"],
                    "description": item["weather"][0]["description"],
                    "rain": item.get("rain", {}).get("3h", 0),
                })

            return forecast

        except Exception as e:
            logger.error(f"❌ Forecast API failed: {e}")
            return []

    @classmethod
    async def get_weather_by_city(cls, city: str, country: str = "IN") -> dict:
        """Get weather by city name (fallback when coordinates unavailable)."""
        try:
            url = f"{BASE_URL}/weather"
            params = {
                "q": f"{city},{country}",
                "appid": settings.OPENWEATHER_API_KEY,
                "units": "metric",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return cls._fallback_weather()
                    data = await resp.json()

            return {
                "location": data.get("name", city),
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"] * 3.6,
                "clouds": data.get("clouds", {}).get("all", 0),
                "rain": data.get("rain", {}).get("1h", 0),
            }
        except Exception as e:
            logger.error(f"❌ Weather by city failed: {e}")
            return cls._fallback_weather()

    @classmethod
    def _fallback_weather(cls) -> dict:
        """Return fallback weather data when API is unavailable."""
        return {
            "location": "Unknown",
            "temperature": 28.0,
            "feels_like": 30.0,
            "humidity": 65,
            "pressure": 1013,
            "description": "partly cloudy",
            "wind_speed": 12.0,
            "clouds": 40,
            "rain": 0,
            "is_fallback": True,
        }
