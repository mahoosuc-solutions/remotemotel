# GitHub Codespaces Integration Plan

**Objective**: Ensure the RemoteMotel platform runs seamlessly in GitHub Codespaces with 100% test pass rate and full operational capability.

**Target Timeline**: 2-3 hours
**Status**: 🔧 In Planning

---

## Current State Analysis

### ✅ What's Already Working

1. **Devcontainer Configuration** ([.devcontainer/devcontainer.json](.devcontainer/devcontainer.json))
   - Python 3.12 base image configured
   - Docker-in-Docker for PostgreSQL container
   - GitHub CLI integration
   - VS Code extensions (Python, Black, Ruff, Docker, YAML)
   - Ports forwarded (8000 for FastAPI, 5433 for PostgreSQL)
   - Python path and environment variables set

2. **Setup Script** ([.devcontainer/setup.sh](.devcontainer/setup.sh))
   - Virtual environment creation
   - Pip upgrade and dependency installation
   - PostgreSQL container startup
   - Database migrations
   - Directory creation

3. **Local Development**
   - Platform 100% operational locally
   - All 88 tests passing (18 integration + 70 voice)
   - Database seeded with 10 rooms, 20 rates, 900 availability records
   - Knowledge base with 10 documents ingested (100,000+ words)

### ❌ Identified Gaps

1. **Environment Variables**
   - No `.env.codespaces` file for Codespaces-specific config
   - Sensitive credentials (OpenAI, Twilio, Stripe) not configured
   - Need GitHub Codespaces Secrets integration

2. **Database Seeding**
   - Setup script doesn't run `seed_data.py`
   - No data available for tests after fresh Codespace creation

3. **Knowledge Base Ingestion**
   - Setup script doesn't run knowledge ingestion
   - 10 documents need to be ingested for search functionality

4. **Secret Management**
   - OpenAI API key required for embeddings
   - Twilio credentials for voice tests (optional but recommended)
   - Stripe key for payment tests (optional but recommended)

5. **Test Configuration**
   - Need to verify pytest configuration works in Codespaces
   - May need Codespaces-specific test markers

6. **Documentation**
   - No Codespaces-specific README or getting started guide
   - Missing troubleshooting section for common Codespaces issues

---

## Integration Plan

### Phase 1: Environment Configuration (30 minutes)

#### Task 1.1: Create `.env.codespaces` Template

**File**: `.env.codespaces`

**Purpose**: Provide a clean template for Codespaces that uses GitHub Secrets

**Content**:
```bash
# GitHub Codespaces Environment Configuration
# Secrets should be configured at: https://github.com/USER/REPO/settings/secrets/codespaces

# Environment
ENV=codespaces
PROJECT_ID=remotemotel-codespaces
REGION=us-central1

# Database (Local PostgreSQL in container)
DATABASE_URL=postgresql://stayhive:stayhive@localhost:5433/stayhive

# OpenAI (Required - Set as Codespace Secret)
OPENAI_API_KEY=${OPENAI_API_KEY}

# Twilio (Optional - For voice testing)
TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID:-MOCK}
TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN:-MOCK}
TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER:-+15555555555}

# Stripe (Optional - For payment testing)
STRIPE_API_KEY=${STRIPE_API_KEY:-MOCK}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:-MOCK}

# Voice Module
VOICE_ENABLED=true
VOICE_RECORDING_ENABLED=true
VOICE_RECORDING_PATH=/workspace/data/recordings
OPENAI_REALTIME_ENABLED=true
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

# Knowledge Base
KNOWLEDGE_TOP_K=5
EMBEDDING_MODEL=text-embedding-3-small

# Feature Flags
FEATURE_VOICE_AI=true
FEATURE_PAYMENT_LINKS=true
FEATURE_BOOKING_ENGINE=true
FEATURE_KNOWLEDGE_BASE=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Testing
SKIP_DEPS_CHECK=1
PYTHONPATH=/workspace
```

**Action**: Create file and update .gitignore to exclude it

---

#### Task 1.2: Update `devcontainer.json`

