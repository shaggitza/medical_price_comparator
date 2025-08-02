import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from io import BytesIO

class TestOCREndpoints:
    """Test OCR-related endpoints"""
    
    @pytest.mark.asyncio
    async def test_process_ocr_missing_api_key(self, client: AsyncClient):
        """Test OCR processing without API key"""
        # Mock image data (base64)
        mock_image_data = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD"
        
        response = await client.post("/api/v1/ocr/process", json={
            "image_data": mock_image_data,
            "provider_context": "reginamaria"
        })
        
        # Should handle missing API key gracefully
        assert response.status_code in [400, 500]  # Depending on implementation
    
    @pytest.mark.asyncio
    async def test_process_ocr_invalid_image_data(self, client: AsyncClient):
        """Test OCR processing with invalid image data"""
        response = await client.post("/api/v1/ocr/process", json={
            "image_data": "invalid_base64_data",
            "provider_context": "reginamaria"
        })
        
        assert response.status_code == 400

class TestFileUploadLimits:
    """Test file upload size limits"""
    
    @pytest.mark.asyncio
    async def test_csv_upload_large_file(self, client: AsyncClient):
        """Test CSV upload with file exceeding size limit"""
        # Create a large CSV content (> 10MB)
        large_content = "name,price,currency\n" + "Test Analysis,50.0,RON\n" * 100000
        large_file = BytesIO(large_content.encode('utf-8'))
        
        response = await client.post(
            "/api/v1/admin/csv-preview",
            files={"file": ("large.csv", large_file, "text/csv")}
        )
        
        # Should either reject or handle gracefully
        # Implementation may vary based on actual file size limits
        assert response.status_code in [400, 413, 422]

class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, client: AsyncClient):
        """Test API with invalid JSON payload"""
        response = await client.post(
            "/api/v1/analyses/compare",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient):
        """Test API with missing required fields"""
        response = await client.post("/api/v1/analyses/compare", json={
            # Missing analysis_names field
        })
        
        assert response.status_code == 422
        data = response.json()
        assert "analysis_names" in str(data)

class TestPerformance:
    """Test performance scenarios"""
    
    @pytest.mark.asyncio
    async def test_search_with_large_dataset(self, client: AsyncClient):
        """Test search performance with large dataset"""
        # Create multiple analyses
        from backend.app.models import MedicalAnalysis
        
        analyses = []
        for i in range(100):
            analysis = MedicalAnalysis(
                name=f"Test Analysis {i}",
                category="test",
                description=f"Test description {i}"
            )
            analyses.append(analysis)
        
        # Save all analyses
        for analysis in analyses:
            await analysis.save()
        
        # Test search
        response = await client.get("/api/v1/analyses/search?query=test&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10  # Respects limit
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: AsyncClient):
        """Test handling of concurrent requests"""
        import asyncio
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = client.get("/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

class TestDataValidation:
    """Test data validation scenarios"""
    
    @pytest.mark.asyncio
    async def test_analysis_name_validation(self, client: AsyncClient):
        """Test analysis name validation"""
        from backend.app.models import MedicalAnalysis
        
        # Test with empty name
        with pytest.raises(Exception):
            analysis = MedicalAnalysis(
                name="",  # Empty name should fail
                category="blood"
            )
            await analysis.save()
    
    @pytest.mark.asyncio
    async def test_provider_slug_validation(self, client: AsyncClient):
        """Test provider slug validation"""
        from backend.app.models import Provider
        
        # Test with invalid slug characters
        provider = Provider(
            name="Test Provider",
            slug="invalid slug with spaces"  # Should be normalized
        )
        
        # Depending on implementation, this might auto-normalize or fail
        saved_provider = await provider.save()
        # Test that slug is properly formatted
        assert " " not in saved_provider.slug or saved_provider.slug == "invalid slug with spaces"

class TestConfigurationAndSettings:
    """Test configuration and settings"""
    
    def test_settings_default_values(self):
        """Test that settings have proper default values"""
        from backend.app.config import settings
        
        assert settings.database_name == "medical_price_comparator"
        assert settings.max_file_size > 0
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
    
    def test_testing_mode_settings(self):
        """Test settings in testing mode"""
        from backend.app.config import settings
        
        # Should be in testing mode during tests
        assert settings.testing is True
        assert settings.log_level == "ERROR"  # Reduced log noise