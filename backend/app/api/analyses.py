from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import re
from beanie import PydanticObjectId

from ..config import app_logger
from ..models import AnalysisQuery, MedicalAnalysis

router = APIRouter()


@router.get("/suggestions")
async def get_suggestions(
    query: str = Query(..., description="Search term for analysis suggestions"),
    limit: int = Query(10, description="Maximum number of suggestions")
):
    """Get search suggestions for medical analyses with fuzzy matching"""
    app_logger.info(f"Getting suggestions for query: '{query}', limit: {limit}")
    
    if limit <= 0 or limit > 20:
        app_logger.warning(f"Invalid limit requested: {limit}")
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 20")
    
    if len(query.strip()) < 2:
        return {"suggestions": []}
    
    try:
        query_clean = query.strip().lower()
        
        # First try exact and prefix matches
        exact_pattern = re.compile(f"^{re.escape(query_clean)}", re.IGNORECASE)
        contains_pattern = re.compile(re.escape(query_clean), re.IGNORECASE)
        
        # Search in name and alternative_names fields
        exact_results = await MedicalAnalysis.find({
            "$or": [
                {"name": {"$regex": exact_pattern}},
                {"alternative_names": {"$regex": exact_pattern}}
            ]
        }).limit(limit).to_list()
        
        contains_results = await MedicalAnalysis.find({
            "$or": [
                {"name": {"$regex": contains_pattern}},
                {"alternative_names": {"$regex": contains_pattern}}
            ]
        }).limit(limit).to_list()
        
        # Combine results, giving priority to exact matches
        all_results = []
        seen_names = set()
        
        for analysis in exact_results:
            if analysis.name not in seen_names:
                all_results.append(analysis)
                seen_names.add(analysis.name)
        
        for analysis in contains_results:
            if analysis.name not in seen_names and len(all_results) < limit:
                all_results.append(analysis)
                seen_names.add(analysis.name)
        
        # If still no results or very few, try fuzzy matching with sample data
        if len(all_results) < 3:
            fuzzy_suggestions = get_fuzzy_suggestions(query_clean, limit - len(all_results))
            all_results.extend(fuzzy_suggestions)
        
        # Convert to simple suggestion format
        suggestions = []
        for analysis in all_results:
            if hasattr(analysis, 'name'):  # Database result
                suggestions.append({
                    "name": analysis.name,
                    "category": analysis.category,
                    "alternative_names": analysis.alternative_names or []
                })
            else:  # Sample/fuzzy result
                suggestions.append(analysis)
        
        app_logger.info(f"Found {len(suggestions)} suggestions for query '{query}'")
        return {"suggestions": suggestions[:limit]}
        
    except Exception as e:
        app_logger.error(f"Error getting suggestions: {e}")
        # Fallback to fuzzy suggestions on error
        try:
            fuzzy_suggestions = get_fuzzy_suggestions(query.strip().lower(), limit)
            return {"suggestions": fuzzy_suggestions}
        except:
            return {"suggestions": [], "error": str(e)}


