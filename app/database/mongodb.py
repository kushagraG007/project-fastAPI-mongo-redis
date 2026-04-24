"""
MongoDB connection management using Motor (async driver).
Provides async database client for FastAPI endpoints.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from loguru import logger
from app.config import settings


class MongoDB:
    """MongoDB connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls):
        """
        Establish connection to MongoDB.
        Called during FastAPI startup event.
        """
        try:
            logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
            
            # Create async MongoDB client
            cls.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            
            # Get database reference
            cls.database = cls.client[settings.mongodb_db_name]
            
            # Test connection
            await cls.client.admin.command('ping')
            
            logger.info(f"Successfully connected to MongoDB database: {settings.mongodb_db_name}")
            
            # Create indexes
            await cls.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    @classmethod
    async def create_indexes(cls):
        """
        Create database indexes for better query performance.
        
        Indexes created:
        - user_id + status (for listing user documents with status filter)
        - content_hash (for cache lookup)
        - created_at (for sorting)
        """
        try:
            documents_collection = cls.database.documents
            
            # Compound index for user queries with status filter
            await documents_collection.create_index(
                [("user_id", 1), ("status", 1)],
                name="user_id_status_idx"
            )
            
            # Index for content-based caching
            await documents_collection.create_index(
                "content_hash",
                name="content_hash_idx",
                unique=False
            )
            
            # Index for sorting by creation time
            await documents_collection.create_index(
                "created_at",
                name="created_at_idx"
            )
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create indexes: {str(e)}")
    
    @classmethod
    async def disconnect(cls):
        """
        Close MongoDB connection.
        Called during FastAPI shutdown event.
        """
        if cls.client:
            logger.info("Closing MongoDB connection")
            cls.client.close()
            cls.client = None
            cls.database = None
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get database instance.
        Used in dependency injection.
        """
        if cls.database is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return cls.database


# Convenience function for dependency injection
async def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency to get database instance.
    
    Usage in routes:
        @app.get("/documents/{id}")
        async def get_document(id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
            doc = await db.documents.find_one({"_id": ObjectId(id)})
    """
    return MongoDB.get_database()