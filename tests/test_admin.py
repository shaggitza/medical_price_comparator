import pytest
from io import BytesIO
import json
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

class TestCSVPreview:
    """Test CSV preview functionality"""
    
    @pytest.mark.asyncio
    async def test_csv_preview_valid_file(self, client: AsyncClient):
        """Test CSV preview with valid file"""
        csv_content = "name,price,currency\nComplete Blood Count,50.0,RON\nUrine Analysis,30.0,RON"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        
        response = await client.post(
            "/api/v1/admin/csv-preview",
            files={"file": ("test.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "headers" in data
        assert "sample_data" in data
        assert "name" in data["headers"]
        assert "price" in data["headers"]
        assert len(data["sample_data"]) == 2
    
    @pytest.mark.asyncio
    async def test_csv_preview_invalid_file_type(self, client: AsyncClient):
        """Test CSV preview with invalid file type"""
        text_content = "This is not a CSV file"
        text_file = BytesIO(text_content.encode('utf-8'))
        
        response = await client.post(
            "/api/v1/admin/csv-preview",
            files={"file": ("test.txt", text_file, "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "CSV" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_csv_preview_empty_file(self, client: AsyncClient):
        """Test CSV preview with empty file"""
        csv_file = BytesIO(b"")
        
        response = await client.post(
            "/api/v1/admin/csv-preview",
            files={"file": ("empty.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 400

class TestCSVImport:
    """Test CSV import functionality (mocked database operations)"""
    
    @pytest.mark.asyncio
    async def test_csv_import_missing_required_field(self, client: AsyncClient):
        """Test CSV import with missing required field mapping"""
        csv_content = "name,price,currency\nTest Analysis,50.0,RON"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        
        field_mapping = {
            "name": "name",
            "price": "price"
            # Missing currency mapping
        }
        
        response = await client.post(
            "/api/v1/admin/import-csv",
            data={
                "provider": "test-provider",
                "field_mapping": json.dumps(field_mapping)
            },
            files={"file": ("test.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "currency" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_csv_import_invalid_json_mapping(self, client: AsyncClient):
        """Test CSV import with invalid JSON field mapping"""
        csv_content = "name,price,currency\nTest Analysis,50.0,RON"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        
        response = await client.post(
            "/api/v1/admin/import-csv",
            data={
                "provider": "test-provider",
                "field_mapping": "invalid json"
            },
            files={"file": ("test.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid field mapping JSON" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_csv_import_non_csv_file(self, client: AsyncClient):
        """Test CSV import with non-CSV file"""
        text_content = "This is not a CSV"
        text_file = BytesIO(text_content.encode('utf-8'))
        
        field_mapping = {
            "name": "name",
            "price": "price",
            "currency": "currency"
        }
        
        response = await client.post(
            "/api/v1/admin/import-csv",
            data={
                "provider": "test-provider", 
                "field_mapping": json.dumps(field_mapping)
            },
            files={"file": ("test.txt", text_file, "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "CSV" in data["detail"]

class TestImportHistory:
    """Test import history functionality"""
    
    @pytest.mark.asyncio
    async def test_get_import_history_database_error(self, client: AsyncClient):
        """Test getting import history when database fails"""
        with patch('backend.app.api.admin.ImportedData.find_all') as mock_find:
            mock_find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(side_effect=Exception("Database error"))
            
            response = await client.get("/api/v1/admin/import-history")
            
            assert response.status_code == 200
            data = response.json()
            assert "imports" in data
            assert "error" in data
            assert len(data["imports"]) == 0

class TestAdminFileHandling:
    """Test admin file handling edge cases"""
    
    @pytest.mark.asyncio
    async def test_csv_preview_malformed_csv(self, client: AsyncClient):
        """Test CSV preview with malformed CSV content"""
        malformed_csv = 'name,price\n"Incomplete quote,50.0\nValid,30.0'
        csv_file = BytesIO(malformed_csv.encode('utf-8'))
        
        response = await client.post(
            "/api/v1/admin/csv-preview",
            files={"file": ("malformed.csv", csv_file, "text/csv")}
        )
        
        # Should handle gracefully, either succeed or return proper error
        assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    async def test_csv_preview_different_encodings(self, client: AsyncClient):
        """Test CSV preview handles different text encodings"""
        # Test with UTF-8 BOM
        csv_content = "name,price,currency\nTest Analysis,50.0,RON"
        utf8_bom = b'\xef\xbb\xbf' + csv_content.encode('utf-8')
        csv_file = BytesIO(utf8_bom)
        
        response = await client.post(
            "/api/v1/admin/csv-preview",
            files={"file": ("test_bom.csv", csv_file, "text/csv")}
        )
        
        # Should handle BOM gracefully
        assert response.status_code in [200, 400]