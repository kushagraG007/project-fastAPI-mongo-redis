"""
Centralized logging configuration
"""

import sys
from loguru import logger
from app.config import settings


def setup_logging():
    """Configure structured logging with loguru"""
    logger.remove()
    
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    logger.info(f"Logging configured: level={settings.log_level}")


def get_logger():
    """Get configured logger instance"""
    return logger