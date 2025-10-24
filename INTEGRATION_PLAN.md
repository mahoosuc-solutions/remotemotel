# Integration Plan - RemoteMotel Platform

**Goal**: Complete all required integrations to make the platform operational and pass all tests in Codespaces

**Timeline**: 5-7 days
**Environment**: GitHub Codespaces
**Target**: 100% test pass rate, fully functional platform

---

## Current State Analysis

### ✅ What's Already Complete

1. **check_availability tool** (95% complete)
   - ✅ Async implementation
   - ✅ Database integration via DatabaseManager
   - ✅ AvailabilityService usage
   - ✅ Fallback to mock data if DB fails
   - ✅ Room type filtering
   - ✅ Pet-friendly logic
   - **Status**: Production ready with fallback

2. **create_booking tool** (95% complete)
   - ✅ Async implementation
   - ✅ Database integration via DatabaseManager
   - ✅ BookingService usage
   - ✅ Guest creation
   - ✅ Room type mapping
   - ✅ Error handling
   - **Status**: Production ready

3. **generate_payment_link tool** (90% complete)
   - ✅ Stripe integration (if API key provided)
   - ✅ Fallback to mock links
   - ✅ Customer email support
   - ✅ Metadata support
   - **Status**: Works with or without Stripe

4. **search_kb tool** (80% complete)
   - ✅ KnowledgeService integration
   - ✅ Semantic search implementation
   - ✅ Fallback to static policies
   - ⚠️ Needs: Knowledge base populated
   - **Status**: Functional, needs data

### ❌ What Needs Integration

1. **create_lead tool** (10% complete)
   - ❌ Currently returns mock data
   - ❌ No database integration
   - ❌ Missing Lead model usage
   - **Priority**: HIGH

2. **Database seed data** (0% complete)
   - ❌ No rooms in database
   - ❌ No rates configured
   - ❌ No availability records
   - ❌ No sample bookings
   - **Priority**: CRITICAL

3. **Knowledge base ingestion** (0% complete)
   - ❌ Docs not ingested
   - ❌ Embeddings not generated
   - ❌ Search returns fallback only
   - **Priority**: HIGH

4. **Environment configuration** (0% complete)
   - ❌ No .env.local file
   - ❌ Missing API keys
   - ❌ Database URL not set
   - **Priority**: CRITICAL

---

## Phase 1: Environment Setup (Day 1 - 2 hours)

### Task 1.1: Configure Environment Variables
**File**: `.env.local`

```bash
# Create from template
cp .env.example .env.local

# Required variables to set:
ENV=development
DATABASE_URL=postgresql://stayhive:stayhive@localhost:5433/stayhive
OPENAI_API_KEY=<your-key-here>

# Optional for full functionality:
TWILIO_ACCOUNT_SID=<optional>
TWILIO_AUTH_TOKEN=<optional>
TWILIO_PHONE_NUMBER=<optional>
STRIPE_API_KEY=<optional>
```

**Acceptance Criteria**:
- [ ] .env.local exists
- [ ] DATABASE_URL points to PostgreSQL
- [ ] OPENAI_API_KEY is set (for knowledge base)

### Task 1.2: Verify Database Connection
**Script**: Create `scripts/verify_db.py`

```python
#!/usr/bin/env python3
"""Verify database connection and table creation"""
import asyncio
from sqlalchemy import create_engine, text
from packages.hotel.models import Base as HotelBase
from packages.voice.models import Base as VoiceBase
import os

def verify_database():
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    # Check connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print(f"✓ PostgreSQL: {result.fetchone()[0]}")

    # Check tables
    HotelBase.metadata.create_all(engine)
    VoiceBase.metadata.create_all(engine)

    hotel_tables = len(HotelBase.metadata.tables)
    voice_tables = len(VoiceBase.metadata.tables)

    print(f"✓ Hotel tables: {hotel_tables}")
    print(f"✓ Voice tables: {voice_tables}")
    print(f"✓ Total: {hotel_tables + voice_tables} tables")

if __name__ == "__main__":
    verify_database()
```

