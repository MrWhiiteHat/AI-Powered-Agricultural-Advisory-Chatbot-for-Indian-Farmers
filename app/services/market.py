"""
Market Price Service.
Fetches and compares agricultural commodity prices from Agmarknet / data.gov.in.
Falls back to sample data when API is unreachable.
"""

import aiohttp
from app.utils.logger import logger


# ── Sample fallback data for demo ──────────────────────────────
SAMPLE_PRICES = {
    "tomato": [
        {"market": "Azadpur Mandi, Delhi", "price_min": 1200, "price_max": 1800, "unit": "quintal"},
        {"market": "Vashi Mandi, Mumbai", "price_min": 1400, "price_max": 2000, "unit": "quintal"},
        {"market": "Koyambedu, Chennai", "price_min": 1100, "price_max": 1600, "unit": "quintal"},
        {"market": "Devaraja Market, Mysuru", "price_min": 1000, "price_max": 1500, "unit": "quintal"},
    ],
    "potato": [
        {"market": "Azadpur Mandi, Delhi", "price_min": 800, "price_max": 1200, "unit": "quintal"},
        {"market": "Vashi Mandi, Mumbai", "price_min": 900, "price_max": 1300, "unit": "quintal"},
        {"market": "Howrah, Kolkata", "price_min": 700, "price_max": 1100, "unit": "quintal"},
    ],
    "onion": [
        {"market": "Lasalgaon, Maharashtra", "price_min": 1500, "price_max": 2200, "unit": "quintal"},
        {"market": "Azadpur Mandi, Delhi", "price_min": 1600, "price_max": 2400, "unit": "quintal"},
        {"market": "Pimpalgaon, Maharashtra", "price_min": 1400, "price_max": 2100, "unit": "quintal"},
    ],
    "wheat": [
        {"market": "Narela Mandi, Delhi", "price_min": 2200, "price_max": 2600, "unit": "quintal"},
        {"market": "Indore Mandi, MP", "price_min": 2100, "price_max": 2500, "unit": "quintal"},
        {"market": "Hapur Mandi, UP", "price_min": 2000, "price_max": 2400, "unit": "quintal"},
    ],
    "rice": [
        {"market": "Karnal, Haryana", "price_min": 3000, "price_max": 3800, "unit": "quintal"},
        {"market": "Azadpur Mandi, Delhi", "price_min": 3200, "price_max": 4000, "unit": "quintal"},
    ],
    "cotton": [
        {"market": "Rajkot, Gujarat", "price_min": 6000, "price_max": 7200, "unit": "quintal"},
        {"market": "Akola, Maharashtra", "price_min": 5800, "price_max": 7000, "unit": "quintal"},
    ],
}

# Commodity name mappings (Hindi → English)
COMMODITY_MAP = {
    "टमाटर": "tomato",
    "आलू": "potato",
    "प्याज": "onion",
    "गेहूं": "wheat",
    "चावल": "rice",
    "कपास": "cotton",
    "धान": "rice",
    "सोयाबीन": "soybean",
}


class MarketService:
    """Agricultural market price service."""

    @classmethod
    async def get_prices(cls, commodity: str) -> dict:
        """
        Get market prices for a commodity.
        
        Args:
            commodity: Commodity name (English or Hindi)
            
        Returns:
            Dict with prices, average, and best market
        """
        # Normalize commodity name
        commodity_lower = commodity.lower().strip()
        commodity_en = COMMODITY_MAP.get(commodity_lower, commodity_lower)

        # Try live API first
        try:
            prices = await cls._fetch_live_prices(commodity_en)
            if prices:
                return cls._format_prices(commodity_en, prices)
        except Exception as e:
            logger.warning(f"⚠️ Live price fetch failed, using sample data: {e}")

        # Fallback to sample data
        sample = SAMPLE_PRICES.get(commodity_en, [])
        if not sample:
            # Try fuzzy matching
            for key in SAMPLE_PRICES:
                if key in commodity_en or commodity_en in key:
                    sample = SAMPLE_PRICES[key]
                    commodity_en = key
                    break

        if not sample:
            return {
                "commodity": commodity,
                "prices": [],
                "average_price": 0,
                "best_market": None,
                "message": f"No price data available for '{commodity}'. Available: {', '.join(SAMPLE_PRICES.keys())}",
            }

        return cls._format_prices(commodity_en, sample)

    @classmethod
    async def _fetch_live_prices(cls, commodity: str) -> list:
        """Attempt to fetch live prices from data.gov.in API."""
        try:
            url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
            params = {
                "api-key": "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b",
                "format": "json",
                "filters[commodity]": commodity.title(),
                "limit": 10,
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        records = data.get("records", [])
                        if records:
                            return [
                                {
                                    "market": f"{r.get('market', '')}, {r.get('state', '')}",
                                    "price_min": float(r.get("min_price", 0)),
                                    "price_max": float(r.get("max_price", 0)),
                                    "unit": "quintal",
                                }
                                for r in records
                            ]
        except Exception:
            pass
        return []

    @classmethod
    def _format_prices(cls, commodity: str, prices: list) -> dict:
        """Format price data with analytics."""
        avg_prices = [(p["price_min"] + p["price_max"]) / 2 for p in prices]
        avg_price = sum(avg_prices) / len(avg_prices) if avg_prices else 0

        best_idx = avg_prices.index(max(avg_prices)) if avg_prices else 0
        best_market = prices[best_idx]["market"] if prices else None

        return {
            "commodity": commodity.title(),
            "prices": prices,
            "average_price": round(avg_price, 2),
            "best_market": best_market,
            "best_price": round(max(avg_prices), 2) if avg_prices else 0,
        }

    @classmethod
    def format_prices_text(cls, price_data: dict) -> str:
        """Format price data as readable text for LLM context."""
        lines = [f"Commodity: {price_data['commodity']}"]
        for p in price_data.get("prices", []):
            lines.append(
                f"- {p['market']}: ₹{p['price_min']}-{p['price_max']}/{p['unit']}"
            )
        lines.append(f"Average Price: ₹{price_data.get('average_price', 'N/A')}/quintal")
        lines.append(f"Best Market: {price_data.get('best_market', 'N/A')}")
        return "\n".join(lines)