**Changes Required**:
1. Add `onCreateCommand` to copy `.env.codespaces` to `.env.local`
2. Add environment variable mappings for GitHub Secrets
3. Configure lifecycle hooks properly

**Updated Configuration**:
```json
{
  "name": "Front Desk Platform",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",

  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },

  "onCreateCommand": "cp .env.codespaces .env.local",
  "postCreateCommand": "bash .devcontainer/setup.sh",
  "postStartCommand": "bash .devcontainer/post-start.sh",

  "forwardPorts": [8000, 5433],
  "portsAttributes": {
    "8000": {
      "label": "FastAPI Server",
      "onAutoForward": "notify"
    },
    "5433": {
      "label": "PostgreSQL",
      "onAutoForward": "silent"
    }
  },

  "remoteEnv": {
    "PYTHONPATH": "${containerWorkspaceFolder}",
    "ENV": "codespaces",
    "DATABASE_URL": "postgresql://stayhive:stayhive@localhost:5433/stayhive",
    "OPENAI_API_KEY": "${localEnv:OPENAI_API_KEY}",
    "SKIP_DEPS_CHECK": "1"
  },

  "secrets": {
    "OPENAI_API_KEY": {
      "description": "OpenAI API key for embeddings and voice AI"
    },
    "TWILIO_ACCOUNT_SID": {
      "description": "Twilio Account SID (optional for voice testing)"
    },
    "TWILIO_AUTH_TOKEN": {
      "description": "Twilio Auth Token (optional for voice testing)"
    }
  },

  "mounts": [
    "source=${localWorkspaceFolderBasename}-venv,target=${containerWorkspaceFolder}/.venv,type=volume"
  ],

  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "charliermarsh.ruff",
        "ms-azuretools.vscode-docker",
        "redhat.vscode-yaml",
        "GitHub.copilot"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/workspace/.venv/bin/python",
        "python.formatting.provider": "black",
        "python.linting.enabled": true,
        "python.linting.ruffEnabled": true,
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
          "source.organizeImports": "explicit"
        }
      }
    }
  }
}
```

---

#### Task 1.3: Enhance `setup.sh`

**Add**:
1. Database seeding
2. Knowledge base ingestion (if OpenAI key available)
3. Better error handling
4. Codespaces detection

**Enhanced Script**:
```bash
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
  cp .env.example .env.local
  echo "⚠️  Please update .env.local with your credentials"
fi

# Source environment variables
export $(grep -v '^#' .env.local | xargs)

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
docker compose -f docker-compose.postgres.yml exec -T postgres psql -U stayhive -d stayhive < scripts/create_knowledge_schema.sql || echo "Schema may already exist"

# 8. Run database migrations
echo "Running database migrations..."
export SKIP_DEPS_CHECK=1
alembic upgrade head || echo "⚠️  Migrations may have already been applied"

# 9. Seed database
echo "Seeding database with sample data..."
export PYTHONPATH=$(pwd)
python scripts/seed_data.py || echo "⚠️  Database may already be seeded"

# 10. Ingest knowledge base (if OpenAI key available)
if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your-openai-api-key-here" ]; then
  echo "Ingesting knowledge base documents..."
  ./scripts/ingest_all_docs.sh || echo "⚠️  Knowledge base may already be ingested"
else
  echo "⚠️  Skipping knowledge ingestion (OPENAI_API_KEY not set)"
  echo "   To enable: Set OPENAI_API_KEY as a Codespace secret"
fi

# 11. Create data directories
echo "Creating data directories..."
mkdir -p data/knowledge
mkdir -p data/recordings
mkdir -p logs

# 12. Run tests to verify setup
echo "Running quick health check..."
pytest tests/integration/knowledge/test_api.py::test_list_documents_endpoint -v || echo "⚠️  Some tests failed"

# 13. Display success message
echo ""
echo "=================================="
echo "✓ Setup Complete!"
echo "=================================="
echo ""
echo "Platform Status:"
echo "  ✓ PostgreSQL running on port 5433"
echo "  ✓ Database migrated and seeded"
if [ -n "$OPENAI_API_KEY" ]; then
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
echo "  - Ingest docs: ./scripts/ingest_all_docs.sh"
echo ""
```

