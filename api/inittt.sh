#!/bin/bash

set -e

echo "🚀 Initializing Liella Rankings API project..."

# 1. Create venv
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Format code
echo "🎨 Formatting code..."
black app/ tests/
isort app/ tests/

# 4. Run linting
echo "🔍 Running linting..."
pylint app/
flake8 app/

echo "✅ Project initialized!"
echo ""
echo "Next steps:"
echo "  1. Create .env file: cp .env.example .env"
echo "  2. Start services: docker-compose up"
echo "  3. Or run locally: make dev"