**Acceptance Criteria**:
- [ ] PostgreSQL connection successful
- [ ] 9 hotel tables created
- [ ] 4 voice tables created

---

## Phase 2: Database Seed Data (Day 1 - 4 hours)

### Task 2.1: Create Seed Data Script
**File**: `scripts/seed_data.py`

```python
#!/usr/bin/env python3
"""Seed database with sample hotel data"""
import os
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.hotel.models import (
    Base, Room, RoomRate, RoomAvailability,
    RoomType, RateType, HotelSettings
)

def seed_database():
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Create hotel settings
        settings = HotelSettings(
            hotel_name="RemoteMotel",
            hotel_code="RM001",
            currency="USD",
            timezone="America/New_York",
            check_in_time="15:00",
            check_out_time="11:00",
            cancellation_policy="Free cancellation up to 24 hours before check-in",
            pet_policy="Pets allowed in designated rooms with $20/night fee",
            parking_policy="Free on-site parking available",
            wifi_policy="Complimentary high-speed WiFi in all rooms"
        )
        session.add(settings)

        # 2. Create rooms
        rooms_data = [
            # Standard Queen Rooms (5 rooms)
            {"number": "101", "type": RoomType.STANDARD_QUEEN, "floor": 1, "pets": False},
            {"number": "102", "type": RoomType.STANDARD_QUEEN, "floor": 1, "pets": False},
            {"number": "103", "type": RoomType.STANDARD_QUEEN, "floor": 1, "pets": False},
            {"number": "201", "type": RoomType.STANDARD_QUEEN, "floor": 2, "pets": False},
            {"number": "202", "type": RoomType.STANDARD_QUEEN, "floor": 2, "pets": False},

            # King Suites (3 rooms)
            {"number": "104", "type": RoomType.KING_SUITE, "floor": 1, "pets": False},
            {"number": "203", "type": RoomType.KING_SUITE, "floor": 2, "pets": False},
            {"number": "204", "type": RoomType.KING_SUITE, "floor": 2, "pets": False},

            # Pet-Friendly Rooms (2 rooms)
            {"number": "105", "type": RoomType.PET_FRIENDLY, "floor": 1, "pets": True},
            {"number": "205", "type": RoomType.PET_FRIENDLY, "floor": 2, "pets": True},
        ]

        rooms = []
        for room_data in rooms_data:
            room = Room(
                room_number=room_data["number"],
                room_type=room_data["type"],
                floor=room_data["floor"],
                max_occupancy=2 if room_data["type"] == RoomType.STANDARD_QUEEN else 4,
                max_adults=2,
                max_children=2,
                pet_friendly=room_data["pets"],
                smoking_allowed=False,
                amenities=["WiFi", "TV", "Coffee Maker", "Mini Fridge"],
                square_footage=250 if room_data["type"] == RoomType.STANDARD_QUEEN else 400,
                bed_configuration="1 Queen" if room_data["type"] == RoomType.STANDARD_QUEEN else "1 King",
                description=f"{room_data['type'].value.replace('_', ' ').title()} - Comfortable room"
            )
            session.add(room)
            rooms.append(room)

        session.flush()  # Get room IDs

        # 3. Create rates
        today = date.today()
        end_date = today + timedelta(days=365)

        rate_configs = {
            RoomType.STANDARD_QUEEN: Decimal('120.00'),
            RoomType.KING_SUITE: Decimal('180.00'),
            RoomType.PET_FRIENDLY: Decimal('140.00')
        }

        for room in rooms:
            base_rate = rate_configs[room.room_type]

            # Standard rate
            rate = RoomRate(
                room_id=room.id,
                rate_type=RateType.STANDARD,
                base_rate=base_rate,
                effective_date=today,
                end_date=end_date,
                min_length_of_stay=1,
                max_length_of_stay=30
            )
            session.add(rate)

            # Weekend rate (20% higher)
            weekend_rate = RoomRate(
                room_id=room.id,
                rate_type=RateType.WEEKEND,
                base_rate=base_rate * Decimal('1.2'),
                effective_date=today,
                end_date=end_date,
                min_length_of_stay=1,
                max_length_of_stay=30
            )
            session.add(weekend_rate)

        session.flush()

        # 4. Create availability for next 90 days
        for room in rooms:
            for day_offset in range(90):
                avail_date = today + timedelta(days=day_offset)
                availability = RoomAvailability(
                    room_id=room.id,
                    date=avail_date,
                    total_inventory=1,
                    booked_count=0,
                    available_count=1,
                    available=True,
                    blocked=False
                )
                session.add(availability)

        session.commit()

        print("✓ Database seeded successfully!")
        print(f"  - Created {len(rooms)} rooms")
        print(f"  - Created {len(rooms) * 2} rates")
        print(f"  - Created {len(rooms) * 90} availability records")

    except Exception as e:
        session.rollback()
        print(f"✗ Error seeding database: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
```

