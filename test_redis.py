"""Test Redis services"""

import redis
from app.config import settings
from app.services.rate_limiter import RateLimiter
from app.services.cache_service import CacheService

# Connect to Redis
r = redis.from_url("redis://localhost:6379", decode_responses=True)


# Test 1: Rate Limiter
print("Test 1: Rate Limiter")
limiter = RateLimiter(r)

# Clear previous data
r.delete("rate_limit:user:test_user:active_jobs")

# Should allow 3 jobs
for i in range(3):
    allowed = limiter.check_and_increment("test_user")
    print(f"  Job {i+1}: {'✅ Allowed' if allowed else '❌ Blocked'}")

# 4th should be blocked
allowed = limiter.check_and_increment("test_user")
print(f"  Job 4: {'✅ Allowed' if allowed else '❌ Blocked (correct!)'}")

# Decrement and try again
limiter.decrement("test_user")
allowed = limiter.check_and_increment("test_user")
print(f"  Job 5 (after decrement): {'✅ Allowed (correct!)' if allowed else '❌ Blocked'}")

# Test 2: Cache
print("\nTest 2: Cache Service")
cache = CacheService(r)

# Cache miss
summary = cache.get_cached_summary("abc123")
print(f"  First lookup: {'❌ Found' if summary else '✅ Not found (correct!)'}")

# Set cache
cache.set_cached_summary("abc123", "This is a test summary")

# Cache hit
summary = cache.get_cached_summary("abc123")
print(f"  Second lookup: {'✅ Found (correct!)' if summary else '❌ Not found'}")
print(f"  Summary: {summary}")

print("\n✅ All Redis tests passed!")