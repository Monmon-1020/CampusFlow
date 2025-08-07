#!/bin/bash

# CampusFlow Backend Local Startup Script

echo "🎓 CampusFlow Backend - Local Development Setup"
echo "=============================================="

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

echo "📦 Installing dependencies..."
poetry install

echo "🔧 Setting up environment..."
# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "DATABASE_URL=sqlite:///./campusflow.db" > .env
    echo "JWT_SECRET_KEY=your-secret-key-here" >> .env
    echo "GOOGLE_CLIENT_ID=your-google-client-id" >> .env
    echo "GOOGLE_CLIENT_SECRET=your-google-client-secret" >> .env
    echo "📄 Created .env file with default values"
fi

echo "🗄️  Running database migrations..."
poetry run alembic upgrade head

echo "🚀 Starting development server..."
echo "   API will be available at: http://localhost:8000"
echo "   API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000