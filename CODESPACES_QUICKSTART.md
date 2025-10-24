# Codespaces Quick Start Guide

**Goal**: Get the RemoteMotel platform fully operational in GitHub Codespaces
**Time**: ~30 minutes for basic setup, 5-7 days for full integration
**Outcome**: Fully functional hotel AI platform with passing tests

---

## Step 1: Access Your Codespace (2 minutes)

You should already have created your Codespace at:
**https://github.com/mahoosuc-solutions/remotemotel**

If the Codespace is running:
1. Go to GitHub repository
2. Click **Code** → **Codespaces**
3. Click on your existing Codespace name

The automatic setup should have completed with:
```
==================================
✓ Setup Complete!
==================================
```

---

## Step 2: Configure Environment (5 minutes)

### Create .env.local File

```bash
# Copy template
cp .env.example .env.local

# Edit with nano or VS Code
nano .env.local
```

### Required Configuration

**Minimum (for testing without external APIs)**:
```env
ENV=development
DATABASE_URL=postgresql://stayhive:stayhive@localhost:5433/stayhive
```

**Recommended (for full functionality)**:
```env
ENV=development
DATABASE_URL=postgresql://stayhive:stayhive@localhost:5433/stayhive
OPENAI_API_KEY=sk-your-actual-key-here
```

**Optional (for advanced features)**:
```env
# For voice calls
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_PHONE_NUMBER=+15551234567

# For payment links
STRIPE_API_KEY=sk_test_xxxx
```

**Save and exit**: `Ctrl+X`, then `Y`, then `Enter`

---

## Step 3: Verify Database (2 minutes)

```bash
# Activate virtual environment
source .venv/bin/activate

# Check PostgreSQL is running
docker compose -f docker-compose.postgres.yml ps

# Should show:
# NAME                    STATUS
# front-desk-postgres     Up X minutes

# Check tables were created
docker compose -f docker-compose.postgres.yml exec postgres psql -U stayhive -d stayhive -c "\dt"

# Should show 13 tables (9 hotel + 4 voice)
```

**Expected output**:
```
             List of relations
 Schema |         Name          | Type  |  Owner
--------+-----------------------+-------+----------
 public | bookings              | table | stayhive
 public | guests                | table | stayhive
 public | hotel_settings        | table | stayhive
 public | inventory_blocks      | table | stayhive
 public | payments              | table | stayhive
 public | rate_rules            | table | stayhive
 public | room_availability     | table | stayhive
 public | room_rates            | table | stayhive
 public | rooms                 | table | stayhive
 public | voice_analytics       | table | stayhive
 public | voice_calls           | table | stayhive
 public | voice_conversations   | table | stayhive
 public | voice_transcripts     | table | stayhive
```

---

## Step 4: Seed Database (5 minutes)

### Download seed_data.py Script

Create `scripts/seed_data.py` with the content from **INTEGRATION_PLAN.md** Phase 2, Task 2.1.

Or create it quickly:
```bash
# Copy from integration plan (search for "def seed_database")
nano scripts/seed_data.py
# Paste the full script from INTEGRATION_PLAN.md
```

### Run Seed Script

```bash
python scripts/seed_data.py
```

**Expected output**:
```
✓ Database seeded successfully!
  - Created 10 rooms
  - Created 20 rates
  - Created 900 availability records
```

### Verify Seed Data

```bash
# Check rooms
docker compose -f docker-compose.postgres.yml exec postgres psql -U stayhive -d stayhive -c "SELECT room_number, room_type, floor FROM rooms ORDER BY room_number;"

# Should show 10 rooms (101-105, 201-205)
```

---

## Step 5: Test the Platform (5 minutes)

### Test 1: Platform Validation

```bash
python test_platform.py
```

**Expected**: May show some import warnings, but should run without major errors.

### Test 2: Start FastAPI Server

```bash
# In terminal 1
python apps/operator-runtime/main.py
```

**Expected output**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Codespaces will show a notification: "Your application running on port 8000 is available."
Click **Open in Browser** or go to the **Ports** tab.

### Test 3: Health Check (in new terminal)

```bash
# Open new terminal (Ctrl+Shift+`)
curl http://localhost:8000/health
```

**Expected**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-24T...",
  "version": "1.0.0"
}
```

### Test 4: Check Availability

```bash
curl "http://localhost:8000/availability?check_in=2025-11-01&check_out=2025-11-03&adults=2&pets=false"
```

**Expected**: JSON response with available rooms and pricing.

---

## Step 6: Run Tests (5 minutes)

### Integration Tests

```bash
# Stop the server (Ctrl+C in terminal 1)

# Run integration tests
pytest tests/integration/test_hotel_system.py -v
```

**Expected**: 10+ tests pass

### Voice Tests

```bash
pytest tests/unit/voice/ -v
```

**Expected**: 70 tests pass

### All Tests

```bash
pytest tests/ -v --tb=short
```

**Expected**: Majority of tests pass

---

## Step 7: Access Web Interface (Optional)

### Option A: Port Forwarding (Automatic)

1. Start the server: `python apps/operator-runtime/main.py`
2. Click notification or go to **Ports** tab
3. Click globe icon next to port 8000
4. Opens in browser

### Option B: Manual URL