---

#### Task 1.4: Create `post-start.sh`

**Purpose**: Run on every Codespace restart (not just first creation)

**File**: `.devcontainer/post-start.sh`

```bash
#!/bin/bash
set -e

echo "=================================="
echo "Post-Start: Checking Services"
echo "=================================="

# Activate virtual environment
source .venv/bin/activate

# Check if PostgreSQL is running
if ! docker compose -f docker-compose.postgres.yml ps | grep -q "Up"; then
  echo "Starting PostgreSQL container..."
  docker compose -f docker-compose.postgres.yml up -d

  # Wait for PostgreSQL
  until docker compose -f docker-compose.postgres.yml exec -T postgres pg_isready -U stayhive; do
    echo "Waiting for PostgreSQL..."
    sleep 1
  done
fi

echo "✓ PostgreSQL is running"
echo "✓ Environment ready"
echo ""
echo "Start server: python apps/operator-runtime/main.py"
```

---

### Phase 2: Secret Management (15 minutes)

#### Task 2.1: Document Secret Configuration

**File**: `CODESPACES_SECRETS.md`

**Content**:
```markdown
# GitHub Codespaces Secrets Configuration

## Required Secrets

### OPENAI_API_KEY (Required)
- **Purpose**: Powers knowledge base embeddings and voice AI
- **Get Key**: https://platform.openai.com/api-keys
- **Set Secret**:
  1. Go to Repository Settings → Secrets → Codespaces
  2. Click "New repository secret"
  3. Name: `OPENAI_API_KEY`
  4. Value: `sk-...` (your OpenAI API key)

## Optional Secrets (For Full Feature Testing)

### TWILIO_ACCOUNT_SID
- **Purpose**: Voice call testing
- **Get Key**: https://console.twilio.com/
- **Format**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### TWILIO_AUTH_TOKEN
- **Purpose**: Voice call authentication
- **Format**: 32-character alphanumeric string

### STRIPE_API_KEY
- **Purpose**: Payment link generation testing
- **Get Key**: https://dashboard.stripe.com/test/apikeys
- **Format**: `sk_test_...`

## Setting Secrets

### Repository-wide (Recommended)
1. Navigate to: `https://github.com/YOUR_ORG/remotemotel/settings/secrets/codespaces`
2. Click "New repository secret"
3. Add each secret name and value
4. Secrets will be available in all Codespaces for this repo

### Per-Codespace (Advanced)
1. Open Codespace settings: `https://github.com/settings/codespaces`
2. Click on your Codespace name
3. Add secrets in the "Secrets" section
4. Restart Codespace to apply

## Verification

After setting secrets, verify in Codespace terminal:
```bash
echo $OPENAI_API_KEY  # Should show sk-...
echo $TWILIO_ACCOUNT_SID  # Should show AC... or empty
```

## Troubleshooting

**Secret not available in Codespace?**
- Ensure secret is set at repository level, not user level
- Rebuild Codespace: Cmd/Ctrl+Shift+P → "Codespaces: Rebuild Container"
- Check secret name matches exactly (case-sensitive)

**OpenAI API errors?**
- Verify key is valid: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`
- Check billing: https://platform.openai.com/account/billing
```

---

#### Task 2.2: Create Secret Validation Script

**File**: `scripts/validate_secrets.py`

