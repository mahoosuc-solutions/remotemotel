#!/bin/bash
set -e

echo "=================================="
echo "Front Desk Platform Setup"
echo "=================================="

# 1. Create virtual environment
echo "Creating Python virtual environment..."
python -m venv .venv
source .venv/bin/activate

# 2. Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# 3. Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# 4. Start PostgreSQL container
echo "Starting PostgreSQL container..."
docker compose -f docker-compose.postgres.yml up -d

# 5. Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until docker compose -f docker-compose.postgres.yml exec -T postgres pg_isready -U stayhive; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is ready!"

# 6. Run database migrations
echo "Running database migrations..."
export SKIP_DEPS_CHECK=1
alembic upgrade head

# 7. Create sample data directory
echo "Creating data directories..."
mkdir -p data/knowledge
mkdir -p data/recordings
mkdir -p logs

# 8. Display success message
echo ""
echo "=================================="
echo "✓ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Set environment variables in .env.local"
echo "  2. Ingest knowledge base: python scripts/ingest_knowledge.py --dir docs/"
echo "  3. Start server: python apps/operator-runtime/main.py"
echo ""
echo "Useful commands:"
echo "  - Test platform: python test_platform.py"
echo "  - Run tests: pytest tests/ -v"
echo "  - Check health: curl http://localhost:8000/health"
echo ""
