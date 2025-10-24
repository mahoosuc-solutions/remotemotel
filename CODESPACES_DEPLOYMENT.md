# GitHub Codespaces Deployment Guide

## Overview

This guide shows how to deploy and test the Front Desk Platform in GitHub Codespaces - a cloud-based development environment with Docker, proper bash, and all tools pre-configured.

## Why Codespaces?

- **Clean Environment**: Fresh Linux container with Python 3.12, Docker, and bash
- **No Local Setup**: Bypasses WSL/bash configuration issues
- **Pre-configured**: Automatic dependency installation and database setup
- **Cloud Resources**: Sufficient CPU/memory for testing
- **Port Forwarding**: Easy access to FastAPI server and PostgreSQL
- **Free Tier**: 60 hours/month free for personal accounts

## Prerequisites

1. **GitHub Account** with access to the repository
2. **Repository Pushed** to GitHub (if not already done)
3. **Codespaces Enabled** on your GitHub account

## Quick Start

### Step 1: Create Codespace

1. Go to your GitHub repository: `https://github.com/<username>/frontdesk`
2. Click the green **Code** button
3. Select **Codespaces** tab
4. Click **Create codespace on main**

### Step 2: Wait for Setup

The devcontainer will automatically:
- ✓ Pull Python 3.12 base image
- ✓ Install Docker-in-Docker
- ✓ Install GitHub CLI
- ✓ Create virtual environment
- ✓ Install all Python dependencies
- ✓ Start PostgreSQL container
- ✓ Run database migrations
- ✓ Create data directories

**Expected Time**: 3-5 minutes

### Step 3: Verify Setup

Once the terminal shows "✓ Setup Complete!", run:

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify database
docker compose -f docker-compose.postgres.yml ps

# Check database tables
docker compose -f docker-compose.postgres.yml exec postgres psql -U stayhive -d stayhive -c "\dt"

# Test Python imports
python test_platform.py
```

## Environment Configuration

Create `.env.local` file with your API keys:

```bash
# Required for knowledge base and voice AI
OPENAI_API_KEY=sk-your-key-here

# Required for voice calls (optional for testing)
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_PHONE_NUMBER=+15551234567

# Database (pre-configured)
DATABASE_URL=postgresql://stayhive:stayhive@localhost:5433/stayhive

# Environment
ENV=development
PROJECT_ID=front-desk-dev
REGION=us-central1
```

## Running the Platform

### 1. Ingest Knowledge Base

```bash
# Activate venv
source .venv/bin/activate

# Ingest documentation
python scripts/ingest_knowledge.py --dir docs/ --hotel-id demo-hotel

# Verify ingestion
python scripts/ingest_knowledge.py --list
```

### 2. Start FastAPI Server

```bash
# Start server
python apps/operator-runtime/main.py
```

The server will start on port 8000. Codespaces will automatically forward the port and show a notification.

### 3. Test Endpoints

In a new terminal:

```bash
# Health check
curl http://localhost:8000/health

# Check availability
curl "http://localhost:8000/availability?check_in=2025-10-25&check_out=2025-10-27&adults=2&pets=false"

# Search knowledge base
curl -X POST http://localhost:8000/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "pet policy", "top_k": 3}'

# Voice health (if Twilio configured)
curl http://localhost:8000/voice/health
```

### 4. Access Web Interface

1. Click the **Ports** tab in VS Code
2. Find port **8000** (FastAPI Server)
3. Click the globe icon to open in browser
4. Or hover and click **Open in Browser**

You can now test the API from your browser or Postman!

## Running Tests

```bash
# Activate venv
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/unit/voice/ -v
pytest tests/integration/ -v

# Run with coverage
pytest tests/ --cov=packages --cov-report=html
```

## Database Management

### View Database

```bash
# Connect to PostgreSQL
docker compose -f docker-compose.postgres.yml exec postgres psql -U stayhive -d stayhive

# List tables
\dt

# View room availability
SELECT * FROM room_availability LIMIT 10;

# View leads
SELECT * FROM leads LIMIT 10;

# Exit
\q
```

### Reset Database

```bash
# Stop and remove database
docker compose -f docker-compose.postgres.yml down -v

# Restart
docker compose -f docker-compose.postgres.yml up -d

# Wait for startup
sleep 3