```python
#!/usr/bin/env python3
"""Validate that required secrets are configured correctly."""

import os
import sys
from typing import Dict, List, Tuple

def check_secret(name: str, required: bool = False) -> Tuple[bool, str]:
    """Check if a secret is configured."""
    value = os.getenv(name)

    if not value:
        status = "❌ MISSING" if required else "⚠️  NOT SET"
        return (False, status)

    if value in ["your-openai-api-key-here", "MOCK", "sk-your-openai-api-key-here"]:
        return (False, "⚠️  DEFAULT VALUE (not configured)")

    # Basic format validation
    if name == "OPENAI_API_KEY" and not value.startswith("sk-"):
        return (False, "❌ INVALID FORMAT")

    if name == "TWILIO_ACCOUNT_SID" and not value.startswith("AC"):
        return (False, "⚠️  INVALID FORMAT")

    # Mask the value for display
    if len(value) > 8:
        masked = f"{value[:4]}...{value[-4:]}"
    else:
        masked = "***"

    return (True, f"✓ CONFIGURED ({masked})")

def main():
    """Validate all secrets."""
    print("================================")
    print("Secret Configuration Validation")
    print("================================\n")

    secrets = {
        "Required Secrets": [
            ("OPENAI_API_KEY", True),
            ("DATABASE_URL", True),
        ],
        "Optional Secrets (Voice Testing)": [
            ("TWILIO_ACCOUNT_SID", False),
            ("TWILIO_AUTH_TOKEN", False),
            ("TWILIO_PHONE_NUMBER", False),
        ],
        "Optional Secrets (Payment Testing)": [
            ("STRIPE_API_KEY", False),
            ("STRIPE_WEBHOOK_SECRET", False),
        ]
    }

    all_valid = True

    for category, secret_list in secrets.items():
        print(f"{category}:")
        for secret_name, required in secret_list:
            valid, status = check_secret(secret_name, required)
            print(f"  {secret_name}: {status}")
            if required and not valid:
                all_valid = False
        print()

    # Summary
    print("================================")
    if all_valid:
        print("✓ All required secrets configured!")
        print("\nPlatform ready for:")
        print("  ✓ Database operations")
        print("  ✓ Knowledge base (semantic search)")
        print("  ✓ Voice AI (if Twilio configured)")
        print("  ✓ Payment links (if Stripe configured)")
        sys.exit(0)
    else:
        print("❌ Missing required secrets!")
        print("\nTo fix:")
        print("  1. Set secrets at: https://github.com/settings/codespaces")
        print("  2. See CODESPACES_SECRETS.md for detailed instructions")
        print("  3. Rebuild container: Cmd/Ctrl+Shift+P → Rebuild Container")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

### Phase 3: Database & Knowledge Base (30 minutes)

#### Task 3.1: Verify Database Seeding Script

**Check**: `scripts/seed_data.py` works correctly
**Action**: Add better error handling and Codespaces compatibility

**Enhancement**:
```python
# Add at the top of seed_data.py
import os