def get_fuzzy_suggestions(query: str, limit: int):
    """Generate fuzzy suggestions for medical analyses, including typo-tolerant matches"""
    # Extended list of common Romanian medical analyses with variations
    sample_analyses = [
        {"name": "Hemoglobina", "category": "Hematologie", "alternative_names": ["Hb", "Hemoglobin"]},
        {"name": "Hematocrit", "category": "Hematologie", "alternative_names": ["Ht", "HCT"]},
        {"name": "Leucocite", "category": "Hematologie", "alternative_names": ["WBC", "Globule albe"]},
        {"name": "Trombocite", "category": "Hematologie", "alternative_names": ["PLT", "Plachetele"]},
        {"name": "Eritrocite", "category": "Hematologie", "alternative_names": ["RBC", "Globule rosii"]},
        {"name": "Glicemia", "category": "Biochimie", "alternative_names": ["Glucoza", "Glucose", "Glicemie"]},
        {"name": "Colesterol", "category": "Biochimie", "alternative_names": ["Cholesterol", "Colesterolul"]},
        {"name": "Colesterol HDL", "category": "Biochimie", "alternative_names": ["HDL", "Colesterol bun"]},
        {"name": "Colesterol LDL", "category": "Biochimie", "alternative_names": ["LDL", "Colesterol rau"]},
        {"name": "Trigliceride", "category": "Biochimie", "alternative_names": ["TG", "Trigliceridele"]},
        {"name": "Creatinina", "category": "Biochimie", "alternative_names": ["Creatinine", "Creat"]},
        {"name": "Urea", "category": "Biochimie", "alternative_names": ["BUN", "Azot urea"]},
        {"name": "Acid uric", "category": "Biochimie", "alternative_names": ["Uric acid", "Acidul uric"]},
        {"name": "Bilirubina totala", "category": "Biochimie", "alternative_names": ["Bilirubina", "TBIL"]},
        {"name": "Bilirubina directa", "category": "Biochimie", "alternative_names": ["Bilirubina conjugata", "DBIL"]},
        {"name": "AST", "category": "Biochimie", "alternative_names": ["ASAT", "Aspartat aminotransferaza"]},
        {"name": "ALT", "category": "Biochimie", "alternative_names": ["ALAT", "Alanin aminotransferaza"]},
        {"name": "Fosfataza alcalina", "category": "Biochimie", "alternative_names": ["ALP", "FA"]},
        {"name": "GGT", "category": "Biochimie", "alternative_names": ["Gamma GT", "Gamma glutamil transferaza"]},
        {"name": "Proteine totale", "category": "Biochimie", "alternative_names": ["Total proteins", "TP"]},
        {"name": "Albumina", "category": "Biochimie", "alternative_names": ["Albumin", "ALB"]},
        {"name": "Fierul seric", "category": "Biochimie", "alternative_names": ["Fe", "Iron", "Fier"]},
        {"name": "Feritina", "category": "Biochimie", "alternative_names": ["Ferritin", "Feritina serica"]},
        {"name": "Transferina", "category": "Biochimie", "alternative_names": ["Transferrin", "TIBC"]},
        {"name": "Vitamina B12", "category": "Vitamine", "alternative_names": ["B12", "Cobalamina"]},
        {"name": "Vitamina D", "category": "Vitamine", "alternative_names": ["25-OH Vitamina D", "Vit D"]},
        {"name": "Acid folic", "category": "Vitamine", "alternative_names": ["Folati", "Vitamina B9"]},
        {"name": "TSH", "category": "Endocrinologie", "alternative_names": ["Tirotropina", "Thyroid stimulating hormone"]},
        {"name": "T4 liber", "category": "Endocrinologie", "alternative_names": ["FT4", "Tiroxina libera"]},
        {"name": "T3 liber", "category": "Endocrinologie", "alternative_names": ["FT3", "Triiodotironina libera"]},
        {"name": "Prolactina", "category": "Endocrinologie", "alternative_names": ["PRL", "Prolactin"]},
        {"name": "Testosteron", "category": "Endocrinologie", "alternative_names": ["Testosteron total", "T"]},
        {"name": "Estradiol", "category": "Endocrinologie", "alternative_names": ["E2", "Estrogen"]},
        {"name": "Cortizol", "category": "Endocrinologie", "alternative_names": ["Cortisol", "Hidrocortizon"]},
        {"name": "Insulina", "category": "Endocrinologie", "alternative_names": ["Insulin", "INS"]},
        {"name": "HbA1c", "category": "Endocrinologie", "alternative_names": ["Hemoglobina glicata", "Hemoglobina glicosilata"]},
        {"name": "PCR", "category": "Inflamatii", "alternative_names": ["CRP", "Proteina C reactiva"]},
        {"name": "VSH", "category": "Inflamatii", "alternative_names": ["ESR", "Viteza de sedimentare"]},
        {"name": "Fibrinogen", "category": "Coagulare", "alternative_names": ["Fibrinogenul", "FIB"]},
        {"name": "INR", "category": "Coagulare", "alternative_names": ["Raport normalizat international"]},
        {"name": "PTT", "category": "Coagulare", "alternative_names": ["aPTT", "Timpul de tromboplastina partiala"]},
        {"name": "Examen urinar", "category": "Urologie", "alternative_names": ["Sumarul de urina", "Urina completa"]},
        {"name": "Urocultura", "category": "Urologie", "alternative_names": ["Cultura urina", "Urine culture"]},
        {"name": "Microalbumina", "category": "Urologie", "alternative_names": ["Albumina urinara", "MAU"]},
        {"name": "PSA", "category": "Urologie", "alternative_names": ["Antigen prostatic specific"]},
        {"name": "Beta hCG", "category": "Ginecologie", "alternative_names": ["hCG", "Gonadotrofina corionica"]},
        {"name": "CA 15-3", "category": "Markeri tumorali", "alternative_names": ["Marker tumoral san"]},
        {"name": "CA 125", "category": "Markeri tumorali", "alternative_names": ["Marker tumoral ovar"]},
        {"name": "CEA", "category": "Markeri tumorali", "alternative_names": ["Antigen carcinoembrionar"]},
        {"name": "AFP", "category": "Markeri tumorali", "alternative_names": ["Alfa-fetoproteina"]},
    ]
    
    # Calculate similarity scores and find matches
    matches = []
    query_lower = query.lower()
    
    for analysis in sample_analyses:
        score = 0
        
        # Check main name
        name_lower = analysis["name"].lower()
        if query_lower in name_lower:
            score += 10
        elif name_lower.startswith(query_lower):
            score += 8
        elif any(word.startswith(query_lower) for word in name_lower.split()):
            score += 6
        elif calculate_similarity(query_lower, name_lower) > 0.6:
            score += 4
        
        # Check alternative names
        for alt_name in analysis["alternative_names"]:
            alt_lower = alt_name.lower()
            if query_lower in alt_lower:
                score += 8
            elif alt_lower.startswith(query_lower):
                score += 6
            elif calculate_similarity(query_lower, alt_lower) > 0.6:
                score += 3
        
        # Check if query is a common typo or abbreviation
        if is_common_typo(query_lower, name_lower) or is_common_typo(query_lower, analysis["alternative_names"]):
            score += 5
        
        if score > 0:
            matches.append((score, analysis))
    
    # Sort by score and return top matches
    matches.sort(key=lambda x: x[0], reverse=True)
    return [match[1] for match in matches[:limit]]


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings using simple character-based matching"""
    if not str1 or not str2:
        return 0.0
    
    # Convert to sets of characters for simple overlap calculation
    set1 = set(str1.lower())
    set2 = set(str2.lower())
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def is_common_typo(query: str, targets) -> bool:
    """Check if query might be a common typo of any target"""
    if isinstance(targets, str):
        targets = [targets]
    
    # Common typo patterns for Romanian medical terms
    typo_patterns = {
        'hemo': ['hemoglobina', 'hematocrit'],
        'hema': ['hematocrit', 'hemoglobina'],
        'glice': ['glicemia', 'glicemie'],
        'gluco': ['glucoza', 'glicemia'],
        'cole': ['colesterol'],
        'chol': ['colesterol'],
        'creat': ['creatinina'],
        'uric': ['acid uric'],
        'bili': ['bilirubina'],
        'tsh': ['tirotropina'],
        't4': ['tiroxina'],
        't3': ['triiodotironina'],
        'vita': ['vitamina'],
        'vit': ['vitamina'],
    }
    
    for pattern, matches in typo_patterns.items():
        if query.startswith(pattern):
            for target in targets:
                if isinstance(target, str) and any(match in target.lower() for match in matches):
                    return True
    
    return False


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