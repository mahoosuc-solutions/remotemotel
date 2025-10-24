#!/bin/bash
set -e

echo "=================================="
echo "Post-Start: Checking Services"
echo "=================================="

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

# Check if PostgreSQL is running
if ! docker compose -f docker-compose.postgres.yml ps | grep -q "Up"; then
  echo "Starting PostgreSQL container..."
  docker compose -f docker-compose.postgres.yml up -d

  # Wait for PostgreSQL
  echo "Waiting for PostgreSQL..."
  max_attempts=30
  attempt=0
  until docker compose -f docker-compose.postgres.yml exec -T postgres pg_isready -U stayhive; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
      echo "❌ PostgreSQL failed to start"
      exit 1
    fi
    echo "Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
    sleep 1
  done
fi

echo "✓ PostgreSQL is running"
echo "✓ Environment ready"
echo ""
echo "Platform ready! Next steps:"
echo "  - Start server: python apps/operator-runtime/main.py"
echo "  - Run tests: pytest tests/integration/ -v"
echo "  - Check health: curl http://localhost:8000/health"