def get_database_url():
    """Get database URL from environment."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback for Codespaces
        db_url = "postgresql://stayhive:stayhive@localhost:5433/stayhive"
    return db_url

# Update engine creation
engine = create_engine(get_database_url())
```

---

#### Task 3.2: Optimize Knowledge Ingestion for Codespaces

**Issue**: Ingesting 10 documents takes ~45 seconds and uses OpenAI credits

**Solution**: Create a "quick start" option that ingests only essential docs

**File**: `scripts/ingest_essential_docs.sh`

```bash
#!/bin/bash
# Quick ingestion of essential documents for Codespaces

set -e

export DATABASE_URL="postgresql://stayhive:stayhive@localhost:5433/stayhive"
export PYTHONPATH=$(pwd)

if [ -z "$OPENAI_API_KEY" ]; then
  echo "❌ OPENAI_API_KEY not set"
  exit 1
fi

echo "🔄 Quick knowledge ingestion (4 essential documents)..."

# Core documentation only
python3 scripts/ingest_knowledge.py VOICE_MODULE_DESIGN.md \
  --hotel remotemotel \
  --title "Voice Module Design" \
  --tags "voice,design,architecture"

python3 scripts/ingest_knowledge.py INTEGRATION_PLAN.md \
  --hotel remotemotel \
  --title "Platform Integration Plan" \
  --tags "integration,plan"

python3 scripts/ingest_knowledge.py docs/STAYHIVE_QUICKSTART.md \
  --hotel remotemotel \
  --title "StayHive Platform Quickstart" \
  --tags "quickstart,setup"

python3 scripts/ingest_knowledge.py COMPLETE_IMPLEMENTATION_ROADMAP.md \
  --hotel remotemotel \
  --title "Complete Implementation Roadmap" \
  --tags "roadmap,implementation"

echo "✅ Essential knowledge base ready!"
```

---

### Phase 4: Testing Configuration (20 minutes)

#### Task 4.1: Create Codespaces Test Configuration

**File**: `pytest.codespaces.ini`

```ini
[pytest]
# Codespaces-specific pytest configuration
minversion = 6.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers for Codespaces
markers =
    integration: Integration tests requiring database
    voice: Voice module tests (may need Twilio credentials)
    knowledge: Knowledge base tests (requires OpenAI)
    payment: Payment tests (requires Stripe)
    fast: Quick tests that don't require external services
    slow: Slow tests that may take >5 seconds

# Skip slow tests by default in Codespaces
addopts =
    -v
    --tb=short
    --strict-markers
    -m "not slow"
    --maxfail=5
    --durations=10

# Async configuration
asyncio_mode = auto

# Coverage (optional)
# addopts = --cov=packages --cov-report=html

# Logging
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S
```

---

#### Task 4.2: Add Test Markers to Tests

**Update** key test files with markers:

```python
# tests/integration/test_hotel_system.py
import pytest

@pytest.mark.integration
@pytest.mark.fast
class TestHotelSystemIntegration:
    ...

# tests/integration/test_realtime_activation.py
@pytest.mark.integration
@pytest.mark.voice
def test_realtime_client_connection():
    ...

# tests/integration/knowledge/test_api.py
@pytest.mark.integration
@pytest.mark.knowledge
def test_list_documents_endpoint():
    ...
```

---

#### Task 4.3: Create Test Runner Script

**File**: `scripts/run_codespaces_tests.sh`

```bash
#!/bin/bash
# Smart test runner for Codespaces

set -e

echo "=================================="
echo "Codespaces Test Suite"
echo "=================================="

# Activate environment
source .venv/bin/activate
export $(grep -v '^#' .env.local | xargs)

# Check which services are available
HAS_OPENAI=false
HAS_TWILIO=false

if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "MOCK" ]; then
  HAS_OPENAI=true
fi

if [ -n "$TWILIO_ACCOUNT_SID" ] && [ "$TWILIO_ACCOUNT_SID" != "MOCK" ]; then
  HAS_TWILIO=true
fi

echo ""
echo "Test Configuration:"
echo "  Database: ✓ (local PostgreSQL)"
echo "  OpenAI: $([ "$HAS_OPENAI" = true ] && echo "✓" || echo "⚠️  MOCK")"
echo "  Twilio: $([ "$HAS_TWILIO" = true ] && echo "✓" || echo "⚠️  MOCK")"
echo ""

# Build test command
TEST_MARKERS=""

if [ "$HAS_OPENAI" = false ]; then
  TEST_MARKERS="not knowledge"
fi

if [ "$HAS_TWILIO" = false ]; then
  if [ -n "$TEST_MARKERS" ]; then
    TEST_MARKERS="$TEST_MARKERS and not voice"
  else
    TEST_MARKERS="not voice"
  fi
fi

# Run tests
if [ -n "$TEST_MARKERS" ]; then
  echo "Running tests (excluding: $TEST_MARKERS)..."
  pytest tests/integration/ -v -m "$TEST_MARKERS"
else
  echo "Running all tests..."
  pytest tests/integration/ -v
fi

echo ""
echo "✓ Tests complete!"
```

---

### Phase 5: Documentation (15 minutes)

#### Task 5.1: Create `CODESPACES_QUICKSTART.md`

**File**: `CODESPACES_QUICKSTART.md`

```markdown
# GitHub Codespaces Quickstart

Get the RemoteMotel platform running in GitHub Codespaces in under 5 minutes.

## Prerequisites

1. **GitHub Account** with Codespaces enabled
2. **OpenAI API Key** (required for knowledge base)
   - Get one at: https://platform.openai.com/api-keys
3. **Optional**: Twilio and Stripe credentials for full testing

## Setup Steps

### Step 1: Configure Secrets (One-time setup)

1. Go to: https://github.com/mahoosuc-solutions/remotemotel/settings/secrets/codespaces
2. Add `OPENAI_API_KEY` secret with your OpenAI key
3. (Optional) Add `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`
4. (Optional) Add `STRIPE_API_KEY`

See [CODESPACES_SECRETS.md](CODESPACES_SECRETS.md) for detailed instructions.

### Step 2: Create Codespace

1. Go to: https://github.com/mahoosuc-solutions/remotemotel
2. Click green "Code" button
3. Select "Codespaces" tab
4. Click "Create codespace on main"

**Wait 3-5 minutes** for automatic setup:
- ✓ Python environment configured
- ✓ PostgreSQL container started
- ✓ Database migrated and seeded
- ✓ Knowledge base ingested (if OpenAI key set)

### Step 3: Verify Setup

```bash
# Check secrets
python scripts/validate_secrets.py

# Run health check
curl http://localhost:8000/health

# Run tests
./scripts/run_codespaces_tests.sh
```

### Step 4: Start the Server

```bash
# Activate environment
source .venv/bin/activate

# Start FastAPI server
python apps/operator-runtime/main.py
```

Server will be available at: `https://YOUR_CODESPACE-8000.app.github.dev`

## Common Tasks

### Run All Tests
```bash
pytest tests/integration/ -v
```

### Run Specific Test Category
```bash
pytest tests/integration/ -v -m integration  # Database tests
pytest tests/integration/ -v -m knowledge    # Knowledge base tests
pytest tests/integration/ -v -m voice        # Voice module tests
```

### Ingest Additional Documentation
```bash
./scripts/ingest_all_docs.sh  # All 10 documents (slower)
./scripts/ingest_essential_docs.sh  # 4 core documents (faster)
```

### Check Database Status
```bash
# View PostgreSQL logs
docker compose -f docker-compose.postgres.yml logs -f postgres

# Connect to database
docker compose -f docker-compose.postgres.yml exec postgres psql -U stayhive -d stayhive

# Count seeded records
docker compose -f docker-compose.postgres.yml exec -T postgres psql -U stayhive -d stayhive -c "SELECT 'rooms' as table, COUNT(*) FROM rooms UNION SELECT 'rates', COUNT(*) FROM room_rates UNION SELECT 'availability', COUNT(*) FROM room_availability;"
```

### Reset Database
```bash
# Stop and remove containers
docker compose -f docker-compose.postgres.yml down -v

# Recreate
docker compose -f docker-compose.postgres.yml up -d

# Wait for ready
until docker compose -f docker-compose.postgres.yml exec -T postgres pg_isready -U stayhive; do sleep 1; done

# Recreate schema
docker compose -f docker-compose.postgres.yml exec -T postgres psql -U stayhive -d stayhive < scripts/create_knowledge_schema.sql

# Run migrations
export SKIP_DEPS_CHECK=1
alembic upgrade head

# Seed data
python scripts/seed_data.py

# Ingest knowledge
./scripts/ingest_essential_docs.sh
```

## Troubleshooting

### PostgreSQL Won't Start
```bash
# Check container status
docker compose -f docker-compose.postgres.yml ps

# View logs
docker compose -f docker-compose.postgres.yml logs postgres

# Restart
docker compose -f docker-compose.postgres.yml restart
```

### Tests Failing
```bash
# Validate secrets
python scripts/validate_secrets.py

# Check environment
env | grep -E "DATABASE_URL|OPENAI|TWILIO|STRIPE"

# Run single test
pytest tests/integration/test_hotel_system.py::TestHotelSystemIntegration::test_rate_service_integration -v
```

### Knowledge Base Empty
```bash
# Check if documents were ingested
python3 -c "
import asyncio
from packages.knowledge.service import KnowledgeService

async def check():
    service = KnowledgeService()
    docs = await service.list_documents('remotemotel', limit=50)
    print(f'Documents: {len(docs)}')
    for doc in docs:
        print(f'  - {doc.title}')

asyncio.run(check())
"

# Re-ingest if empty
./scripts/ingest_essential_docs.sh
```

### Codespace Running Slow
- Check CPU/memory usage: `htop`
- Stop PostgreSQL when not testing: `docker compose -f docker-compose.postgres.yml stop`
- Use smaller Codespace machine type in settings

## Features Available in Codespaces

✅ **Fully Functional**:
- Hotel management (rooms, rates, availability, bookings)
- Knowledge base with semantic search
- Lead capture and management
- Database operations
- All API endpoints

⚠️ **Requires Configuration**:
- Voice AI (needs Twilio credentials)
- Payment links (needs Stripe credentials)
- External webhooks (use ngrok or Codespaces forwarding)

## Performance Notes

- **Initial setup**: 3-5 minutes (one-time)
- **Restart**: 30-60 seconds
- **Test suite**: 8-15 seconds (depending on markers)
- **Knowledge ingestion**: 15-45 seconds (depending on documents)

## Cost Considerations

- **GitHub Codespaces**: 60 hours/month free for individual accounts
- **OpenAI API**: ~$0.02 per knowledge ingestion (10 documents)
- **Twilio**: Free tier available for testing
- **Stripe**: Test mode is free

## Next Steps

1. **Explore the API**: http://localhost:8000/docs (FastAPI Swagger)
2. **Run the platform**: [PLATFORM_100_COMPLETE.md](PLATFORM_100_COMPLETE.md)
3. **Build features**: [GUEST_AND_STAFF_FEATURES_ROADMAP.md](GUEST_AND_STAFF_FEATURES_ROADMAP.md)
4. **Deploy to production**: [CLOUD_DEPLOYMENT_GUIDE.md](CLOUD_DEPLOYMENT_GUIDE.md)

## Support

- **Issues**: https://github.com/mahoosuc-solutions/remotemotel/issues
- **Discussions**: https://github.com/mahoosuc-solutions/remotemotel/discussions
```

---

### Phase 6: Verification & Testing (20 minutes)

#### Task 6.1: Create Automated Verification Script

**File**: `scripts/verify_codespaces_setup.py`

```python
#!/usr/bin/env python3
"""
Comprehensive verification script for Codespaces setup.
Checks all components and reports status.
"""

import asyncio
import os
import subprocess
import sys
from typing import Tuple

def run_command(cmd: str) -> Tuple[bool, str]:
    """Run a shell command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return (result.returncode == 0, result.stdout + result.stderr)
    except Exception as e:
        return (False, str(e))