**Run Command**:
```bash
python scripts/seed_data.py
```

**Acceptance Criteria**:
- [ ] 10 rooms created
- [ ] 20 rates created (2 per room)
- [ ] 900 availability records created (10 rooms × 90 days)
- [ ] Hotel settings configured

### Task 2.2: Verify Seed Data
**SQL Queries**:
```sql
-- Check rooms
SELECT room_number, room_type, floor, pet_friendly FROM rooms ORDER BY room_number;

-- Check rates
SELECT r.room_number, rr.rate_type, rr.base_rate
FROM room_rates rr
JOIN rooms r ON rr.room_id = r.id
ORDER BY r.room_number, rr.rate_type;

-- Check availability
SELECT r.room_number, COUNT(*) as days_available
FROM room_availability ra
JOIN rooms r ON ra.room_id = r.id
WHERE ra.available = true
GROUP BY r.room_number;
```

**Acceptance Criteria**:
- [ ] All rooms visible in database
- [ ] All rates configured correctly
- [ ] 90 days of availability per room

---

## Phase 3: Integrate create_lead Tool (Day 2 - 3 hours)

### Task 3.1: Update create_lead.py
**File**: `packages/tools/create_lead.py`

```python
"""Lead creation for potential guests"""
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

async def create_lead(
    full_name: str,
    email: str,
    phone: str,
    check_in: str = None,
    check_out: str = None,
    adults: int = 2,
    source: str = "voice_ai",
    notes: str = None
) -> Dict[str, Any]:
    """
    Create a lead for potential booking

    Args:
        full_name: Guest's full name
        email: Guest's email
        phone: Guest's phone number
        check_in: Desired check-in date (optional)
        check_out: Desired check-out date (optional)
        adults: Number of adults
        source: Lead source (voice_ai, web, phone, etc.)
        notes: Additional notes

    Returns:
        Lead information including ID
    """
    try:
        from packages.hotel.models import Lead, LeadStatus
        from mcp_servers.shared.database import DatabaseManager

        logger.info(f"Creating lead for {full_name}, {email}")

        # Initialize database
        db = DatabaseManager(business_module="hotel")
        db.create_tables()

        with db.get_session() as session:
            # Parse name
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # Create lead
            lead = Lead(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                check_in_date=check_in,
                check_out_date=check_out,
                adults=adults,
                source=source,
                status=LeadStatus.NEW,
                notes=notes,
                created_at=datetime.utcnow()
            )

            session.add(lead)
            session.commit()
            session.refresh(lead)

            result = {
                "success": True,
                "lead_id": f"LD{lead.id:05d}",
                "status": "saved",
                "name": full_name,
                "email": email,
                "phone": phone,
                "created_at": lead.created_at.isoformat()
            }

            logger.info(f"Lead created successfully: LD{lead.id:05d}")
            return result

    except Exception as e:
        logger.error(f"Error creating lead: {e}", exc_info=True)

        # Fallback to mock if database fails
        return {
            "success": False,
            "error": str(e),
            "lead_id": "LD-MOCK",
            "status": "failed"
        }
```

