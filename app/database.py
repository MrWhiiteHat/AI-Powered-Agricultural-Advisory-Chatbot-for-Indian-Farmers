"""
MongoDB connection manager using Motor (async driver).
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class Database:
    """Async MongoDB connection manager."""

    client: AsyncIOMotorClient = None  # type: ignore
    db: AsyncIOMotorDatabase = None  # type: ignore

    @classmethod
    async def connect(cls):
        """Establish MongoDB connection."""
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=50,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000,
            )
            cls.db = cls.client[settings.MONGODB_DB_NAME]
            # Verify connection
            await cls.client.admin.command("ping")
            logger.info(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise

    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("🔌 MongoDB connection closed")

    @classmethod
    def get_collection(cls, name: str):
        """Get a MongoDB collection."""
        if cls.db is None:
            return None
        return cls.db[name]


# ── Collection accessors ─────────────────────────────────
def get_farmers_collection():
    return Database.get_collection("farmers")


def get_conversations_collection():
    return Database.get_collection("conversations")


def get_disease_logs_collection():
    return Database.get_collection("disease_logs")
