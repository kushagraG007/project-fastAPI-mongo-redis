"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.config import settings
from app.database.mongodb import MongoDB
from app.database.redis import RedisClient
from app.routers import documents_router

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level
)

# Create FastAPI application
app = FastAPI(
    title="Document Insights API",
    description="Asynchronous document processing service with rate limiting and caching",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("=" * 60)
    logger.info("Starting Document Insights API")
    logger.info(f"MongoDB: {settings.mongodb_url}")
    logger.info(f"Redis: {settings.redis_url}")
    logger.info("=" * 60)
    
    await MongoDB.connect()
    RedisClient.connect()
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Shutting down Document Insights API")
    
    await MongoDB.disconnect()
    RedisClient.disconnect()
    
    logger.info("Application shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = MongoDB.get_database()
        await db.command('ping')
        mongodb_status = "connected"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")
        mongodb_status = "disconnected"
    
    try:
        redis_client = RedisClient.get_client()
        redis_client.ping()
        redis_status = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_status = "disconnected"
    
    is_healthy = mongodb_status == "connected" and redis_status == "connected"
    
    return JSONResponse(
        status_code=200 if is_healthy else 503,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "services": {
                "mongodb": mongodb_status,
                "redis": redis_status
            }
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Document Insights API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Register routers
app.include_router(documents_router)