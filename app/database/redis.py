"""
Redis connection management for caching and rate limiting.
Provides sync Redis client (operations are fast enough).
"""

import redis
from typing import Optional
from loguru import logger
from app.config import settings


class RedisClient:
    """Redis connection manager"""
    
    client: Optional[redis.Redis] = None
    
    @classmethod
    def connect(cls):
        """
        Establish connection to Redis.
        Called during FastAPI startup event.
        """
        try:
            logger.info(f"Connecting to Redis at {settings.redis_url}")
            
            # Create Redis client
            cls.client = redis.from_url(
                settings.redis_url,
                decode_responses=True,  # Return strings instead of bytes
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            cls.client.ping()
            
            logger.info("Successfully connected to Redis")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    @classmethod
    def disconnect(cls):
        """
        Close Redis connection.
        Called during FastAPI shutdown event.
        """
        if cls.client:
            logger.info("Closing Redis connection")
            cls.client.close()
            cls.client = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        Get Redis client instance.
        Used in dependency injection.
        """
        if cls.client is None:
            raise RuntimeError("Redis not initialized. Call connect() first.")
        return cls.client


# Convenience function for dependency injection
def get_redis() -> redis.Redis:
    """
    FastAPI dependency to get Redis client.
    
    Usage in routes:
        @app.post("/documents")
        async def create_document(
            doc: Document,
            redis_client: redis.Redis = Depends(get_redis)
        ):
            # Use redis_client for rate limiting
    """
    return RedisClient.get_client()