import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional

from .models import MedicalAnalysis, Provider, ImportedData

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection and initialize Beanie ODM"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:password123@localhost:27017/medical_comparator?authSource=admin")
    db.client = AsyncIOMotorClient(mongodb_url)
    db.database = db.client.medical_comparator
    
    # Initialize Beanie ODM with document models
    await init_beanie(
        database=db.database,
        document_models=[
            MedicalAnalysis,
            Provider,
            ImportedData,
        ]
    )

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()

def get_database():
    return db.database