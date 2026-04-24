"""
Content-based caching service using Redis.
Caches document summaries by content hash.
"""

import redis
import json
from typing import Optional
from loguru import logger
from app.config import settings


class CacheService:
    """Cache for document summaries"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = settings.redis_cache_ttl
    
    def _get_key(self, content_hash: str) -> str:
        """Generate Redis key for cached summary"""
        return f"cache:summary:{content_hash}"
    
    def get_cached_summary(self, content_hash: str) -> Optional[str]:
        """
        Get cached summary by content hash.
        
        Returns:
            Summary text if cached, None if not found
        """
        key = self._get_key(content_hash)
        
        try:
            cached = self.redis.get(key)
            if cached:
                logger.info(f"Cache HIT for content_hash: {content_hash[:16]}...")
                return cached
            else:
                logger.info(f"Cache MISS for content_hash: {content_hash[:16]}...")
                return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set_cached_summary(self, content_hash: str, summary: str):
        """
        Cache a summary with TTL.
        
        Args:
            content_hash: SHA-256 hash of content
            summary: Generated summary text
        """
        key = self._get_key(content_hash)
        
        try:
            self.redis.setex(key, self.ttl, summary)
            logger.info(f"Cached summary for content_hash: {content_hash[:16]}... (TTL: {self.ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    def invalidate_cache(self, content_hash: str):
        """Delete cached summary"""
        key = self._get_key(content_hash)
        
        try:
            self.redis.delete(key)
            logger.info(f"Invalidated cache for content_hash: {content_hash[:16]}...")
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")