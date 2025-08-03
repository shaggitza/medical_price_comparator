import pytest
from backend.app.models import PriceInfo, ProviderPrices

class TestPydanticModels:
    """Test Pydantic models"""
    
    def test_price_info_model(self):
        """Test PriceInfo model"""
        price = PriceInfo(
            amount=75.5,
            currency="RON",
            promotional_price=60.0,
            promotion_description="Holiday discount"
        )
        
        assert price.amount == 75.5
        assert price.currency == "RON"
        assert price.promotional_price == 60.0
        assert price.promotion_description == "Holiday discount"
    
    def test_price_info_default_currency(self):
        """Test PriceInfo with default currency"""
        price = PriceInfo(amount=100.0)
        assert price.currency == "RON"  # Default value
        assert price.promotional_price is None
    
    def test_provider_prices_model(self):
        """Test ProviderPrices model"""
        prices = ProviderPrices(
            normal=PriceInfo(amount=100.0, currency="RON"),
            premium=PriceInfo(amount=80.0, currency="RON"),
            subscription=PriceInfo(amount=50.0, currency="RON")
        )
        
        assert prices.normal.amount == 100.0
        assert prices.premium.amount == 80.0
        assert prices.subscription.amount == 50.0
        assert prices.premium_standard is None  # Not set

class TestModelValidation:
    """Test model validation"""
    
    def test_price_info_negative_amount(self):
        """Test PriceInfo with negative amount should work"""
        # Negative amounts might be valid for discounts
        price = PriceInfo(amount=-10.0, currency="RON")
        assert price.amount == -10.0
    
    def test_price_info_zero_amount(self):
        """Test PriceInfo with zero amount"""
        price = PriceInfo(amount=0.0, currency="RON")
        assert price.amount == 0.0
    
    def test_price_info_invalid_currency_still_works(self):
        """Test PriceInfo with any currency string"""
        # Model doesn't enforce currency validation
        price = PriceInfo(amount=100.0, currency="INVALID")
        assert price.currency == "INVALID"