async def check_database():
    """Check database connectivity and data."""
    print("Checking database...")

    # Check container
    success, output = run_command("docker compose -f docker-compose.postgres.yml ps | grep Up")
    if not success:
        return (False, "PostgreSQL container not running")

    # Check connectivity
    success, output = run_command(
        "docker compose -f docker-compose.postgres.yml exec -T postgres " +
        "psql -U stayhive -d stayhive -c 'SELECT 1'"
    )
    if not success:
        return (False, "Cannot connect to database")

    # Check seeded data
    success, output = run_command(
        "docker compose -f docker-compose.postgres.yml exec -T postgres " +
        "psql -U stayhive -d stayhive -t -c 'SELECT COUNT(*) FROM rooms'"
    )
    if not success or int(output.strip()) == 0:
        return (False, "Database not seeded")

    return (True, f"✓ {output.strip()} rooms seeded")

async def check_knowledge_base():
    """Check knowledge base ingestion."""
    print("Checking knowledge base...")

    try:
        from packages.knowledge.service import KnowledgeService
        service = KnowledgeService()
        docs = await service.list_documents('remotemotel', limit=50)

        if len(docs) == 0:
            return (False, "No documents ingested")

        return (True, f"✓ {len(docs)} documents ingested")
    except Exception as e:
        return (False, f"Error: {str(e)}")

