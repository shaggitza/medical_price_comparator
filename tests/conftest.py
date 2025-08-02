import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from backend.app.main import app
from backend.app.config import settings

# Configure test settings
settings.testing = True
settings.log_level = "ERROR"  # Reduce log noise during tests

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def client():
    """Create test client with mocked database"""
    # Mock database operations to avoid needing real database
    with patch('backend.app.database.connect_to_mongo', new_callable=AsyncMock), \
         patch('backend.app.database.close_mongo_connection', new_callable=AsyncMock):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

@pytest.fixture
def sample_provider_data():
    """Sample provider data for testing"""
    return {
        "name": "Test Hospital",
        "slug": "test-hospital",
        "website": "https://test.com",
        "location": "Bucharest"
    }

@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing"""
    return {
        "name": "Complete Blood Count",
        "alternative_names": ["CBC", "Full Blood Count"],
        "category": "blood",
        "description": "Basic blood test",
        "prices": {
            "test-hospital": {
                "normal": {"amount": 50.0, "currency": "RON"}
            }
        }
    }