from fastapi import APIRouter, HTTPException
from typing import List

from ..config import app_logger
from ..models import Provider

router = APIRouter()


@router.get("/")
async def list_providers():
    """List all healthcare providers"""
    app_logger.info("Retrieving list of healthcare providers")
    
    try:
        providers = await Provider.find_all().to_list()
        app_logger.debug(f"Found {len(providers)} providers in database")
        
        if not providers:
            app_logger.info("No providers found in database, returning default providers")
            # Return default providers when database is empty
            default_providers = [
                {"name": "Regina Maria", "slug": "reginamaria", "website": "https://www.reginamaria.ro"},
                {"name": "Medlife", "slug": "medlife", "website": "https://www.medlife.ro"},
                {"name": "Synevo", "slug": "synevo", "website": "https://www.synevo.ro"},
                {"name": "Medicover", "slug": "medicover", "website": "https://www.medicover.ro"}
            ]
            return {"providers": default_providers, "source": "default"}
        
        app_logger.info(f"Successfully retrieved {len(providers)} providers from database")
        return {"providers": providers, "source": "database"}
    except Exception as e:
        app_logger.error(f"Error retrieving providers: {e}")
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
    provider = await Provider.find_one(Provider.slug == provider_slug)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return provider


@router.post("/")
async def create_provider(provider: Provider):
    """Create a new healthcare provider"""
    # Check if provider with same slug already exists
    existing = await Provider.find_one(Provider.slug == provider.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Provider with this slug already exists")
    
    created_provider = await provider.create()
    return created_provider


# Initialize default providers
async def initialize_default_providers():
    """Initialize default Romanian healthcare providers"""
    try:
        default_providers_data = [
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
        
        for provider_data in default_providers_data:
            existing = await Provider.find_one(Provider.slug == provider_data["slug"])
            if not existing:
                provider = Provider(**provider_data)
                await provider.create()
    except Exception as e:
        print(f"Error initializing providers: {e}")