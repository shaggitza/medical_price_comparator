from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Dict, Any
import csv
import io
import json
import os
from datetime import datetime

from ..config import app_logger, settings
from ..models import MedicalAnalysis, PriceInfo, ProviderPrices, ImportedData

router = APIRouter()


@router.post("/import-csv")
async def import_csv_data(
    file: UploadFile = File(...),
    provider: str = Form(...),
    field_mapping: str = Form(...)
):
    """Import medical analysis data from CSV file"""
    app_logger.info(f"Starting CSV import for provider: {provider}, file: {file.filename}")
    
    if not file.filename.endswith('.csv'):
        app_logger.warning(f"Invalid file type for import: {file.filename}")
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Parse field mapping
        mapping = json.loads(field_mapping)
        app_logger.debug(f"Field mapping: {mapping}")
        required_fields = ['name', 'price', 'currency']
        
        for field in required_fields:
            if field not in mapping:
                app_logger.error(f"Missing required field mapping: {field}")
                raise HTTPException(status_code=400, detail=f"Missing required field mapping: {field}")
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        imported_count = 0
        errors = []
        total_records = 0
        
        for row_num, row in enumerate(csv_reader, 1):
            total_records += 1
            
            try:
                # Extract data based on mapping
                analysis_name = row.get(mapping['name'], '').strip()
                price_str = row.get(mapping['price'], '0').strip()
                currency = row.get(mapping.get('currency', 'currency'), 'RON').strip()
                
                if not analysis_name:
                    errors.append(f"Row {row_num}: Missing analysis name")
                    continue
                
                # Convert price to float
                try:
                    price = float(price_str.replace(',', '.'))
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid price format: {price_str}")
                    continue
                
                # Get optional fields
                category = row.get(mapping.get('category', ''), 'general')
                price_type = row.get(mapping.get('price_type', ''), 'normal')
                description = row.get(mapping.get('description', ''), '')
                alternative_names = []
                
                if 'alternative_names' in mapping:
                    alt_names_str = row.get(mapping['alternative_names'], '')
                    if alt_names_str:
                        alternative_names = [name.strip() for name in alt_names_str.split(';') if name.strip()]
                
                # Check if analysis already exists using Beanie
                existing = await MedicalAnalysis.find_one(MedicalAnalysis.name == analysis_name)
                
                if existing:
                    # Update existing analysis with new price
                    price_info = PriceInfo(amount=price, currency=currency)
                    
                    # Update the prices dictionary
                    if provider not in existing.prices:
                        existing.prices[provider] = {}
                    existing.prices[provider][price_type] = price_info.dict()
                    
                    await existing.save()
                else:
                    # Create new analysis using Beanie
                    price_info = PriceInfo(amount=price, currency=currency)
                    provider_prices = ProviderPrices()
                    setattr(provider_prices, price_type, price_info)
                    
                    new_analysis = MedicalAnalysis(
                        name=analysis_name,
                        alternative_names=alternative_names,
                        category=category,
                        description=description if description else None,
                        prices={provider: provider_prices.dict()}
                    )
                    
                    await new_analysis.create()
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        # Save import log using Beanie
        import_log = ImportedData(
            filename=file.filename,
            import_date=datetime.now().isoformat(),
            provider=provider,
            total_records=total_records,
            successful_imports=imported_count,
            errors=errors
        )
        
        await import_log.create()
        
        return {
            "message": "Import completed",
            "total_records": total_records,
            "successful_imports": imported_count,
            "errors": len(errors),
            "error_details": errors[:10]  # Return first 10 errors
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid field mapping JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/import-history")
async def get_import_history():
    """Get history of data imports"""
    try:
        imports = await ImportedData.find_all().sort("-import_date").limit(50).to_list()
        return {"imports": imports}
    except Exception as e:
        return {"imports": [], "error": str(e)}


@router.post("/csv-preview")
async def preview_csv_structure(file: UploadFile = File(...)):
    """Preview CSV structure to help with field mapping"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Limit file size to 10MB to prevent memory issues
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        # Try different encodings to handle various file formats
        csv_content = None
        for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
            try:
                csv_content = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if csv_content is None:
            raise HTTPException(status_code=400, detail="Unable to decode file. Please ensure it's a valid CSV with UTF-8 encoding")
        
        # Limit preview to first 1000 characters to avoid processing huge files
        preview_content = csv_content[:1000] if len(csv_content) > 1000 else csv_content
        
        # Read first few rows with safety limits
        csv_reader = csv.DictReader(io.StringIO(preview_content))
        
        # Get field names
        fieldnames = csv_reader.fieldnames
        
        if not fieldnames:
            raise HTTPException(status_code=400, detail="No headers found in CSV file")
        
        # Get first 3 rows as sample with safety counter
        sample_rows = []
        row_count = 0
        for row in csv_reader:
            if row_count >= 3:  # Limit to 3 sample rows
                break
            sample_rows.append(row)
            row_count += 1
        
        return {
            "fieldnames": fieldnames,
            "sample_rows": sample_rows,
            "suggested_mapping": {
                "name": "name" if "name" in fieldnames else fieldnames[0] if fieldnames else "",
                "price": "price" if "price" in fieldnames else fieldnames[1] if len(fieldnames) > 1 else "",
                "currency": "currency" if "currency" in fieldnames else "",
                "category": "category" if "category" in fieldnames else "",
                "price_type": "price_type" if "price_type" in fieldnames else ""
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")


@router.delete("/clear-data")
async def clear_all_data(confirm: str = ""):
    """Clear all analysis data (use with caution)"""
    if confirm != "DELETE_ALL_DATA":
        raise HTTPException(status_code=400, detail="Must provide confirmation")
    
    try:
        # Delete all analyses using Beanie
        result = await MedicalAnalysis.delete_all()
        return {"message": f"Deleted all analyses"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing data: {str(e)}")


@router.post("/load-sample-data/{provider}")
async def load_sample_data(provider: str):
    """Load sample data for a specific provider into the database"""
    app_logger.info(f"Loading sample data for provider: {provider}")
    
    # Validate provider
    if provider not in ["reginamaria", "medlife"]:
        raise HTTPException(status_code=400, detail="Invalid provider. Must be 'reginamaria' or 'medlife'")
    
    try:
        # Use the smart data path resolution from config
        data_dir = settings.resolved_data_path
        csv_file_path = data_dir / f"sample_analyses_{provider}.csv"
        
        app_logger.info(f"Data path resolution: resolved to {data_dir}")
        app_logger.debug(f"Looking for sample CSV at: {csv_file_path}")
        app_logger.debug(f"Data directory exists: {data_dir.exists()}")
        
        if not csv_file_path.exists():
            app_logger.warning(f"Sample data file not found: {csv_file_path}")
            
            if data_dir.exists():
                try:
                    available_files = [f.name for f in data_dir.iterdir() if f.is_file()]
                    app_logger.warning(f"Available files in data directory {data_dir}: {available_files}")
                except Exception as e:
                    app_logger.warning(f"Could not list files in data directory: {e}")
            else:
                app_logger.warning(f"Data directory {data_dir} does not exist")
                # Debug path resolution
                from pathlib import Path
                app_logger.debug(f"Checking Docker path /app/data: exists={Path('/app/data').exists()}")
                app_logger.debug(f"Current file location: {Path(__file__).parent}")
                
            raise HTTPException(status_code=404, detail=f"Sample data file not found for provider {provider}")
        
        # Read and parse the CSV file
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_content = file.read()
        
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        imported_count = 0
        errors = []
        total_records = 0
        
        for row_num, row in enumerate(csv_reader, 1):
            total_records += 1
            
            try:
                # Extract data from CSV row
                analysis_name = row.get('name', '').strip()
                price_str = row.get('price', '0').strip()
                currency = row.get('currency', 'RON').strip()
                category = row.get('category', 'general').strip()
                price_type = row.get('price_type', 'normal').strip()
                description = row.get('description', '').strip()
                alternative_names_str = row.get('alternative_names', '')
                
                if not analysis_name:
                    errors.append(f"Row {row_num}: Missing analysis name")
                    continue
                
                # Convert price to float
                try:
                    price = float(price_str.replace(',', '.'))
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid price format: {price_str}")
                    continue
                
                # Parse alternative names
                alternative_names = []
                if alternative_names_str:
                    alternative_names = [name.strip() for name in alternative_names_str.split(';') if name.strip()]
                
                # Check if analysis already exists
                existing = await MedicalAnalysis.find_one(MedicalAnalysis.name == analysis_name)
                
                if existing:
                    # Update existing analysis with new price
                    price_info = PriceInfo(amount=price, currency=currency)
                    
                    # Update the prices dictionary
                    if provider not in existing.prices:
                        existing.prices[provider] = {}
                    existing.prices[provider][price_type] = price_info.dict()
                    
                    await existing.save()
                    app_logger.debug(f"Updated existing analysis: {analysis_name} with {price_type} price for {provider}")
                else:
                    # Create new analysis
                    price_info = PriceInfo(amount=price, currency=currency)
                    
                    new_analysis = MedicalAnalysis(
                        name=analysis_name,
                        alternative_names=alternative_names,
                        category=category,
                        description=description if description else None,
                        prices={provider: {price_type: price_info.dict()}}
                    )
                    
                    await new_analysis.create()
                    app_logger.debug(f"Created new analysis: {analysis_name} with {price_type} price for {provider}")
                
                imported_count += 1
                
            except Exception as e:
                error_msg = f"Row {row_num}: {str(e)}"
                errors.append(error_msg)
                app_logger.warning(error_msg)
        
        # Save import log
        import_log = ImportedData(
            filename=f"sample_analyses_{provider}.csv",
            import_date=datetime.now().isoformat(),
            provider=provider,
            total_records=total_records,
            successful_imports=imported_count,
            errors=[{"message": error, "row": i+1} for i, error in enumerate(errors)]
        )
        
        await import_log.create()
        
        app_logger.info(f"Sample data load completed for {provider}: {imported_count}/{total_records} records imported")
        
        return {
            "message": f"Sample data loaded successfully for {provider}",
            "provider": provider,
            "total_records": total_records,
            "successful_imports": imported_count,
            "errors": len(errors),
            "error_details": errors[:5] if errors else []  # Return first 5 errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error loading sample data for {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load sample data: {str(e)}")