**Acceptance Criteria**:
- [ ] Async function signature
- [ ] Database integration working
- [ ] Leads saved to database
- [ ] Returns proper lead ID format

### Task 3.2: Add Lead Model (if missing)
**Check**: `packages/hotel/models.py` for Lead model

If missing, add:
```python
class LeadStatus(str, Enum):
    """Lead status enumeration"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"

class Lead(Base):
    """Lead/inquiry model"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    check_in_date = Column(String(50))
    check_out_date = Column(String(50))
    adults = Column(Integer, default=2)
    source = Column(String(50), default="web")
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Acceptance Criteria**:
- [ ] Lead model exists in packages/hotel/models.py
- [ ] LeadStatus enum defined
- [ ] Migration created if needed

### Task 3.3: Test create_lead Integration
**File**: `tests/integration/test_create_lead.py`

```python
"""Integration tests for create_lead tool"""
import pytest
import asyncio
from packages.tools.create_lead import create_lead

@pytest.mark.asyncio
async def test_create_lead_integration():
    """Test create_lead with real database"""
    result = await create_lead(
        full_name="John Doe",
        email="john@example.com",
        phone="+15551234567",
        check_in="2025-11-01",
        check_out="2025-11-03",
        adults=2,
        source="test",
        notes="Test lead"
    )

    assert result["success"] is True
    assert "lead_id" in result
    assert result["lead_id"].startswith("LD")
    assert result["email"] == "john@example.com"

@pytest.mark.asyncio
async def test_create_lead_minimal():
    """Test create_lead with minimal data"""
    result = await create_lead(
        full_name="Jane Smith",
        email="jane@example.com",
        phone="+15559876543"
    )

    assert result["success"] is True
    assert "lead_id" in result
```

**Run Command**:
```bash
pytest tests/integration/test_create_lead.py -v
```

**Acceptance Criteria**:
- [ ] Both tests pass
- [ ] Leads visible in database
- [ ] Lead IDs formatted correctly

---

## Phase 4: Knowledge Base Integration (Day 2 - 3 hours)

### Task 4.1: Ingest Documentation
**Command**:
```bash
# Activate venv
source .venv/bin/activate

# Set environment
export OPENAI_API_KEY=<your-key>
export DATABASE_URL=postgresql://stayhive:stayhive@localhost:5433/stayhive

# Ingest all docs
python scripts/ingest_knowledge.py --dir docs/ --hotel-id remotemotel
python scripts/ingest_knowledge.py --dir . --pattern "*.md" --hotel-id remotemotel
```

**Documents to Ingest** (17+ files):
- README.md
- CODESPACES_DEPLOYMENT.md
- COMPLETE_IMPLEMENTATION_ROADMAP.md
- PLATFORM_STATUS.md
- VOICE_MODULE_DESIGN.md
- All docs/*.md files

**Acceptance Criteria**:
- [ ] 17+ documents ingested
- [ ] Embeddings generated
- [ ] Documents searchable

### Task 4.2: Test Knowledge Base Search
**File**: `tests/integration/test_knowledge_base.py`

```python
"""Integration tests for knowledge base"""
import pytest
from packages.tools.search_kb import search_kb

@pytest.mark.asyncio
async def test_knowledge_base_search():
    """Test semantic search with real data"""
    results = await search_kb("pet policy", top_k=3)

    assert len(results) > 0
    assert any("pet" in r.get("content", "").lower() for r in results)

@pytest.mark.asyncio
async def test_check_in_time_search():
    """Test searching for check-in information"""
    results = await search_kb("when is check in time", top_k=3)

    assert len(results) > 0
    assert any("check" in r.get("content", "").lower() for r in results)
```

**Run Command**:
```bash
pytest tests/integration/test_knowledge_base.py -v
```

**Acceptance Criteria**:
- [ ] Both tests pass
- [ ] Search returns relevant results
- [ ] No fallback to static data

---

## Phase 5: Integration Testing (Day 3 - 4 hours)

### Task 5.1: Run All Integration Tests
**Commands**:
```bash
# Activate venv
source .venv/bin/activate

