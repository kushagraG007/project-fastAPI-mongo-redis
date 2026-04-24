"""
Pytest configuration and fixtures.
Provides reusable test components.
"""

import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import redis
from httpx import AsyncClient
from app.main import app
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """MongoDB test database fixture"""
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[f"{settings.mongodb_db_name}_test"]
    
    yield db
    
    # Cleanup
    await client.drop_database(f"{settings.mongodb_db_name}_test")
    client.close()


@pytest.fixture
def test_redis():
    """Redis test client fixture"""
    client = redis.from_url(settings.redis_url, decode_responses=True)
    
    yield client
    
    # Cleanup - flush test keys
    client.flushdb()
    client.close()


@pytest.fixture
async def client():
    """FastAPI test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac