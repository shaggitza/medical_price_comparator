#!/bin/bash

# Medical Price Comparator Setup Script
echo "🏥 Setting up Medical Price Comparator..."

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✅ Docker and Docker Compose found"
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        echo "📝 Creating .env file from template..."
        cp .env.template .env
        echo "⚠️  Please edit .env file with your actual API keys and configuration"
    fi
    
    echo "🚀 Starting application with Docker..."
    docker-compose up --build -d
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Check if services are running
    if curl -f -s http://localhost:8000/health > /dev/null; then
        echo "✅ Backend is running at http://localhost:8000"
        echo "✅ Admin panel available at http://localhost:8000/admin"
        echo "✅ Frontend available at http://localhost:3000"
    else
        echo "❌ Backend failed to start. Check logs with: docker-compose logs"
    fi
    
else
    echo "⚠️  Docker not found. Using local Python setup..."
    
    # Check if Python 3.11+ is available
    if command -v python3 &> /dev/null; then
        echo "✅ Python found"
        
        # Setup backend
        echo "📦 Setting up Python virtual environment..."
        cd backend
        python3 -m venv venv
        source venv/bin/activate
        
        echo "📦 Installing Python dependencies..."
        pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
        
        # Create directories
        mkdir -p static templates
        
        echo "🚀 Starting backend server..."
        export MONGODB_URL="mongodb://localhost:27017/medical_comparator"
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        
        echo "⏳ Waiting for backend to start..."
        sleep 5
        
        if curl -f -s http://localhost:8000/health > /dev/null; then
            echo "✅ Backend is running at http://localhost:8000"
            echo "✅ Admin panel available at http://localhost:8000/admin"
            echo ""
            echo "📋 Next steps:"
            echo "1. Import sample data via admin panel"
            echo "2. Add your own CSV data files"
            echo "3. Configure OCR and AI integration"
            echo ""
            echo "📖 Sample data files are available in the data/ directory"
        else
            echo "❌ Backend failed to start. Check the logs above."
        fi
        
    else
        echo "❌ Python 3 not found. Please install Python 3.11 or later."
        exit 1
    fi
fi

echo ""
echo "🎉 Setup complete!"
echo "📚 Check README.md for detailed usage instructions"