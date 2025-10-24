# GitHub Codespaces Quickstart

Get the RemoteMotel platform running in GitHub Codespaces in under 5 minutes.

## Prerequisites

1. **GitHub Account** with Codespaces enabled
2. **OpenAI API Key** (required for knowledge base)
   - Get one at: https://platform.openai.com/api-keys
3. **Optional**: Twilio and Stripe credentials for full testing

## Setup Steps

### Step 1: Configure Secrets (One-time setup)

1. Go to: `https://github.com/YOUR_ORG/front-desk/settings/secrets/codespaces`
2. Add `OPENAI_API_KEY` secret with your OpenAI key
3. (Optional) Add `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`
4. (Optional) Add `STRIPE_API_KEY`

See [CODESPACES_SECRETS.md](CODESPACES_SECRETS.md) for detailed instructions.

### Step 2: Create Codespace

1. Go to: `https://github.com/YOUR_ORG/front-desk`
2. Click green "Code" button
3. Select "Codespaces" tab
4. Click "Create codespace on main"

**Wait 3-5 minutes** for automatic setup:
- Python environment configured
- PostgreSQL container started
- Database migrated and seeded
- Knowledge base ingested (if OpenAI key set)

### Step 3: Verify Setup

```bash
# Check secrets
python scripts/validate_secrets.py

# Verify database
docker compose -f docker-compose.postgres.yml exec postgres psql -U stayhive -d stayhive -c "SELECT COUNT(*) FROM rooms;"

# Run verification script
python scripts/verify_codespaces_setup.py
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

### Run Smart Test Runner (Skips unavailable services)

```bash
./scripts/run_codespaces_tests.sh
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

### Fully Functional

- Hotel management (rooms, rates, availability, bookings)
- Knowledge base with semantic search
- Lead capture and management
- Database operations
- All API endpoints

### Requires Configuration

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

- **Issues**: https://github.com/YOUR_ORG/front-desk/issues
- **Discussions**: https://github.com/YOUR_ORG/front-desk/discussions
- **Secrets Setup**: [CODESPACES_SECRETS.md](CODESPACES_SECRETS.md)
- **Integration Plan**: [CODESPACES_INTEGRATION_PLAN.md](CODESPACES_INTEGRATION_PLAN.md)

---

**You're now ready to develop and test the RemoteMotel platform!**
