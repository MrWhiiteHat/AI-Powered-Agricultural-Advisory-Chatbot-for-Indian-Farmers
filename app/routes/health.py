"""
Health check and status routes.
"""

from fastapi import APIRouter
from app.config import get_settings
from app.database import Database
from app.services.disease_detector import DiseaseDetector

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check():
    """System health check endpoint."""
    # Check MongoDB
    db_connected = False
    try:
        if Database.client:
            await Database.client.admin.command("ping")
            db_connected = True
    except Exception:
        pass

    # Check model
    model_loaded = DiseaseDetector._model is not None

    return {
        "status": "healthy" if db_connected else "degraded",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "db_connected": db_connected,
        "model_loaded": model_loaded,
        "environment": settings.APP_ENV,
    }


@router.get("/api/v1/stats")
async def get_stats():
    """Get system statistics."""
    try:
        farmers_count = await Database.get_collection("farmers").count_documents({})
        conversations_count = await Database.get_collection("conversations").count_documents({})
        disease_logs_count = await Database.get_collection("disease_logs").count_documents({})
    except Exception:
        farmers_count = 0
        conversations_count = 0
        disease_logs_count = 0

    return {
        "total_farmers": farmers_count,
        "total_conversations": conversations_count,
        "total_disease_detections": disease_logs_count,
        "model_loaded": DiseaseDetector._model is not None,
    }
