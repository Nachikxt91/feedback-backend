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
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                retryWrites=True,
                w="majority"
            )
            
            await self.client.admin.command('ping')
            self.db = self.client[settings.MONGODB_DB_NAME]
            
            await self._create_indexes()
            
            logger.info(f"Successfully connected to MongoDB database: {self.db.name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def _create_indexes(self):
        """Create necessary database indexes for multi-tenant architecture"""
        # Companies collection
        companies = self.db.companies
        await companies.create_index("email", unique=True, name="email_unique_idx")
        await companies.create_index("slug", unique=True, name="slug_unique_idx")
        await companies.create_index("api_key", unique=True, name="api_key_unique_idx")
        
        # Feedbacks collection (tenant-scoped)
        feedbacks = self.db.feedbacks
        await feedbacks.create_index(
            [("company_id", 1), ("created_at", -1)],
            name="company_created_idx"
        )
        await feedbacks.create_index(
            [("company_id", 1), ("sentiment", 1)],
            name="company_sentiment_idx"
        )
        await feedbacks.create_index(
            [("company_id", 1), ("processed", 1)],
            name="company_processed_idx"
        )
        await feedbacks.create_index("created_at", name="created_at_idx")
        
        logger.info("Database indexes created for multi-tenant architecture")

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