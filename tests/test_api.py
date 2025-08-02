import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test that health endpoint returns correct response"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Medical Price Comparator" in data["message"]

class TestProviderEndpoints:
    """Test provider-related endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_providers_fallback(self, client: AsyncClient):
        """Test getting providers returns fallback data when database fails"""
        # Mock the Provider.find_all to raise an exception
        with patch('backend.app.api.providers.Provider.find_all') as mock_find:
            mock_find.return_value.to_list = AsyncMock(side_effect=Exception("Database error"))
            
            response = await client.get("/api/v1/providers/")
            
            assert response.status_code == 200
            data = response.json()
            assert "providers" in data
            assert data["source"] == "fallback"
            assert len(data["providers"]) == 4  # Default providers
    
    @pytest.mark.asyncio
    async def test_get_providers_default(self, client: AsyncClient):
        """Test getting providers returns default when none exist"""
        # Mock the Provider.find_all to return empty list
        with patch('backend.app.api.providers.Provider.find_all') as mock_find:
            mock_find.return_value.to_list = AsyncMock(return_value=[])
            
            response = await client.get("/api/v1/providers/")
            
            assert response.status_code == 200
            data = response.json()
            assert "providers" in data
            assert data["source"] == "default"
            assert len(data["providers"]) == 4  # Default providers
            
            # Check structure of default providers
            provider = data["providers"][0]
            assert "name" in provider
            assert "slug" in provider
            assert "website" in provider

class TestAnalysisEndpoints:
    """Test analysis-related endpoints"""
    
    @pytest.mark.asyncio
    async def test_search_analyses_empty(self, client: AsyncClient):
        """Test searching analyses when none exist"""
        # Mock the search to return empty results
        with patch('backend.app.api.analyses.MedicalAnalysis.find') as mock_find:
            mock_find.return_value.limit.return_value.to_list = AsyncMock(return_value=[])
            
            response = await client.get("/api/v1/analyses/search?query=test")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_search_analyses_invalid_limit(self, client: AsyncClient):
        """Test searching analyses with invalid limit"""
        response = await client.get("/api/v1/analyses/search?query=test&limit=0")
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio  
    async def test_search_analyses_large_limit(self, client: AsyncClient):
        """Test searching analyses with limit too large"""
        response = await client.get("/api/v1/analyses/search?query=test&limit=999")
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_compare_prices_empty_request(self, client: AsyncClient):
        """Test price comparison with empty analysis names"""
        response = await client.post("/api/v1/analyses/compare", json={
            "analysis_names": []
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_compare_prices_invalid_json(self, client: AsyncClient):
        """Test price comparison with invalid JSON"""
        response = await client.post(
            "/api/v1/analyses/compare",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self, client: AsyncClient):
        """Test calling non-existent endpoint"""
        response = await client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_method_not_allowed(self, client: AsyncClient):
        """Test calling endpoint with wrong HTTP method"""
        response = await client.post("/health")
        
        assert response.status_code == 405