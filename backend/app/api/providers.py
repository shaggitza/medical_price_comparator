from fastapi import APIRouter, HTTPException
from typing import List

from ..database import get_database
from ..models import Provider

router = APIRouter()


@router.get("/")
async def list_providers():
    """List all healthcare providers"""
    db = get_database()
    
    if db is None:
        # Return default providers when database is not available
        default_providers = [
            {"name": "Regina Maria", "slug": "reginamaria", "website": "https://www.reginamaria.ro"},
            {"name": "Medlife", "slug": "medlife", "website": "https://www.medlife.ro"},
            {"name": "Synevo", "slug": "synevo", "website": "https://www.synevo.ro"},
            {"name": "Medicover", "slug": "medicover", "website": "https://www.medicover.ro"}
        ]
        return {"providers": default_providers, "source": "default"}
    
    try:
        cursor = db.providers.find({})
        
        results = []
        async for doc in cursor:
            provider = Provider(**doc)
            results.append(provider)
        
        return {"providers": results, "source": "database"}
    except Exception as e:
        # Fallback to default providers on error
        default_providers = [
            {"name": "Regina Maria", "slug": "reginamaria", "website": "https://www.reginamaria.ro"},
            {"name": "Medlife", "slug": "medlife", "website": "https://www.medlife.ro"},
            {"name": "Synevo", "slug": "synevo", "website": "https://www.synevo.ro"},
            {"name": "Medicover", "slug": "medicover", "website": "https://www.medicover.ro"}
        ]
        return {"providers": default_providers, "source": "fallback", "error": str(e)}


@router.get("/{provider_slug}")
async def get_provider(provider_slug: str):
    """Get detailed information for a specific provider"""
    db = get_database()
    
    doc = await db.providers.find_one({"slug": provider_slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return Provider(**doc)


@router.post("/")
async def create_provider(provider: Provider):
    """Create a new healthcare provider"""
    db = get_database()
    
    # Check if provider with same slug already exists
    existing = await db.providers.find_one({"slug": provider.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Provider with this slug already exists")
    
    result = await db.providers.insert_one(provider.dict(by_alias=True, exclude={"id"}))
    provider.id = result.inserted_id
    
    return provider


# Initialize default providers
async def initialize_default_providers():
    """Initialize default Romanian healthcare providers"""
    db = get_database()
    
    if db is None:
        return  # Cannot initialize without database
    
    try:
        default_providers = [
            {
                "name": "Regina Maria",
                "slug": "reginamaria",
                "logo_url": "https://www.reginamaria.ro/themes/custom/regina_maria/logo.svg",
                "website": "https://www.reginamaria.ro",
                "location": "Romania",
                "contact_info": {"phone": "021 9467", "email": "contact@reginamaria.ro"}
            },
            {
                "name": "Medlife",
                "slug": "medlife",
                "logo_url": "https://www.medlife.ro/images/logo.png",
                "website": "https://www.medlife.ro",
                "location": "Romania",
                "contact_info": {"phone": "021 9736", "email": "contact@medlife.ro"}
            },
            {
                "name": "Synevo",
                "slug": "synevo",
                "logo_url": "https://www.synevo.ro/images/logo.png",
                "website": "https://www.synevo.ro",
                "location": "Romania",
                "contact_info": {"phone": "021 9717", "email": "contact@synevo.ro"}
            },
            {
                "name": "Medicover",
                "slug": "medicover",
                "logo_url": "https://www.medicover.ro/images/logo.png",
                "website": "https://www.medicover.ro",
                "location": "Romania",
                "contact_info": {"phone": "021 9999", "email": "contact@medicover.ro"}
            }
        ]
        
        for provider_data in default_providers:
            existing = await db.providers.find_one({"slug": provider_data["slug"]})
            if not existing:
                await db.providers.insert_one(provider_data)
    except Exception as e:
        print(f"Error initializing providers: {e}")