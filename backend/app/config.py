import os
from pathlib import Path
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
    
    # Data directory path - configurable for different environments
    data_path: str = ""
    
    @property
    def resolved_data_path(self) -> Path:
        """Resolve the data path based on environment"""
        if self.data_path:
            # Use explicitly configured path
            return Path(self.data_path)
        
        # Auto-detect data path based on environment
        docker_path = Path("/app/data")
        if docker_path.exists():
            # Running in Docker container
            return docker_path
        
        # Running locally - find data directory relative to project root
        current_path = Path(__file__).parent
        while current_path.parent != current_path:  # Stop at filesystem root
            data_dir = current_path / "data"
            if data_dir.exists() and data_dir.is_dir():
                return data_dir
            current_path = current_path.parent
        
        # Fallback to relative path from backend directory
        backend_parent = Path(__file__).parent.parent.parent
        return backend_parent / "data"
    
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