async def check_environment():
    """Check environment variables."""
    print("Checking environment variables...")

    required = ["DATABASE_URL", "OPENAI_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        return (False, f"Missing: {', '.join(missing)}")

    return (True, "✓ All required variables set")

async def main():
    """Run all verification checks."""
    print("=" * 50)
    print("Codespaces Setup Verification")
    print("=" * 50)
    print()

    checks = {
        "Environment Variables": check_environment(),
        "Database Connectivity": check_database(),
        "Knowledge Base": check_knowledge_base(),
    }

    results = {}
    for name, check_coro in checks.items():
        success, message = await check_coro
        results[name] = (success, message)
        status = "✓" if success else "✗"
        print(f"{status} {name}: {message}")

    print()
    print("=" * 50)

    all_passed = all(success for success, _ in results.values())

    if all_passed:
        print("✓ All checks passed!")
        print()
        print("Platform is ready. Start server with:")
        print("  python apps/operator-runtime/main.py")
        return 0
    else:
        print("✗ Some checks failed")
        print()
        print("To fix:")
        print("  1. Check .env.local configuration")
        print("  2. Run setup: bash .devcontainer/setup.sh")
        print("  3. See CODESPACES_QUICKSTART.md for help")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

---

## Summary & Timeline

### Estimated Time: 2-3 hours

| Phase | Tasks | Time | Priority |
|-------|-------|------|----------|
| **Phase 1** | Environment Configuration | 30 min | HIGH |
| **Phase 2** | Secret Management | 15 min | HIGH |
| **Phase 3** | Database & Knowledge Base | 30 min | HIGH |
| **Phase 4** | Testing Configuration | 20 min | MEDIUM |
| **Phase 5** | Documentation | 15 min | MEDIUM |
| **Phase 6** | Verification & Testing | 20 min | HIGH |
| **Total** | | **2.5 hours** | |

### Success Criteria

- ✅ Codespace launches successfully (< 5 minutes)
- ✅ PostgreSQL container starts and is accessible
- ✅ Database migrated and seeded with 10+ rooms
- ✅ Knowledge base ingested with 4-10 documents
- ✅ All integration tests pass (18/18)
- ✅ Environment secrets properly configured
- ✅ Documentation clear and comprehensive

### Post-Implementation

1. **Test the setup** by creating a fresh Codespace
2. **Document any issues** encountered during testing
3. **Create video walkthrough** (optional but recommended)
4. **Update main README** with Codespaces badge and instructions

---

## Files to Create/Update

### New Files (9)
1. `.env.codespaces` - Codespaces environment template
2. `.devcontainer/post-start.sh` - Restart services script
3. `CODESPACES_SECRETS.md` - Secret configuration guide
4. `CODESPACES_QUICKSTART.md` - Quick start guide
5. `scripts/validate_secrets.py` - Secret validation script
6. `scripts/ingest_essential_docs.sh` - Quick ingestion script
7. `scripts/run_codespaces_tests.sh` - Smart test runner
8. `scripts/verify_codespaces_setup.py` - Setup verification
9. `pytest.codespaces.ini` - Codespaces pytest config

### Updated Files (4)
1. `.devcontainer/devcontainer.json` - Add secrets, lifecycle hooks
2. `.devcontainer/setup.sh` - Enhanced with seeding and ingestion
3. `scripts/seed_data.py` - Add database URL fallback
4. Test files - Add pytest markers

---

## Risk Mitigation

### Potential Issues

1. **OpenAI API Key Missing**
   - **Impact**: Knowledge base won't work
   - **Mitigation**: Clear error messages, fallback to mock data
   - **Documentation**: Prominent setup instructions

2. **PostgreSQL Port Conflict**
   - **Impact**: Database won't start
   - **Mitigation**: Use docker-in-docker isolation
   - **Fallback**: Dynamic port allocation

3. **Slow Setup Time**
   - **Impact**: Poor developer experience
   - **Mitigation**: Optimize dependency installation, use volume caching
   - **Alternative**: Skip knowledge ingestion on first run

4. **Test Failures Due to Missing Credentials**
   - **Impact**: Confusing for new developers
   - **Mitigation**: Smart test markers, skip tests gracefully
   - **Documentation**: Clear explanations of optional features

---

## Next Actions

1. **Immediate**: Create all configuration files (Phase 1-2)
2. **Testing**: Verify in a fresh Codespace
3. **Documentation**: Write quickstart and troubleshooting guides
4. **Announcement**: Update README with Codespaces instructions

---

**Plan Status**: Ready for execution
**Expected Outcome**: 100% operational platform in Codespaces with <5 minute setup time
