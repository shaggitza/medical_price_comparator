from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from .database import connect_to_mongo, close_mongo_connection
from .api import analyses, providers, admin, ocr


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await connect_to_mongo()
        
        # Initialize default data
        from .services.init_data import initialize_app_data
        await initialize_app_data()
        print("Connected to MongoDB successfully")
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB: {e}")
        print("Application will run in limited mode without database features")
    
    yield
    
    # Shutdown
    try:
        await close_mongo_connection()
    except Exception as e:
        print(f"Warning during shutdown: {e}")


app = FastAPI(
    title="Medical Price Comparator",
    description="A medical analysis price comparator for Romania with AI integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates (conditional mounting)
import os
static_path = "static"
templates_path = "templates"

if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

if os.path.exists(templates_path):
    templates = Jinja2Templates(directory=templates_path)

# Include API routes
app.include_router(analyses.router, prefix="/api/v1/analyses", tags=["analyses"])
app.include_router(providers.router, prefix="/api/v1/providers", tags=["providers"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["ocr"])


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main application"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Medical Price Comparator</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .search-section { margin-bottom: 30px; }
            .upload-section { margin-bottom: 30px; padding: 20px; border: 2px dashed #ccc; }
            .results-section { margin-top: 30px; }
            input, button { padding: 10px; margin: 5px; }
            button { background: #007bff; color: white; border: none; cursor: pointer; }
            button:hover { background: #0056b3; }
            .price-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            .price-table th, .price-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            .price-table th { background-color: #f2f2f2; position: sticky; top: 0; }
            .loading { display: none; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Medical Price Comparator</h1>
                <p>Compare medical analysis prices across Romanian healthcare providers</p>
            </div>
            
            <div class="upload-section">
                <h3>📋 Upload Doctor's Recommendation (OCR)</h3>
                <input type="file" id="imageFile" accept="image/*">
                <button onclick="processOCR()">Process with AI</button>
                <div id="ocrLoading" class="loading">Processing image...</div>
            </div>
            
            <div class="search-section">
                <h3>🔍 Search Analyses</h3>
                <input type="text" id="searchInput" placeholder="Enter analysis names (comma separated)" style="width: 70%;">
                <button onclick="searchAnalyses()">Search Prices</button>
                <div id="searchLoading" class="loading">Searching...</div>
            </div>
            
            <div class="results-section">
                <div id="results"></div>
            </div>
        </div>
        
        <script>
            async function processOCR() {
                const fileInput = document.getElementById('imageFile');
                const loading = document.getElementById('ocrLoading');
                
                if (!fileInput.files[0]) {
                    alert('Please select an image file');
                    return;
                }
                
                loading.style.display = 'block';
                
                const formData = new FormData();
                formData.append('image', fileInput.files[0]);
                
                try {
                    const response = await fetch('/api/v1/ocr/process', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.analyses && result.analyses.length > 0) {
                        document.getElementById('searchInput').value = result.analyses.join(', ');
                        await searchAnalyses();
                    } else {
                        alert('No analyses detected in the image');
                    }
                } catch (error) {
                    alert('Error processing image: ' + error.message);
                } finally {
                    loading.style.display = 'none';
                }
            }
            
            async function searchAnalyses() {
                const searchInput = document.getElementById('searchInput');
                const loading = document.getElementById('searchLoading');
                const results = document.getElementById('results');
                
                if (!searchInput.value.trim()) {
                    alert('Please enter analysis names');
                    return;
                }
                
                loading.style.display = 'block';
                
                const analyses = searchInput.value.split(',').map(s => s.trim()).filter(s => s);
                
                try {
                    const response = await fetch('/api/v1/analyses/compare', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            analysis_names: analyses
                        })
                    });
                    
                    const data = await response.json();
                    displayResults(data);
                } catch (error) {
                    results.innerHTML = '<p>Error searching analyses: ' + error.message + '</p>';
                } finally {
                    loading.style.display = 'none';
                }
            }
            
            function displayResults(data) {
                const results = document.getElementById('results');
                
                if (!data.results || data.results.length === 0) {
                    results.innerHTML = '<p>No results found for the specified analyses.</p>';
                    return;
                }
                
                let html = '<h3>💰 Price Comparison Results</h3>';
                html += '<table class="price-table">';
                html += '<thead><tr><th>Analysis</th>';
                
                // Get all unique providers
                const providers = new Set();
                data.results.forEach(analysis => {
                    Object.keys(analysis.prices || {}).forEach(provider => {
                        providers.add(provider);
                    });
                });
                
                Array.from(providers).forEach(provider => {
                    html += `<th>${provider.charAt(0).toUpperCase() + provider.slice(1)}</th>`;
                });
                
                html += '</tr></thead><tbody>';
                
                data.results.forEach(analysis => {
                    html += `<tr><td><strong>${analysis.name}</strong>`;
                    if (analysis.alternative_names && analysis.alternative_names.length > 0) {
                        html += `<br><small>(${analysis.alternative_names.join(', ')})</small>`;
                    }
                    html += '</td>';
                    
                    Array.from(providers).forEach(provider => {
                        const providerPrices = analysis.prices && analysis.prices[provider];
                        html += '<td>';
                        
                        if (providerPrices) {
                            if (providerPrices.normal) {
                                html += `Normal: ${providerPrices.normal.amount} ${providerPrices.normal.currency}<br>`;
                            }
                            if (providerPrices.premium) {
                                html += `Premium: ${providerPrices.premium.amount} ${providerPrices.premium.currency}<br>`;
                            }
                            if (providerPrices.subscription) {
                                html += `Subscription: ${providerPrices.subscription.amount} ${providerPrices.subscription.currency}`;
                            }
                        } else {
                            html += 'N/A';
                        }
                        
                        html += '</td>';
                    });
                    
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                results.innerHTML = html;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Serve the admin interface"""
    try:
        admin_path = os.path.join("..", "frontend", "admin.html")
        if os.path.exists(admin_path):
            with open(admin_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        else:
            return HTMLResponse(content="<h1>Admin interface not found</h1><p>Please check if the frontend files are in place.</p>")
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading admin interface</h1><p>{str(e)}</p>")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Medical Price Comparator is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)