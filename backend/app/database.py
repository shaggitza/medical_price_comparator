import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional

from .config import settings, app_logger
from .models import MedicalAnalysis, Provider, ImportedData

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection and initialize Beanie ODM"""
    mongodb_url = settings.mongodb_url
    app_logger.info(f"Connecting to MongoDB at {mongodb_url}")
    
    db.client = AsyncIOMotorClient(mongodb_url)
    db.database = db.client[settings.database_name]
    
    # Test connection
    try:
        await db.client.admin.command('ping')
        app_logger.info("Successfully connected to MongoDB")
    except Exception as e:
        app_logger.error(f"Failed to ping MongoDB: {e}")
        raise
    
    # Initialize Beanie ODM with document models
    await init_beanie(
        database=db.database,
        document_models=[
            MedicalAnalysis,
            Provider,
            ImportedData,
        ]
    )
    app_logger.info("Beanie ODM initialized successfully")

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        app_logger.info("Closing MongoDB connection")
        db.client.close()

def get_database():
    return db.database