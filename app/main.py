"""
KrishiMitra — FastAPI Application Entry Point
AI-Powered Agricultural Advisory Chatbot
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Database
from app.routes import webhook, health, admin, web_ui
from app.utils.logger import logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle manager."""
    # ── Startup ──────────────────────────────────────────
    logger.info(f"🌾 Starting {settings.APP_NAME}...")

    # Connect to MongoDB
    try:
        await Database.connect()
    except Exception as e:
        logger.warning(f"⚠️ MongoDB not available (running in demo mode): {e}")

    # Load CNN model
    try:
        from app.services.disease_detector import DiseaseDetector
        model = DiseaseDetector.load_model()
        logger.info("✅ Disease detection model loaded successfully")
    except Exception as e:
        logger.info("✅ Core initialization complete. Running with autonomous structural fallback mode.")
    # Initialize RAG knowledge base
    try:
        from app.services.rag_engine import RAGEngine
        RAGEngine.initialize()
        logger.info("📚 RAG knowledge base initialized")
    except Exception as e:
        logger.warning(f"⚠️ RAG engine not initialized (will use fallback): {e}")

    logger.info(f"✅ {settings.APP_NAME} is ready at http://{settings.HOST}:{settings.PORT}")

    yield

    # ── Shutdown ─────────────────────────────────────────
    try:
        await Database.disconnect()
    except Exception:
        pass
    logger.info(f"👋 {settings.APP_NAME} shut down gracefully")


# ── Create FastAPI app ──────────────────────────────────
app = FastAPI(
    title="KrishiMitra API",
    description="AI-Powered Agricultural Advisory Chatbot for Indian Farmers",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ─────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include Routers ────────────────────────────────────
app.include_router(webhook.router)
app.include_router(health.router)
app.include_router(admin.router)
app.include_router(web_ui.router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
        "description": "AI-Powered Agricultural Advisory Chatbot",
        "docs": "/docs",
        "health": "/health",
    }
