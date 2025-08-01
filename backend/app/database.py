import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:password123@localhost:27017/medical_comparator?authSource=admin")
    db.client = AsyncIOMotorClient(mongodb_url)
    db.database = db.client.medical_comparator
    
    # Create indexes for efficient querying
    await create_indexes()

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()

async def create_indexes():
    """Create database indexes for efficient querying"""
    if db.database:
        # Index for medical analyses
        await db.database.medical_analyses.create_index("name")
        await db.database.medical_analyses.create_index("alternative_names")
        await db.database.medical_analyses.create_index("category")
        
        # Index for providers
        await db.database.providers.create_index("slug", unique=True)
        await db.database.providers.create_index("name")

def get_database():
    return db.database