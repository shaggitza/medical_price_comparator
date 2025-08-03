import csv
import os
from pathlib import Path
from ..api.providers import initialize_default_providers
from ..models import MedicalAnalysis, Provider


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
    data_dir = Path("/app/data")
    
    # Define CSV files to load
    csv_files = [
        ("sample_analyses_medlife.csv", "medlife"),
        ("sample_analyses_reginamaria.csv", "reginamaria")
    ]
    
    for filename, provider_slug in csv_files:
        csv_path = data_dir / filename
        if csv_path.exists():
            print(f"Loading data from {filename}...")
            await load_csv_data(csv_path, provider_slug)
        else:
            print(f"Warning: {filename} not found in data directory")


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