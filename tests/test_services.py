"""
Unit tests for service layer.
"""

import pytest
from app.services.rate_limiter import RateLimiter
from app.services.cache_service import CacheService


def test_rate_limiter_allows_within_limit(test_redis):
    """Test rate limiter allows requests within limit"""
    limiter = RateLimiter(test_redis)
    
    # Should allow 3 jobs
    assert limiter.check_and_increment("user_test") == True
    assert limiter.check_and_increment("user_test") == True
    assert limiter.check_and_increment("user_test") == True


def test_rate_limiter_blocks_over_limit(test_redis):
    """Test rate limiter blocks 4th request"""
    limiter = RateLimiter(test_redis)
    
    # Fill up the limit
    limiter.check_and_increment("user_test")
    limiter.check_and_increment("user_test")
    limiter.check_and_increment("user_test")
    
    # 4th should be blocked
    assert limiter.check_and_increment("user_test") == False


def test_rate_limiter_decrement(test_redis):
    """Test rate limiter decrement frees up slot"""
    limiter = RateLimiter(test_redis)
    
    # Fill limit
    limiter.check_and_increment("user_test")
    limiter.check_and_increment("user_test")
    limiter.check_and_increment("user_test")
    
    # Should be blocked
    assert limiter.check_and_increment("user_test") == False
    
    # Decrement
    limiter.decrement("user_test")
    
    # Should now be allowed
    assert limiter.check_and_increment("user_test") == True


def test_rate_limiter_different_users(test_redis):
    """Test rate limiter is per-user"""
    limiter = RateLimiter(test_redis)
    
    # User 1 fills limit
    limiter.check_and_increment("user_1")
    limiter.check_and_increment("user_1")
    limiter.check_and_increment("user_1")
    
    # User 2 should still be allowed
    assert limiter.check_and_increment("user_2") == True


def test_cache_miss(test_redis):
    """Test cache returns None on miss"""
    cache = CacheService(test_redis)
    
    result = cache.get_cached_summary("nonexistent_hash")
    assert result is None


def test_cache_hit(test_redis):
    """Test cache returns value on hit"""
    cache = CacheService(test_redis)
    
    # Set cache
    cache.set_cached_summary("test_hash", "Test summary")
    
    # Get cache
    result = cache.get_cached_summary("test_hash")
    assert result == "Test summary"


def test_cache_different_hashes(test_redis):
    """Test cache stores different hashes separately"""
    cache = CacheService(test_redis)
    
    cache.set_cached_summary("hash1", "Summary 1")
    cache.set_cached_summary("hash2", "Summary 2")
    
    assert cache.get_cached_summary("hash1") == "Summary 1"
    assert cache.get_cached_summary("hash2") == "Summary 2"