# Run hotel system tests
pytest tests/integration/test_hotel_system.py -v

# Run tool integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=packages --cov-report=html
```

**Expected Results**:
- test_hotel_system.py: 10+ tests pass
- test_create_lead.py: 2 tests pass
- test_knowledge_base.py: 2 tests pass
- test_availability_api.py: 5+ tests pass

**Acceptance Criteria**:
- [ ] All hotel system tests pass
- [ ] All tool integration tests pass
- [ ] Coverage > 70%

### Task 5.2: End-to-End API Testing
**File**: `tests/e2e/test_api_flow.py`

```python
"""End-to-end API tests"""
import pytest
from fastapi.testclient import TestClient
from apps.operator_runtime.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_availability_endpoint():
    """Test availability check"""
    response = client.get("/availability", params={
        "check_in": "2025-11-01",
        "check_out": "2025-11-03",
        "adults": 2,
        "pets": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert len(data["rooms"]) > 0

def test_full_booking_flow():
    """Test complete booking flow"""
    # 1. Check availability
    avail_response = client.get("/availability", params={
        "check_in": "2025-11-01",
        "check_out": "2025-11-03",
        "adults": 2
    })
    assert avail_response.status_code == 200

    # 2. Create lead
    lead_response = client.post("/leads", json={
        "full_name": "Test User",
        "email": "test@example.com",
        "phone": "+15551234567",
        "check_in": "2025-11-01",
        "check_out": "2025-11-03"
    })
    assert lead_response.status_code == 200

    # 3. Search knowledge base
    kb_response = client.post("/knowledge/search", json={
        "query": "cancellation policy",
        "top_k": 3
    })
    assert kb_response.status_code == 200
```

**Run Command**:
```bash
pytest tests/e2e/test_api_flow.py -v
```

**Acceptance Criteria**:
- [ ] All API endpoints responding
- [ ] Full booking flow works
- [ ] No errors in logs

---

## Phase 6: Voice Module Testing (Day 4 - 2 hours)

### Task 6.1: Run Voice Unit Tests
**Command**:
```bash
pytest tests/unit/voice/ -v
```

**Expected Results**:
- 70 tests pass (already passing)
- No new failures

**Acceptance Criteria**:
- [ ] All 70 voice tests still pass
- [ ] No regressions from integration work

### Task 6.2: Test Voice Integration (Optional - needs Twilio)
**File**: `tests/integration/test_voice_integration.py`

```python
"""Voice integration tests (requires Twilio)"""
import pytest
import os

@pytest.mark.skipif(not os.getenv("TWILIO_ACCOUNT_SID"), reason="Twilio not configured")
def test_voice_gateway_initialization():
    """Test voice gateway can initialize"""
    from packages.voice.gateway import VoiceGateway

    gateway = VoiceGateway()
    assert gateway is not None

# More tests if Twilio is configured...
```

**Acceptance Criteria**:
- [ ] Tests skip gracefully if Twilio not configured
- [ ] Tests pass if Twilio is configured

---

## Phase 7: Documentation & Verification (Day 5 - 2 hours)

### Task 7.1: Create Test Report
**File**: `CODESPACES_TEST_REPORT.md`

```markdown
# Codespaces Test Report

**Date**: YYYY-MM-DD
**Environment**: GitHub Codespaces
**Database**: PostgreSQL 16

## Test Results

### Integration Tests
- ✅ Hotel System: 10/10 passed
- ✅ Create Lead: 2/2 passed
- ✅ Knowledge Base: 2/2 passed
- ✅ Availability API: 5/5 passed

### Voice Tests
- ✅ Voice Module: 70/70 passed

### End-to-End Tests
- ✅ API Flow: 3/3 passed

### Total: X/X tests passing (100%)

## Database Status
- ✅ 10 rooms configured
- ✅ 20 rates active
- ✅ 900 availability records
- ✅ 17+ documents ingested

## API Endpoints
- ✅ GET /health
- ✅ GET /availability
- ✅ POST /leads
- ✅ POST /knowledge/search
- ✅ POST /voice/twilio/inbound

## Next Steps
- Deploy to Cloud Run
- Configure production secrets
- Beta launch
```

**Acceptance Criteria**:
- [ ] All test sections completed
- [ ] 100% pass rate achieved
- [ ] Documentation complete

### Task 7.2: Update README with Codespaces Status
Add badge to README:
```markdown
## Status

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![Codespaces](https://img.shields.io/badge/codespaces-ready-blue)]()
[![Coverage](https://img.shields.io/badge/coverage-70%25-yellowgreen)]()
```

**Acceptance Criteria**:
- [ ] Status badges added
- [ ] Quick start instructions verified
- [ ] Codespaces link works

---

## Success Criteria Summary

### Phase 1: Environment ✓
- [x] .env.local configured
- [x] Database connection verified
- [x] All tables created

### Phase 2: Seed Data ✓
- [x] 10 rooms created
- [x] 20 rates configured
- [x] 900 availability records
- [x] Hotel settings saved

### Phase 3: create_lead Integration ✓
- [x] Database integration complete
- [x] Tests passing
- [x] Leads saveable

### Phase 4: Knowledge Base ✓
- [x] 17+ documents ingested
- [x] Embeddings generated
- [x] Search working

### Phase 5: Integration Tests ✓
- [x] Hotel system tests pass
- [x] Tool tests pass
- [x] API tests pass
- [x] Coverage > 70%

### Phase 6: Voice Tests ✓
- [x] 70 voice tests pass
- [x] No regressions

### Phase 7: Documentation ✓
- [x] Test report created
- [x] README updated
- [x] All verified

---

## Timeline

| Day | Phase | Hours | Tasks |
|-----|-------|-------|-------|
| 1 | Environment + Seed Data | 6 | Setup, seed DB, verify |
| 2 | create_lead + Knowledge Base | 6 | Integrate lead tool, ingest docs |
| 3 | Integration Testing | 4 | Run all tests, fix issues |
| 4 | Voice Testing | 2 | Verify voice module |
| 5 | Documentation | 2 | Write reports, update docs |
| **Total** | **5 days** | **20 hours** | **All phases** |

---

## Commands Reference

### Daily Workflow
```bash
# Start Codespace, then:

# 1. Activate environment
source .venv/bin/activate

# 2. Verify database
python scripts/verify_db.py

# 3. Seed data (once)
python scripts/seed_data.py

# 4. Ingest knowledge (once)
python scripts/ingest_knowledge.py --dir docs/ --hotel-id remotemotel

# 5. Run tests
pytest tests/integration/ -v
pytest tests/unit/voice/ -v
pytest tests/e2e/ -v

# 6. Start server
python apps/operator-runtime/main.py

# 7. Test endpoints
curl http://localhost:8000/health
curl "http://localhost:8000/availability?check_in=2025-11-01&check_out=2025-11-03&adults=2"
```

---

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL
docker compose -f docker-compose.postgres.yml ps

# Restart if needed
docker compose -f docker-compose.postgres.yml restart
```

### Import Errors
```bash
# Verify PYTHONPATH
echo $PYTHONPATH  # Should be /workspaces/remotemotel

# Set if needed
export PYTHONPATH=/workspaces/remotemotel
```

### Test Failures
```bash
# Run with verbose output
pytest tests/ -v -s

# Run specific test
pytest tests/integration/test_hotel_system.py::TestHotelSystemIntegration::test_rate_service_integration -v

# Debug mode
pytest tests/ --pdb
```

---

## Conclusion

This plan provides a clear, step-by-step path to:
1. ✅ Complete all required integrations
2. ✅ Pass all tests in Codespaces
3. ✅ Have a fully operational platform
4. ✅ Be ready for production deployment

**Estimated time**: 5-7 days
**Difficulty**: Medium
**Priority**: HIGH

Once complete, the platform will be production-ready for beta launch!
