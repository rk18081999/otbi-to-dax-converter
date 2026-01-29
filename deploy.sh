#!/bin/bash

# OTBI to DAX Converter - Quick Deploy Script
# This script helps you deploy the application quickly

set -e  # Exit on error

echo "=================================="
echo "OTBI to DAX Converter - Deployment"
echo "=================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to deploy locally
deploy_local() {
    echo "📦 Local Deployment"
    echo "-------------------"
    
    # Check Python
    if ! command_exists python3; then
        echo "❌ Python 3 not found. Please install Python 3.7+"
        exit 1
    fi
    
    echo "✅ Python found: $(python3 --version)"
    
    # Create virtual environment if not exists
    if [ ! -d ".venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
    
    # Install dependencies
    echo "📥 Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    # Check API key
    if [ -z "$GEMINI_API_KEY" ]; then
        echo ""
        echo "⚠️  GEMINI_API_KEY not set!"
        echo "Please set it in llm_config.py or as environment variable"
        echo "Get one at: https://makersuite.google.com/app/apikey"
        echo ""
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    echo ""
    echo "✅ Local deployment ready!"
    echo ""
    echo "To run CLI:"
    echo "  .venv/bin/python main.py Demo_SQL.sql"
    echo ""
    echo "To run Web UI:"
    echo "  .venv/bin/python app.py"
    echo "  Then open: http://127.0.0.1:5000"
    echo ""
}

# Function to deploy with Docker
deploy_docker() {
    echo "🐳 Docker Deployment"
    echo "--------------------"
    
    # Check Docker
    if ! command_exists docker; then
        echo "❌ Docker not found. Please install Docker"
        exit 1
    fi
    
    echo "✅ Docker found: $(docker --version)"
    
    # Check API key
    if [ -z "$GEMINI_API_KEY" ]; then
        echo ""
        echo "⚠️  GEMINI_API_KEY not set!"
        echo "Please export GEMINI_API_KEY before running"
        exit 1
    fi
    
    # Build image
    echo "🔨 Building Docker image..."
    docker build -t otbi-dax-converter .
    
    # Stop existing container
    echo "🛑 Stopping existing container (if any)..."
    docker stop otbi-dax 2>/dev/null || true
    docker rm otbi-dax 2>/dev/null || true
    
    # Run container
    echo "🚀 Starting container..."
    docker run -d \
        -p 5000:5000 \
        -e GEMINI_API_KEY="$GEMINI_API_KEY" \
        --name otbi-dax \
        otbi-dax-converter
    
    echo ""
    echo "✅ Docker deployment complete!"
    echo ""
    echo "Access at: http://localhost:5000"
    echo ""
    echo "To view logs:"
    echo "  docker logs -f otbi-dax"
    echo ""
    echo "To stop:"
    echo "  docker stop otbi-dax"
    echo ""
}

# Function to deploy with Docker Compose
deploy_compose() {
    echo "🐳 Docker Compose Deployment"
    echo "-----------------------------"
    
    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        echo "❌ Docker Compose not found. Please install Docker Compose"
        exit 1
    fi
    
    # Check API key
    if [ -z "$GEMINI_API_KEY" ]; then
        echo ""
        echo "⚠️  GEMINI_API_KEY not set!"
        echo "Please export GEMINI_API_KEY before running"
        exit 1
    fi
    
    # Stop existing services
    echo "🛑 Stopping existing services..."
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
    
    # Start services
    echo "🚀 Starting services..."
    if command_exists docker-compose; then
        docker-compose up -d --build
    else
        docker compose up -d --build
    fi
    
    echo ""
    echo "✅ Docker Compose deployment complete!"
    echo ""
    echo "Access at: http://localhost:5000"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f"
    echo ""
    echo "To stop:"
    echo "  docker-compose down"
    echo ""
}

# Main menu
echo "Choose deployment method:"
echo "1) Local (Python virtual environment)"
echo "2) Docker"
echo "3) Docker Compose"
echo "4) Exit"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        deploy_local
        ;;
    2)
        deploy_docker
        ;;
    3)
        deploy_compose
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