# Re-run migrations
SKIP_DEPS_CHECK=1 alembic upgrade head
```

### Create Test Data

```bash
# Activate venv
source .venv/bin/activate

# Run seed script (if exists)
python scripts/seed_data.py

# Or manually with psql
docker compose -f docker-compose.postgres.yml exec postgres psql -U stayhive -d stayhive <<EOF
-- Insert sample room
INSERT INTO rooms (room_type, room_number, bed_type, max_occupancy, amenities)
VALUES ('standard_queen', '101', 'queen', 2, '["wifi", "tv", "mini_fridge"]');

-- Insert availability
INSERT INTO room_availability (room_id, date, total_inventory, booked_count, available_count)
SELECT id, CURRENT_DATE + i, 10, 0, 10
FROM rooms, generate_series(0, 30) i
WHERE room_number = '101';
EOF
```

## Troubleshooting

### Setup Script Failed

```bash
# Re-run setup manually
cd /workspaces/frontdesk
bash .devcontainer/setup.sh
```

### PostgreSQL Not Starting

```bash
# Check Docker
docker ps -a

# View logs
docker compose -f docker-compose.postgres.yml logs

# Restart
docker compose -f docker-compose.postgres.yml restart
```

### Import Errors

```bash
# Verify PYTHONPATH
echo $PYTHONPATH

# Should show: /workspaces/frontdesk

# If not set:
export PYTHONPATH=/workspaces/frontdesk

# Or activate venv
source .venv/bin/activate
```

### Migrations Failed

```bash
# Check database connection
docker compose -f docker-compose.postgres.yml exec postgres pg_isready -U stayhive

# Re-run migrations
SKIP_DEPS_CHECK=1 alembic upgrade head

# If errors persist, check alembic/env.py
```

## Development Workflow

### 1. Make Code Changes

Edit files in VS Code as normal. The environment is fully configured with:
- Python IntelliSense
- Auto-formatting (Black)
- Linting (Ruff)
- Docker integration

### 2. Test Changes

```bash
# Quick test
python test_platform.py

# Full test suite
pytest tests/ -v

# Test specific endpoint
curl http://localhost:8000/your-endpoint
```

### 3. Commit Changes

```bash
# Stage changes
git add .

# Commit
git commit -m "feat: your changes"

# Push to GitHub
git push origin main
```

### 4. Stop Services

When done:

```bash
# Stop FastAPI (Ctrl+C)

# Stop PostgreSQL
docker compose -f docker-compose.postgres.yml down

# Stop Codespace (from GitHub UI or Settings)
```

## Resource Management

### Codespaces Limits

- **Free Tier**: 60 hours/month (120 core-hours)
- **Default**: 2-core machine (30 hours of usage)
- **Upgrade**: 4-core or 8-core available

### Stop When Not Using

- Codespaces **auto-stop** after 30 minutes of inactivity
- Manually stop: Click **Codespaces** icon → Stop

### Delete When Done

- Keep for ongoing work
- Delete to save storage quota
- All changes are saved in Git

## Advanced Configuration

### Custom Machine Type

Edit `.devcontainer/devcontainer.json`:

```json
{
  "hostRequirements": {
    "cpus": 4,
    "memory": "8gb",
    "storage": "32gb"
  }
}
```

### Additional Services

Add to `docker-compose.postgres.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
```

### Pre-build Configuration

For faster startup, enable Codespaces Prebuilds in repository settings.

## Next Steps

Once the platform is running in Codespaces:

1. **Test Core Features**
   - Knowledge base search
   - Availability checking
   - Lead creation
   - Payment link generation

2. **Wire Real Integrations**
   - Connect Stripe for payments
   - Configure Twilio for voice calls
   - Set up OpenAI API for embeddings

3. **Run Integration Tests**
   - Database operations
   - API endpoints
   - Voice workflows (if Twilio configured)

4. **Deploy to Cloud Run**
   - Follow DEPLOYMENT.md guide
   - Use same Docker setup
   - Configure production secrets

## Support

- **Codespaces Docs**: https://docs.github.com/en/codespaces
- **Platform Issues**: See PLATFORM_STATUS.md
- **Implementation Plan**: See COMPLETE_IMPLEMENTATION_ROADMAP.md

---

**Ready to deploy!** Push your code to GitHub and create a Codespace to start testing the platform immediately.
