#!/bin/bash
set -e

echo "=================================="
echo "Front Desk Platform Setup"
echo "=================================="

# Detect environment
if [ -n "$CODESPACES" ]; then
  echo "🚀 Running in GitHub Codespaces"
  export ENV=codespaces
else
  echo "💻 Running in local environment"
  export ENV=local
fi

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

# 4. Copy environment file
if [ "$ENV" = "codespaces" ] && [ -f ".env.codespaces" ]; then
  echo "Copying .env.codespaces to .env.local..."
  cp .env.codespaces .env.local
elif [ ! -f ".env.local" ]; then
  echo "Creating .env.local from .env.example..."
  if [ -f ".env.example" ]; then
    cp .env.example .env.local
  fi
  echo "⚠️  Please update .env.local with your credentials"
fi

# Source environment variables
if [ -f ".env.local" ]; then
  export $(grep -v '^#' .env.local | xargs -0)
fi

# 5. Start PostgreSQL container
echo "Starting PostgreSQL container..."
docker compose -f docker-compose.postgres.yml up -d

# 6. Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=0
until docker compose -f docker-compose.postgres.yml exec -T postgres pg_isready -U stayhive; do
  attempt=$((attempt + 1))
  if [ $attempt -ge $max_attempts ]; then
    echo "❌ PostgreSQL failed to start after $max_attempts attempts"
    exit 1
  fi
  echo "PostgreSQL is unavailable - sleeping (attempt $attempt/$max_attempts)"
  sleep 2
done
echo "✓ PostgreSQL is ready!"

# 7. Create knowledge schema
echo "Creating knowledge schema..."
docker compose -f docker-compose.postgres.yml exec -T postgres psql -U stayhive -d stayhive < scripts/create_knowledge_schema.sql 2>/dev/null || echo "Schema may already exist"

# 8. Run database migrations
echo "Running database migrations..."
export SKIP_DEPS_CHECK=1
alembic upgrade head || echo "⚠️  Migrations may have already been applied"

# 9. Seed database
echo "Seeding database with sample data..."
export PYTHONPATH=$(pwd)
python scripts/seed_data.py || echo "⚠️  Database may already be seeded"

# 10. Create data directories
echo "Creating data directories..."
mkdir -p data/knowledge
mkdir -p data/recordings
mkdir -p logs

# 11. Ingest knowledge base (if OpenAI key available)
if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your-openai-api-key-here" ] && [ "$OPENAI_API_KEY" != "\${OPENAI_API_KEY}" ]; then
  echo "Ingesting knowledge base documents..."
  if [ -f "./scripts/ingest_essential_docs.sh" ]; then
    bash ./scripts/ingest_essential_docs.sh || echo "⚠️  Knowledge base may already be ingested"
  elif [ -f "./scripts/ingest_all_docs.sh" ]; then
    bash ./scripts/ingest_all_docs.sh || echo "⚠️  Knowledge base may already be ingested"
  else
    echo "⚠️  No ingestion script found"
  fi
else
  echo "⚠️  Skipping knowledge ingestion (OPENAI_API_KEY not set)"
  echo "   To enable: Set OPENAI_API_KEY as a Codespace secret"
fi

# 12. Display success message
echo ""
echo "=================================="
echo "✓ Setup Complete!"
echo "=================================="
echo ""
echo "Platform Status:"
echo "  ✓ PostgreSQL running on port 5433"
echo "  ✓ Database migrated and seeded"
if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your-openai-api-key-here" ] && [ "$OPENAI_API_KEY" != "\${OPENAI_API_KEY}" ]; then
  echo "  ✓ Knowledge base ingested"
else
  echo "  ⚠️  Knowledge base not ingested (no OpenAI key)"
fi
echo ""
echo "Next steps:"
echo "  1. Start server: python apps/operator-runtime/main.py"
echo "  2. Run tests: pytest tests/integration/ -v"
echo "  3. Check health: curl http://localhost:8000/health"
echo ""
echo "Useful commands:"
echo "  - View logs: docker compose -f docker-compose.postgres.yml logs -f"
echo "  - Reset DB: docker compose -f docker-compose.postgres.yml down -v"
echo "  - Validate setup: python scripts/verify_codespaces_setup.py"
echo ""
