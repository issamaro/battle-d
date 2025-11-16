#!/bin/bash
# Startup script for Railway deployment

set -e  # Exit on error

echo "🚀 Starting Battle-D deployment..."

# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head

# Seed database with default users (only if they don't exist)
echo "🌱 Seeding database..."
python seed_db.py

# Start the application
echo "✅ Starting application server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
