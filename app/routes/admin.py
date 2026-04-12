"""
Admin API routes for managing farmers, diseases, and system data.
"""

from fastapi import APIRouter, HTTPException
from app.database import get_farmers_collection, get_disease_logs_collection
from app.services.disease_detector import DiseaseDetector
from app.config import get_settings

router = APIRouter(prefix="/api/v1", tags=["Admin"])
settings = get_settings()


@router.get("/diseases")
async def list_diseases():
    """List all detectable plant diseases."""
    classes = settings.DISEASE_CLASSES
    diseases = []
    for cls_name in classes:
        parts = cls_name.split("___")
        crop = parts[0].replace("_", " ")
        disease = parts[1].replace("_", " ").title() if len(parts) > 1 else "Unknown"
        diseases.append({
            "class_id": cls_name,
            "crop": crop,
            "disease": disease,
            "is_healthy": "healthy" in cls_name.lower(),
        })
    return {"total": len(diseases), "diseases": diseases}


@router.get("/farmers/{phone}")
async def get_farmer(phone: str):
    """Get farmer profile by phone number."""
    collection = get_farmers_collection()
    farmer = await collection.find_one({"phone": phone})
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    farmer["_id"] = str(farmer["_id"])
    return farmer


@router.get("/farmers")
async def list_farmers(limit: int = 20, skip: int = 0):
    """List all registered farmers."""
    collection = get_farmers_collection()
    farmers = []
    cursor = collection.find({}).skip(skip).limit(limit)
    async for farmer in cursor:
        farmer["_id"] = str(farmer["_id"])
        farmers.append(farmer)
    total = await collection.count_documents({})
    return {"total": total, "farmers": farmers}


@router.get("/disease-logs")
async def list_disease_logs(limit: int = 20, skip: int = 0):
    """List recent disease detection logs."""
    collection = get_disease_logs_collection()
    logs = []
    cursor = collection.find({}).sort("timestamp", -1).skip(skip).limit(limit)
    async for log in cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)
    total = await collection.count_documents({})
    return {"total": total, "logs": logs}
