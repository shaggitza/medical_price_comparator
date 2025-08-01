from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class MedicalAnalysis(BaseModel):
    name: str = Field(..., description="Standardized analysis name")
    alternative_names: List[str] = Field(default_factory=list, description="Alternative names and variations")
    category: str = Field(..., description="Medical category (e.g., blood, urine, imaging)")
    description: Optional[str] = None
    prices: Dict[str, Dict] = Field(default_factory=dict, description="Prices by provider")


class PriceInfo(BaseModel):
    amount: float
    currency: str = "RON"
    promotional_price: Optional[float] = None
    promotion_description: Optional[str] = None


class ProviderPrices(BaseModel):
    normal: Optional[PriceInfo] = None
    premium: Optional[PriceInfo] = None
    premium_standard: Optional[PriceInfo] = None
    subscription: Optional[PriceInfo] = None


class Provider(BaseModel):
    name: str
    slug: str  # e.g., "reginamaria", "medlife"
    logo_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    contact_info: Optional[Dict] = None


class ImportedData(BaseModel):
    filename: str
    import_date: str
    provider: str
    total_records: int
    successful_imports: int
    errors: List[Dict] = Field(default_factory=list)


class OCRRequest(BaseModel):
    image_data: str  # base64 encoded image
    provider_context: Optional[str] = None


class AnalysisQuery(BaseModel):
    analysis_names: List[str]
    provider_filter: Optional[List[str]] = None
    price_type: Optional[str] = None  # normal, premium, etc.