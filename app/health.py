"""
Enhanced health check with service status details
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
from loguru import logger

from app.database.mongodb import MongoDB
from app.database.redis import RedisClient

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Comprehensive health check.
    
    Checks:
    - API status
    - MongoDB connection
    - Redis connection
    - Response times
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check MongoDB
    mongodb_start = datetime.utcnow()
    try:
        db = MongoDB.get_database()
        await db.command('ping')
        mongodb_time = (datetime.utcnow() - mongodb_start).total_seconds()
        health_status["services"]["mongodb"] = {
            "status": "connected",
            "response_time_ms": round(mongodb_time * 1000, 2)
        }
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["services"]["mongodb"] = {
            "status": "disconnected",
            "error": str(e)
        }
    
    # Check Redis
    redis_start = datetime.utcnow()
    try:
        redis_client = RedisClient.get_client()
        redis_client.ping()
        redis_time = (datetime.utcnow() - redis_start).total_seconds()
        health_status["services"]["redis"] = {
            "status": "connected",
            "response_time_ms": round(redis_time * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["services"]["redis"] = {
            "status": "disconnected",
            "error": str(e)
        }
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes-style readiness probe.
    Returns 200 only if all services are ready.
    """
    try:
        db = MongoDB.get_database()
        await db.command('ping')
        
        redis_client = RedisClient.get_client()
        redis_client.ping()
        
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    Returns 200 if API process is alive.
    """
    return {"status": "alive"}