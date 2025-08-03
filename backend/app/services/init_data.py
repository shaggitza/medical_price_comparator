import csv
import os
from pathlib import Path
from ..api.providers import initialize_default_providers
from ..models import MedicalAnalysis, Provider
from ..config import settings


async def initialize_app_data():
    """Initialize application with default data"""
    try:
        # Initialize default providers
        await initialize_default_providers()
        
        # Check if we have any analyses using Beanie
        analysis_count = await MedicalAnalysis.count()
        
        if analysis_count == 0:
            print("No medical analyses found. Loading sample data...")
            await load_sample_data()
        else:
            print(f"Found {analysis_count} medical analyses in database.")
        
        print("Application initialized successfully!")
    except Exception as e:
        print(f"Warning during initialization: {e}")


async def load_sample_data():
    """Load sample data from CSV files"""
    data_dir = settings.resolved_data_path
    print(f"Loading sample data from: {data_dir}")
    
    if not data_dir.exists():
        print(f"Warning: Data directory {data_dir} does not exist. Cannot load sample data.")
        print("Available paths checked:")
        print(f"  - Configured path: {settings.data_path or 'Not set'}")
        print(f"  - Docker path: /app/data ({'exists' if Path('/app/data').exists() else 'does not exist'})")
        print(f"  - Resolved path: {data_dir}")
        return
    
    # Define CSV files to load
    csv_files = [
        ("sample_analyses_medlife.csv", "medlife"),
        ("sample_analyses_reginamaria.csv", "reginamaria")
    ]
    
    loaded_any = False
    for filename, provider_slug in csv_files:
        csv_path = data_dir / filename
        if csv_path.exists():
            print(f"Loading data from {filename}...")
            await load_csv_data(csv_path, provider_slug)
            loaded_any = True
        else:
            print(f"Warning: {filename} not found in data directory {data_dir}")
    
    if not loaded_any:
        print(f"Warning: No sample data files found in {data_dir}")
        print("Expected files:")
        for filename, _ in csv_files:
            print(f"  - {filename}")
        
        # List available files for debugging
        try:
            available_files = list(data_dir.glob("*"))
            if available_files:
                print("Available files in data directory:")
                for file in available_files:
                    print(f"  - {file.name}")
            else:
                print("Data directory is empty")
        except Exception as e:
            print(f"Could not list files in data directory: {e}")


async def load_csv_data(csv_path: Path, provider_slug: str):
    """Load data from a specific CSV file"""
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            loaded_count = 0
            
            for row in reader:
                analysis_name = row['name'].strip()
                category = row['category'].strip()
                price = float(row['price'])
                price_type = row['price_type'].strip()
                currency = row['currency'].strip()
                alternative_names = [name.strip() for name in row['alternative_names'].split(';') if name.strip()]
                description = row.get('description', '').strip()
                
                # Find or create analysis
                analysis = await MedicalAnalysis.find_one({"name": analysis_name})
                
                if not analysis:
                    # Create new analysis
                    analysis = MedicalAnalysis(
                        name=analysis_name,
                        alternative_names=alternative_names,
                        category=category,
                        description=description,
                        prices={}
                    )
                
                # Add price for this provider
                if provider_slug not in analysis.prices:
                    analysis.prices[provider_slug] = {}
                
                analysis.prices[provider_slug][price_type] = {
                    "amount": price,
                    "currency": currency
                }
                
                # Save analysis
                await analysis.save()
                loaded_count += 1
            
            print(f"Loaded {loaded_count} analyses from {csv_path.name}")
    
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")