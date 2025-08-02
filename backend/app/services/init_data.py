from ..api.providers import initialize_default_providers
from ..models import MedicalAnalysis


async def initialize_app_data():
    """Initialize application with default data"""
    try:
        # Initialize default providers
        await initialize_default_providers()
        
        # Check if we have any analyses using Beanie
        analysis_count = await MedicalAnalysis.count()
        
        if analysis_count == 0:
            print("No medical analyses found. Please use the admin interface to import data.")
            print("Sample CSV files are available in the data/ directory.")
        else:
            print(f"Found {analysis_count} medical analyses in database.")
        
        print("Application initialized successfully!")
    except Exception as e:
        print(f"Warning during initialization: {e}")