1. Go to **Ports** tab in VS Code
2. Find port 8000
3. Copy the forwarded URL (looks like: `https://xyz-8000.app.github.dev`)
4. Open in browser

### Test Endpoints in Browser

- Health: `https://your-url-8000.app.github.dev/health`
- Docs: `https://your-url-8000.app.github.dev/docs` (Swagger UI)
- Availability: `https://your-url-8000.app.github.dev/availability?check_in=2025-11-01&check_out=2025-11-03&adults=2`

---

## What's Working Now

After these steps, you should have:

✅ **Infrastructure**
- PostgreSQL running on port 5433
- 10 rooms in database
- 20 room rates configured
- 900 days of availability
- Hotel settings saved

✅ **API Endpoints**
- GET /health - Health check
- GET /availability - Check room availability (real data!)
- POST /voice/twilio/inbound - Voice call webhook

✅ **Tools**
- check_availability - Returns real room data
- create_booking - Creates bookings in database
- generate_payment_link - Generates Stripe or mock links

---

## Next Steps

### Immediate (Optional)

1. **Integrate create_lead** (see INTEGRATION_PLAN.md Phase 3)
2. **Ingest knowledge base** (needs OPENAI_API_KEY)
3. **Run all integration tests** (see INTEGRATION_PLAN.md Phase 5)

### This Week (Phase 1)

Follow **INTEGRATION_PLAN.md** to:
- Complete create_lead database integration
- Ingest 17+ documentation files
- Achieve 100% test pass rate
- Verify all endpoints working

### Next Week (Phase 2)

- Configure Twilio for voice calls
- Set up Stripe for payments
- Deploy to Cloud Run
- Beta launch!

---

## Troubleshooting

### Database Not Running

```bash
# Check status
docker compose -f docker-compose.postgres.yml ps

# Start if stopped
docker compose -f docker-compose.postgres.yml up -d

# View logs
docker compose -f docker-compose.postgres.yml logs
```

### Import Errors

```bash
# Verify PYTHONPATH
echo $PYTHONPATH
# Should show: /workspaces/remotemotel

# If not set:
export PYTHONPATH=/workspaces/remotemotel
```

### Server Won't Start

```bash
# Check if something is on port 8000
lsof -i :8000

# Kill if needed
pkill -f "python apps/operator-runtime/main.py"

# Try again
python apps/operator-runtime/main.py
```

### Tests Failing

```bash
# Run with more verbosity
pytest tests/ -v -s

# Run specific test
pytest tests/integration/test_hotel_system.py::test_name -v

# Check test database
pytest tests/ --collect-only  # See what tests exist
```

---

## Daily Workflow

Once set up, your daily workflow is:

```bash
# 1. Open Codespace
# (from GitHub web interface)

# 2. Activate environment
source .venv/bin/activate

# 3. Check database
docker compose -f docker-compose.postgres.yml ps

# 4. Start developing
code .

# 5. Run tests as you work
pytest tests/integration/ -v

# 6. Start server to test
python apps/operator-runtime/main.py

# 7. Commit changes
git add .
git commit -m "feat: your changes"
git push
```

---

## Commands Reference

### Database

```bash
# Start PostgreSQL
docker compose -f docker-compose.postgres.yml up -d

# Stop PostgreSQL
docker compose -f docker-compose.postgres.yml down

# Connect to PostgreSQL
docker compose -f docker-compose.postgres.yml exec postgres psql -U stayhive -d stayhive

# Backup database
docker compose -f docker-compose.postgres.yml exec postgres pg_dump -U stayhive stayhive > backup.sql
```

### Testing

```bash
# All tests
pytest tests/ -v

# Integration tests only
pytest tests/integration/ -v

# Voice tests only
pytest tests/unit/voice/ -v

# With coverage
pytest tests/ --cov=packages --cov-report=html

# Single test file
pytest tests/integration/test_hotel_system.py -v

# Single test
pytest tests/integration/test_hotel_system.py::test_name -v
```

### Development

```bash
# Format code
black packages/ apps/ tests/

# Lint code
ruff check packages/ apps/ tests/

# Type check
mypy packages/ apps/

# Start server
python apps/operator-runtime/main.py

# Start server with reload (development)
uvicorn apps.operator_runtime.main:app --reload
```

---

## Success Checklist

After completing this quick start:

- [ ] Codespace is running
- [ ] .env.local configured
- [ ] PostgreSQL running
- [ ] 13 tables created
- [ ] 10 rooms in database
- [ ] 20 rates configured
- [ ] 900 availability records
- [ ] Health endpoint working
- [ ] Availability endpoint returns real data
- [ ] Integration tests passing
- [ ] Voice tests passing (70/70)

**If all checked**: ✅ Platform is operational! Proceed with INTEGRATION_PLAN.md

---

## Support

- **Detailed Integration**: See [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md)
- **Deployment Guide**: See [CODESPACES_DEPLOYMENT.md](CODESPACES_DEPLOYMENT.md)
- **Platform Status**: See [PLATFORM_STATUS.md](PLATFORM_STATUS.md)
- **Full Roadmap**: See [COMPLETE_IMPLEMENTATION_ROADMAP.md](COMPLETE_IMPLEMENTATION_ROADMAP.md)

---

**You're now ready to develop and test the RemoteMotel platform!** 🎉
