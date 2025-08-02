from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import re
from beanie import PydanticObjectId

from ..config import app_logger
from ..models import AnalysisQuery, MedicalAnalysis

router = APIRouter()


@router.get("/search")
async def search_analyses(
    query: str = Query(..., description="Search term for analysis names"),
    limit: int = Query(20, description="Maximum number of results")
):
    """Search for medical analyses by name"""
    app_logger.info(f"Searching analyses with query: '{query}', limit: {limit}")
    
    if limit <= 0 or limit > 100:
        app_logger.warning(f"Invalid limit requested: {limit}")
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 100")
    
    try:
        # Create case-insensitive regex pattern
        pattern = re.compile(query, re.IGNORECASE)
        app_logger.debug(f"Using regex pattern: {pattern.pattern}")
        
        # Search in name and alternative_names fields using Beanie
        results = await MedicalAnalysis.find({
            "$or": [
                {"name": {"$regex": pattern}},
                {"alternative_names": {"$regex": pattern}}
            ]
        }).limit(limit).to_list()
        
        app_logger.info(f"Found {len(results)} analyses matching query '{query}'")
        
        if not results:
            app_logger.debug("No results found, returning empty list")
            # Return sample data when no results found
            sample_analyses = [
                {"name": "Hemoglobina", "category": "blood", "alternative_names": ["Hb", "Hemoglobin"], "found": False},
                {"name": "Glicemia", "category": "blood", "alternative_names": ["Glucoza", "Glucose"], "found": False},
                {"name": "Colesterol", "category": "blood", "alternative_names": ["Cholesterol"], "found": False}
            ]
            
            # Filter sample data based on query
            filtered = [a for a in sample_analyses if query.lower() in a["name"].lower()]
            return {"results": filtered[:limit], "total": len(filtered), "source": "sample"}
        
        return {"results": results, "total": len(results), "source": "database"}
        
    except Exception as e:
        # Return sample data on error
        sample_analyses = [
            {"name": "Hemoglobina", "category": "blood", "alternative_names": ["Hb", "Hemoglobin"], "found": False},
            {"name": "Glicemia", "category": "blood", "alternative_names": ["Glucoza", "Glucose"], "found": False},
        ]
        filtered = [a for a in sample_analyses if query.lower() in a["name"].lower()]
        return {"results": filtered[:limit], "total": len(filtered), "source": "error", "error": str(e)}


@router.post("/compare")
async def compare_analyses(query: AnalysisQuery):
    """Compare prices for multiple analyses across providers"""
    results = []
    
    try:
        for analysis_name in query.analysis_names:
            # Try exact match first, then partial match using Beanie
            pattern = re.compile(analysis_name.strip(), re.IGNORECASE)
            
            analysis = await MedicalAnalysis.find_one({
                "$or": [
                    {"name": {"$regex": pattern}},
                    {"alternative_names": {"$regex": pattern}}
                ]
            })
            
            if analysis:
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
                "error": str(e)
            }
            results.append(sample_result)
        
        return {"results": results, "query": query, "source": "error", "error": str(e)}


@router.get("/categories")
async def get_categories():
    """Get all available analysis categories"""
    try:
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        categories = []
        async for doc in MedicalAnalysis.get_motor_collection().aggregate(pipeline):
            categories.append({
                "category": doc["_id"],
                "count": doc["count"]
            })
        
        return {"categories": categories}
    except Exception as e:
        return {"categories": [], "error": str(e)}


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get detailed information for a specific analysis"""
    try:
        analysis = await MedicalAnalysis.get(PydanticObjectId(analysis_id))
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid analysis ID: {str(e)}")


@router.get("/")
async def list_analyses(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """List all medical analyses with optional filtering"""
    try:
        query_filter = {}
        if category:
            query_filter["category"] = category
        
        results = await MedicalAnalysis.find(query_filter).skip(skip).limit(limit).to_list()
        
        # Get total count
        total = await MedicalAnalysis.find(query_filter).count()
        
        return {
            "results": results,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        return {
            "results": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "error": str(e)
        }