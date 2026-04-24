"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file with type validation.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or .env file.
    """
    
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "document_insights"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 3600  # 1 hour in seconds
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Application Settings
    log_level: str = "INFO"
    max_active_jobs_per_user: int = 3
    
    # Worker Configuration
    worker_poll_interval: int = 2  # seconds
    worker_min_process_time: int = 10  # seconds
    worker_max_process_time: int = 30  # seconds
    worker_failure_rate: float = 0.1  # 10% failure rate
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # MONGODB_URL or mongodb_url both work


# Global settings instance
settings = Settings()