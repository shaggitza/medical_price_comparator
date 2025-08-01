from fastapi import APIRouter, UploadFile, File, HTTPException
import base64
import io
from PIL import Image
import pytesseract
import re
from typing import List
import os

router = APIRouter()


@router.post("/process")
async def process_ocr_image(image: UploadFile = File(...)):
    """Process uploaded image with OCR to extract medical analysis names"""
    
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Open image with PIL
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Perform OCR with Romanian language support
        ocr_text = pytesseract.image_to_string(pil_image, lang='ron+eng')
        
        # Extract medical analysis names using pattern matching
        analyses = extract_medical_analyses(ocr_text)
        
        return {
            "raw_text": ocr_text,
            "analyses": analyses,
            "found_count": len(analyses)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


def extract_medical_analyses(text: str) -> List[str]:
    """Extract medical analysis names from OCR text using pattern matching"""
    
    # Common Romanian medical analysis patterns
    medical_patterns = [
        # Blood tests
        r'\b(?:hemoglobin[a|ă]|Hb)\b',
        r'\b(?:glicemi[ea]|glucoz[a|ă])\b',
        r'\b(?:colesterol)\b',
        r'\b(?:trigliceride)\b',
        r'\b(?:creatinin[a|ă])\b',
        r'\b(?:ure[ea])\b',
        r'\b(?:acid uric)\b',
        r'\b(?:bilirubina?)\b',
        r'\b(?:transaminaze|ALT|AST)\b',
        r'\b(?:fosfataza? alcalin[a|ă])\b',
        r'\b(?:proteine totale)\b',
        r'\b(?:albumin[a|ă])\b',
        r'\b(?:fierul seric)\b',
        r'\b(?:feritina?)\b',
        r'\b(?:transferina?)\b',
        r'\b(?:vitamina? [A-Z]\d*)\b',
        r'\b(?:homocistein[a|ă])\b',
        r'\b(?:PCR|proteina? C reactiv[a|ă])\b',
        r'\b(?:VSH|viteza de sedimentare)\b',
        r'\b(?:TSH|tirotropin[a|ă])\b',
        r'\b(?:T3|T4|triiodotironin[a|ă]|tiroxin[a|ă])\b',
        r'\b(?:prolactin[a|ă])\b',
        r'\b(?:testosteron)\b',
        r'\b(?:estradiol)\b',
        r'\b(?:cortizol)\b',
        r'\b(?:insulin[a|ă])\b',
        r'\b(?:HbA1c|hemoglobin[a|ă] glicat[a|ă])\b',
        
        # Lipid profile
        r'\b(?:profil lipidic)\b',
        r'\b(?:HDL|LDL)\b',
        
        # Complete blood count
        r'\b(?:hemoleucogram[a|ă]?|CBC|hematii?)\b',
        r'\b(?:leucocite)\b',
        r'\b(?:trombocite)\b',
        r'\b(?:hematocrit)\b',
        
        # Liver function
        r'\b(?:functii? hepatice?)\b',
        r'\b(?:gamma ?GT|GGT)\b',
        
        # Kidney function
        r'\b(?:functii? renale?)\b',
        r'\b(?:clearance creatinin[a|ă])\b',
        
        # Hormones
        r'\b(?:FSH|LH|hormoni? foliculostimulant)\b',
        r'\b(?:progester[o|a]n[a|ă]?)\b',
        
        # Infections
        r'\b(?:hepatit[a|ă] [A-C]|HBsAg|anti.?HCV)\b',
        r'\b(?:HIV|VDRL|sifilis)\b',
        
        # Urine tests
        r'\b(?:examen urin[a|ă]|sediment urinar)\b',
        r'\b(?:urocultur[a|ă])\b',
        
        # Specific tests with numbers/values
        r'\b\w+\s*[-:]\s*\d+[\.,]?\d*\s*(?:mg/dl|g/dl|UI/L|mUI/L|ng/ml|pg/ml|mmol/L)\b',
    ]
    
    analyses = []
    text_lower = text.lower()
    
    # Extract using patterns
    for pattern in medical_patterns:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            analysis = match.group().strip()
            if analysis and len(analysis) > 2:
                # Clean up the analysis name
                analysis = clean_analysis_name(analysis)
                if analysis and analysis not in analyses:
                    analyses.append(analysis)
    
    # Also look for lines that might contain analysis names
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line and is_likely_analysis_line(line):
            clean_line = clean_analysis_name(line)
            if clean_line and clean_line not in analyses and len(clean_line) > 3:
                analyses.append(clean_line)
    
    return analyses[:20]  # Limit to first 20 findings


def clean_analysis_name(text: str) -> str:
    """Clean and normalize analysis name"""
    # Remove common prefixes and suffixes
    text = re.sub(r'^[-•\*\d\.\)\s]+', '', text)
    text = re.sub(r'[:\-\=]+.*$', '', text)
    text = re.sub(r'\s*\([^)]*\)\s*', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Capitalize properly
    if text:
        text = text.lower().title()
        # Fix some Romanian specific capitalizations
        text = re.sub(r'\bDe\b', 'de', text)
        text = re.sub(r'\bLa\b', 'la', text)
        text = re.sub(r'\bUn\b', 'un', text)
    
    return text


def is_likely_analysis_line(line: str) -> bool:
    """Determine if a line likely contains a medical analysis name"""
    line = line.strip().lower()
    
    # Skip if too short or too long
    if len(line) < 3 or len(line) > 100:
        return False
    
    # Skip lines with too many numbers
    if len(re.findall(r'\d', line)) > len(line) * 0.3:
        return False
    
    # Skip pure numeric lines
    if re.match(r'^[\d\s\.\,\-\+\(\)]+$', line):
        return False
    
    # Skip common headers/footers
    skip_patterns = [
        r'pacient', r'doctor', r'medic', r'data', r'ora', r'spital',
        r'clinica', r'laborator', r'rezultat', r'valori', r'normale',
        r'referinta', r'unitate', r'metoda', r'pagina', r'total'
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, line):
            return False
    
    # Positive indicators
    positive_patterns = [
        r'\b(?:acid|proteina?|vitamina?|hormon|enzima?|marker)\b',
        r'\b(?:seric|ular|ic|ina?|oza?|emia?)\b',
        r'\b(?:total|liber|legat)\b'
    ]
    
    for pattern in positive_patterns:
        if re.search(pattern, line):
            return True
    
    # Default: accept if it looks like a medical term
    return bool(re.search(r'[a-z]{4,}', line))


@router.post("/extract-text")
async def extract_text_only(image: UploadFile = File(...)):
    """Extract raw text from image without analysis detection"""
    
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        ocr_text = pytesseract.image_to_string(pil_image, lang='ron+eng')
        
        return {"text": ocr_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")