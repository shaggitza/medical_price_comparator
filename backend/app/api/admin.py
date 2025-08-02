from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Dict, Any
import csv
import io
import json
from datetime import datetime

from ..database import get_database
from ..models import MedicalAnalysis, PriceInfo, ProviderPrices, ImportedData

router = APIRouter()


@router.post("/import-csv")
async def import_csv_data(
    file: UploadFile = File(...),
    provider: str = Form(...),
    field_mapping: str = Form(...)
):
    """Import medical analysis data from CSV file"""
    db = get_database()
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Parse field mapping
        mapping = json.loads(field_mapping)
        required_fields = ['name', 'price', 'currency']
        
        for field in required_fields:
            if field not in mapping:
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
                
                # Check if analysis already exists
                existing = await db.medical_analyses.find_one({"name": analysis_name})
                
                if existing:
                    # Update existing analysis with new price
                    price_info = PriceInfo(amount=price, currency=currency)
                    
                    update_path = f"prices.{provider}.{price_type}"
                    await db.medical_analyses.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {update_path: price_info.dict()}}
                    )
                else:
                    # Create new analysis
                    price_info = PriceInfo(amount=price, currency=currency)
                    provider_prices = ProviderPrices()
                    setattr(provider_prices, price_type, price_info)
                    
                    new_analysis = MedicalAnalysis(
                        name=analysis_name,
                        alternative_names=alternative_names,
                        category=category,
                        description=description if description else None,
                        prices={provider: provider_prices}
                    )
                    
                    await db.medical_analyses.insert_one(new_analysis.dict(by_alias=True, exclude={"id"}))
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        # Save import log
        import_log = ImportedData(
            filename=file.filename,
            import_date=datetime.now().isoformat(),
            provider=provider,
            total_records=total_records,
            successful_imports=imported_count,
            errors=errors
        )
        
        await db.import_logs.insert_one(import_log.dict(by_alias=True, exclude={"id"}))
        
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
    db = get_database()
    
    cursor = db.import_logs.find({}).sort("import_date", -1).limit(50)
    
    results = []
    async for doc in cursor:
        import_log = ImportedData(**doc)
        results.append(import_log)
    
    return {"imports": results}


@router.post("/csv-preview")
async def preview_csv_structure(file: UploadFile = File(...)):
    """Preview CSV structure to help with field mapping"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Read first few rows
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Get field names
        fieldnames = csv_reader.fieldnames
        
        # Get first 3 rows as sample
        sample_rows = []
        for i, row in enumerate(csv_reader):
            if i >= 3:
                break
            sample_rows.append(row)
        
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
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")


@router.delete("/clear-data")
async def clear_all_data(confirm: str = ""):
    """Clear all analysis data (use with caution)"""
    if confirm != "DELETE_ALL_DATA":
        raise HTTPException(status_code=400, detail="Must provide confirmation")
    
    db = get_database()
    
    # Delete all analyses
    result = await db.medical_analyses.delete_many({})
    
    return {"message": f"Deleted {result.deleted_count} analyses"}