from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import re

from ..database import get_database
from ..models import AnalysisQuery, MedicalAnalysis

router = APIRouter()


@router.get("/search")
async def search_analyses(
    query: str = Query(..., description="Search term for analysis names"),
    limit: int = Query(20, description="Maximum number of results")
):
    """Search for medical analyses by name"""
    db = get_database()
    
    if db is None:
        # Return sample data when database is not available
        sample_analyses = [
            {"name": "Hemoglobina", "category": "blood", "alternative_names": ["Hb", "Hemoglobin"], "found": False},
            {"name": "Glicemia", "category": "blood", "alternative_names": ["Glucoza", "Glucose"], "found": False},
            {"name": "Colesterol", "category": "blood", "alternative_names": ["Cholesterol"], "found": False}
        ]
        
        # Filter sample data based on query
        filtered = [a for a in sample_analyses if query.lower() in a["name"].lower()]
        return {"results": filtered[:limit], "total": len(filtered), "source": "sample"}
    
    try:
        # Create case-insensitive regex pattern
        import re
        pattern = re.compile(query, re.IGNORECASE)
        
        # Search in name and alternative_names fields
        cursor = db.medical_analyses.find({
            "$or": [
                {"name": {"$regex": pattern}},
                {"alternative_names": {"$regex": pattern}}
            ]
        }).limit(limit)
        
        results = []
        async for doc in cursor:
            analysis = MedicalAnalysis(**doc)
            results.append(analysis)
        
        return {"results": results, "total": len(results), "source": "database"}
        
    except Exception as e:
        # Return empty results on error
        return {"results": [], "total": 0, "source": "error", "error": str(e)}


@router.post("/compare")
async def compare_analyses(query: AnalysisQuery):
    """Compare prices for multiple analyses across providers"""
    db = get_database()
    
    results = []
    
    if db is None:
        # Return sample data when database is not available
        for analysis_name in query.analysis_names:
            sample_result = {
                "name": analysis_name,
                "alternative_names": [],
                "category": "unknown",
                "prices": {
                    "reginamaria": {
                        "normal": {"amount": 15.0, "currency": "RON"},
                        "premium": {"amount": 12.0, "currency": "RON"}
                    },
                    "medlife": {
                        "normal": {"amount": 14.0, "currency": "RON"},
                        "premium": {"amount": 0.0, "currency": "RON"}
                    }
                },
                "found": False,
                "source": "sample"
            }
            results.append(sample_result)
        
        return {"results": results, "query": query, "source": "sample"}
    
    try:
        for analysis_name in query.analysis_names:
            # Try exact match first, then partial match
            import re
            pattern = re.compile(analysis_name.strip(), re.IGNORECASE)
            
            doc = await db.medical_analyses.find_one({
                "$or": [
                    {"name": {"$regex": pattern}},
                    {"alternative_names": {"$regex": pattern}}
                ]
            })
            
            if doc:
                analysis = MedicalAnalysis(**doc)
                
                # Filter by provider if specified
                if query.provider_filter:
                    filtered_prices = {}
                    for provider in query.provider_filter:
                        if provider in analysis.prices:
                            filtered_prices[provider] = analysis.prices[provider]
                    analysis.prices = filtered_prices
                
                results.append(analysis)
            else:
                # Create a placeholder for missing analysis
                results.append({
                    "name": analysis_name,
                    "alternative_names": [],
                    "category": "unknown",
                    "prices": {},
                    "found": False
                })
        
        return {"results": results, "query": query, "source": "database"}
        
    except Exception as e:
        # Return sample data on error
        for analysis_name in query.analysis_names:
            sample_result = {
                "name": analysis_name,
                "alternative_names": [],
                "category": "unknown",
                "prices": {},
                "found": False,
                "error": str(e)
            }
            results.append(sample_result)
        
        return {"results": results, "query": query, "source": "error", "error": str(e)}


@router.get("/categories")
async def get_categories():
    """Get all available analysis categories"""
    db = get_database()
    
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    categories = []
    async for doc in db.medical_analyses.aggregate(pipeline):
        categories.append({
            "category": doc["_id"],
            "count": doc["count"]
        })
    
    return {"categories": categories}


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get detailed information for a specific analysis"""
    db = get_database()
    
    from bson import ObjectId
    try:
        doc = await db.medical_analyses.find_one({"_id": ObjectId(analysis_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return MedicalAnalysis(**doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid analysis ID: {str(e)}")


@router.get("/")
async def list_analyses(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """List all medical analyses with optional filtering"""
    db = get_database()
    
    query_filter = {}
    if category:
        query_filter["category"] = category
    
    cursor = db.medical_analyses.find(query_filter).skip(skip).limit(limit)
    
    results = []
    async for doc in cursor:
        analysis = MedicalAnalysis(**doc)
        results.append(analysis)
    
    # Get total count
    total = await db.medical_analyses.count_documents(query_filter)
    
    return {
        "results": results,
        "total": total,
        "skip": skip,
        "limit": limit
    }