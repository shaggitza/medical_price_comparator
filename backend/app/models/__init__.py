from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from beanie import Document, Indexed
from bson import ObjectId


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


class MedicalAnalysis(Document):
    name: Indexed(str) = Field(..., description="Standardized analysis name")
    alternative_names: List[str] = Field(default_factory=list, description="Alternative names and variations")
    category: Indexed(str) = Field(..., description="Medical category (e.g., blood, urine, imaging)")
    description: Optional[str] = None
    prices: Dict[str, Dict] = Field(default_factory=dict, description="Prices by provider")

    class Settings:
        name = "medical_analyses"


class Provider(Document):
    name: Indexed(str)
    slug: Indexed(str, unique=True) = Field(..., description="e.g., 'reginamaria', 'medlife'")
    logo_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    contact_info: Optional[Dict] = None

    class Settings:
        name = "providers"


class ImportedData(Document):
    filename: str
    import_date: str
    provider: str
    total_records: int
    successful_imports: int
    errors: List[Dict] = Field(default_factory=list)

    class Settings:
        name = "import_history"


class OCRRequest(BaseModel):
    image_data: str  # base64 encoded image
    provider_context: Optional[str] = None


class AnalysisQuery(BaseModel):
    analysis_names: List[str]
    provider_filter: Optional[List[str]] = None
    price_type: Optional[str] = None  # normal, premium, etc.


class OCRRequest(BaseModel):
    image_data: str  # base64 encoded image
    provider_context: Optional[str] = None


class AnalysisQuery(BaseModel):
    analysis_names: List[str]
    provider_filter: Optional[List[str]] = None
    price_type: Optional[str] = None  # normal, premium, etc.