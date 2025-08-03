import os
from pydantic_settings import BaseSettings
from loguru import logger
import sys

class Settings(BaseSettings):
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "medical_price_comparator"
    
    # Application
    debug: bool = False
    testing: bool = False
    log_level: str = "INFO"
    
    # File upload limits
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # AI/OCR Settings
    openai_api_key: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()

def setup_logging():
    """Configure logging for the application"""
    # Remove default logger
    logger.remove()
    
    # Add console logger with proper formatting
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file logger for production
    if not settings.testing:
        logger.add(
            "logs/app.log",
            rotation="10 MB",
            retention="1 week",
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            compression="zip"
        )
    
    return logger

# Initialize logging
app_logger = setup_logging()