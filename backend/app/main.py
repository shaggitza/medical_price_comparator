from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from .config import settings, app_logger
from .database import connect_to_mongo, close_mongo_connection
from .api import analyses, providers, admin, ocr


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        app_logger.info("Starting Medical Price Comparator API...")
        await connect_to_mongo()
        
        # Initialize default data
        from .services.init_data import initialize_app_data
        await initialize_app_data()
        app_logger.info("Connected to MongoDB successfully")
    except Exception as e:
        app_logger.warning(f"Could not connect to MongoDB: {e}")
        app_logger.info("Application will run in limited mode without database features")
    
    yield
    
    # Shutdown
    try:
        await close_mongo_connection()
        app_logger.info("Application shutdown complete")
    except Exception as e:
        app_logger.warning(f"Warning during shutdown: {e}")


app = FastAPI(
    title="Medical Price Comparator",
    description="A medical analysis price comparator for Romania with AI integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(analyses.router, prefix="/api/v1/analyses", tags=["analyses"])
app.include_router(providers.router, prefix="/api/v1/providers", tags=["providers"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["ocr"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    app_logger.debug("Health check requested")
    return {"status": "healthy", "message": "Medical Price Comparator API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)