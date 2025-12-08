#!/bin/bash
# One-command local development setup for Battle-D
# Usage: ./scripts/dev.sh
#
# This script:
# 1. Creates/activates virtual environment
# 2. Installs dependencies
# 3. Sets up environment file
# 4. Runs database migrations
# 5. Seeds test accounts
# 6. Starts the development server

set -e  # Exit on any error

echo "🚀 Setting up Battle-D local development..."
echo ""

# 1. Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed."
    echo ""
    echo "   Install it with:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    exit 1
fi

# 2. Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
source .venv/bin/activate

# 3. Install dependencies
echo "📦 Installing dependencies..."
uv pip install -r requirements.txt --quiet

# 4. Setup environment file if needed
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from .env.example..."
    cp .env.example .env
    # Set console email provider for dev (cross-platform sed)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' 's/EMAIL_PROVIDER=brevo/EMAIL_PROVIDER=console/' .env
    else
        sed -i 's/EMAIL_PROVIDER=brevo/EMAIL_PROVIDER=console/' .env
    fi
fi

# 5. Initialize database
echo "🗄️  Initializing database..."
mkdir -p data

# Run migrations
.venv/bin/alembic upgrade head

# 6. Seed test accounts
echo "🌱 Seeding test accounts..."
.venv/bin/python seed_db.py

# 7. Start server
echo ""
echo "=========================================="
echo "✅ Battle-D is running at: http://localhost:8000"
echo ""
echo "📧 Test accounts:"
echo "   • admin@battle-d.com (Admin)"
echo "   • staff@battle-d.com (Staff)"
echo "   • mc@battle-d.com (MC)"
echo ""
echo "🔗 Magic links will print to console."
echo "   Copy/paste the URL to log in."
echo "=========================================="
echo ""

.venv/bin/uvicorn app.main:app --reload
