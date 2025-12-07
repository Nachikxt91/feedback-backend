from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging
from .config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    async def connect_to_database(self):
        """Connect to MongoDB with retry logic"""
        try:
            # Debug: Show what settings are being used
            print("="*60)
            print("🔍 MONGODB CONNECTION DEBUG")
            print(f"📍 URL: {settings.MONGODB_URL}")
            print(f"📂 Database: {settings.MONGODB_DB_NAME}")
            print("="*60)
            
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                retryWrites=True,
                w="majority"
            )
            # Test connection
            await self.client.admin.command('ping')
            self.db = self.client[settings.MONGODB_DB_NAME]
            
            # Debug: Show actual connection info
            print(f"✅ Successfully connected to MongoDB")
            print(f"✅ Using database: {self.db.name}")
            print(f"✅ Cluster: {self.client.address}")
            print("="*60)
            
            # Create indexes
            await self._create_indexes()
            
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            print(f"❌ FAILED to connect to MongoDB: {e}")
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise


    async def _create_indexes(self):
        """Create necessary database indexes"""
        feedback_collection = self.db.feedbacks
        await feedback_collection.create_index("created_at", name="created_at_idx")
        await feedback_collection.create_index("rating", name="rating_idx")
        logger.info("Database indexes created")

    async def close_database_connection(self):
        """Gracefully close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

db_manager = DatabaseManager()

def get_database() -> AsyncIOMotorDatabase:
    """Dependency for getting database instance"""
    if db_manager.db is None:
        raise RuntimeError("Database not initialized")
    return db_manager.db