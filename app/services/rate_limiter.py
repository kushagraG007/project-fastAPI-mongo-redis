"""
Rate limiting service using Redis.
Ensures each user has max 3 active jobs (queued + processing).
"""

import redis
from loguru import logger
from app.config import settings


class RateLimiter:
    """Rate limiter for active jobs per user"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.max_jobs = settings.max_active_jobs_per_user
    
    def _get_key(self, user_id: str) -> str:
        """Generate Redis key for user's active job count"""
        return f"rate_limit:user:{user_id}:active_jobs"
    
    def check_and_increment(self, user_id: str) -> bool:
        """
        Check if user can submit a new job and increment counter.
        
        Returns:
            True if allowed (counter incremented)
            False if rate limit exceeded
        """
        key = self._get_key(user_id)
        
        try:
            # Get current count
            current = self.redis.get(key)
            current_count = int(current) if current else 0
            
            # Check limit
            if current_count >= self.max_jobs:
                logger.warning(f"Rate limit exceeded for user {user_id}: {current_count}/{self.max_jobs}")
                return False
            
            # Increment atomically
            new_count = self.redis.incr(key)
            
            # Set expiry if this is first job (safety cleanup)
            if new_count == 1:
                self.redis.expire(key, 86400)  # 24 hours
            
            logger.info(f"Rate limit check passed for user {user_id}: {new_count}/{self.max_jobs}")
            return True
            
        except Exception as e:
            logger.error(f"Rate limiter error: {str(e)}")
            # Fail open - allow request if Redis is down
            return True
    
    def decrement(self, user_id: str):
        """
        Decrement active job count when job completes/fails.
        Called by worker after processing.
        """
        key = self._get_key(user_id)
        
        try:
            current = self.redis.get(key)
            if current and int(current) > 0:
                self.redis.decr(key)
                logger.info(f"Decremented rate limit for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to decrement rate limit: {str(e)}")
    
    def get_current_count(self, user_id: str) -> int:
        """Get current active job count for user"""
        key = self._get_key(user_id)
        try:
            current = self.redis.get(key)
            return int(current) if current else 0
        except Exception as e:
            logger.error(f"Failed to get rate limit count: {str(e)}")
            return 0