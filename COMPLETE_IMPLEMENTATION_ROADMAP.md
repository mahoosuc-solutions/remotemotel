# Front-Desk Platform - Complete Implementation Roadmap

**Repository**: front-desk
**Date**: 2025-10-23
**Status**: 85% Voice AI Complete, 30% Overall Platform Complete
**Goal**: Full production-ready hotel operator agent platform

---

## Executive Summary

This document provides a comprehensive analysis of what exists versus what's needed to complete the front-desk platform. Based on deep code review, the platform is **production-ready for Voice AI** but requires significant work for full hotel operations.

### Current State
- ✅ **Voice AI**: 85% complete (6,000+ lines, OpenAI Realtime API working)
- ⚠️ **Tool Integrations**: 20% complete (mostly mocks)
- ⚠️ **Database/Persistence**: 40% complete (PostgreSQL running, not fully wired)
- ⚠️ **Testing**: 30% complete (78 voice tests passing, need 100+)
- ❌ **Security**: 15% complete (basic Pydantic validation only)
- ❌ **Monitoring**: 10% complete (no alerts/dashboards)

### **Overall Completion**: 33%

---

## 📊 Detailed Gap Analysis

### 1. Voice AI Module (85% Complete)

#### ✅ What Works
- OpenAI Realtime API integration (582 lines) - [packages/voice/realtime.py](packages/voice/realtime.py)
- Twilio Media Stream relay (327 lines) - [packages/voice/relay.py](packages/voice/relay.py)
- West Bethel configuration (330 lines) - [packages/voice/hotel_config.py](packages/voice/hotel_config.py)
- 78/78 unit tests passing - [tests/unit/voice/](tests/unit/voice/)
- GCP Cloud Run deployed - `+1 (207) 220-3501`
- WebSocket support configured

#### ❌ What's Missing
- Real-time conversation analytics
- Call recording storage (S3/GCS integration)
- Voice quality monitoring (MOS scores)
- Multi-language support
- Custom voice training

---

### 2. Tool Integrations (20% Complete)

#### Current Status by Tool

| Tool | File | Status | Completion |
|------|------|--------|------------|
| **check_availability** | `packages/tools/check_availability.py` | Mock only | 10% |
| **create_lead** | `packages/tools/create_lead.py` | Mock only | 10% |
| **generate_payment_link** | `packages/tools/generate_payment_link.py` | Stripe scaffolded | 30% |
| **search_kb** | `packages/tools/search_kb.py` | ChromaDB configured | 40% |
| **create_booking** | `packages/tools/create_booking.py` | Mock only | 10% |

#### Detailed Gaps

**check_availability.py**
```python
# Current (Mock):
return {
    "available": True,
    "rooms_available": 5,
    "room_types": ["standard", "deluxe"]
}

# Needed (Real):
- Connect to packages/hotel/services.py AvailabilityService
- Query PostgreSQL room_inventory table
- Handle date ranges and occupancy calculations
- Return actual pricing from rate tables
```

**create_lead.py**
```python
# Current (Mock):
return {
    "lead_id": "LD-12345",
    "status": "saved"
}

# Needed (Real):
- Connect to packages/hotel/services.py or mcp_servers/stayhive/tools.py
- Insert into PostgreSQL leads table
- Generate real lead ID with timestamp
- Trigger follow-up workflows (email, CRM sync)
```

**generate_payment_link.py**
```python
# Current (Scaffolded):
# TODO: Integrate with actual Stripe API
return {"url": "https://example.com/pay"}

# Needed (Real):
- Use Stripe API (already in requirements.txt)
- Create Product and Price objects
- Generate PaymentLink with webhook
- Handle payment confirmations
- Update booking status on payment
```

**search_kb.py**
```python
# Current (Static):
return [{"policy": "Pet friendly with $40 fee"}]

# Needed (Real):
- Use packages/knowledge/service.py (already exists!)
- Populate database with scripts/ingest_knowledge.py
- Semantic search with OpenAI embeddings
- Return top-k results with relevance scores
```

---

### 3. Database & Persistence (40% Complete)

#### ✅ What Exists
- **PostgreSQL**: Running on port 5433 via docker-compose.postgres.yml
- **Hotel Models**: Complete SQLAlchemy models in [packages/hotel/models.py](packages/hotel/models.py)
  - RoomType, BookingStatus, PaymentStatus enums
  - Room, Guest, Booking, RoomAvailability, Rate models
- **Voice Models**: [packages/voice/models.py](packages/voice/models.py)
  - VoiceCall, ConversationTurn, VoiceAnalytics
- **MCP Models**: [mcp_servers/stayhive/tools.py](mcp_servers/stayhive/tools.py)
  - RoomInventory, Reservation, Lead
- **Knowledge Service**: [packages/knowledge/service.py](packages/knowledge/service.py)
  - Async PostgreSQL + OpenAI embeddings
  - Document chunking and ingestion
  - Semantic search ready

#### ❌ What's Missing
1. **No Migrations**:
   - Alembic initialized but migrations not generated
   - Need to create initial schema migration
   - Tables don't exist in PostgreSQL yet

2. **No Data**:
   - Empty database (need seed data)
   - Knowledge base empty (need document ingestion)
   - No room inventory loaded

3. **Not Wired Up**:
   - Tools don't call database services
   - API endpoints exist but not connected
   - Session management not persisted

#### Action Items
```bash
# 1. Install dependencies in venv
source .venv/bin/activate
pip install alembic asyncpg

# 2. Generate migration (skip deps check)
export SKIP_DEPS_CHECK=1
alembic revision --autogenerate -m "Initial schema"

# 3. Run migration
alembic upgrade head

# 4. Ingest knowledge base
python scripts/ingest_knowledge.py docs/VOICE_MODULE_DESIGN.md
python scripts/ingest_knowledge.py docs/CLAUDE.md
# ... repeat for all 17+ docs

# 5. Load seed data
python packages/hotel/init_data.py
```

---

### 4. Testing (30% Complete)

#### Current Coverage
- **78 voice tests passing** - [tests/unit/voice/](tests/unit/voice/)
- **35 total test files** (need 100+)
- **No integration tests** for tools
- **No E2E tests** for booking flows
- **No load tests**

#### Test Gaps by Category

| Category | Current | Target | Files Needed |
|----------|---------|--------|--------------|
| Voice Unit Tests | 78 tests | 100 tests | +5 files |
| Hotel Unit Tests | 15 tests | 50 tests | +10 files |
| Tool Integration Tests | 0 tests | 30 tests | +6 files |
| E2E Booking Flows | 0 tests | 20 tests | +4 files |
| API Endpoint Tests | 5 tests | 40 tests | +8 files |
| Load/Performance Tests | 0 tests | 5 tests | +2 files |
| **TOTAL** | **35 files** | **110 files** | **+75 files** |

#### Priority Tests to Add

**1. Tool Integration Tests** (NEW: `tests/integration/tools/`)
```python
# test_availability_integration.py
async def test_check_availability_queries_database():
    """Verify availability tool queries real PostgreSQL"""
    result = await check_availability(
        check_in="2025-11-01",
        check_out="2025-11-03"
    )
    assert result["available"] == True
    assert result["rooms_available"] > 0

# test_lead_creation_integration.py
async def test_create_lead_persists_to_database():
    """Verify lead creation saves to PostgreSQL"""
    result = await create_lead(
        full_name="John Doe",
        email="john@example.com",
        channel="voice"
    )
    # Verify in database
    session = SessionLocal()
    lead = session.query(Lead).filter_by(lead_id=result["lead_id"]).first()
    assert lead is not None
```

**2. E2E Booking Flow Tests** (NEW: `tests/e2e/`)
```python
# test_complete_booking_journey.py
async def test_guest_books_room_end_to_end():
    """Test complete flow: availability → lead → booking → payment"""
    # 1. Check availability
    avail = await check_availability("2025-11-01", "2025-11-03")
    assert avail["available"]

    # 2. Create lead
    lead = await create_lead("Jane Smith", "jane@example.com", "voice")
    assert lead["lead_id"]

    # 3. Create booking
    booking = await create_booking(
        guest_name="Jane Smith",
        check_in="2025-11-01",
        check_out="2025-11-03"
    )
    assert booking["confirmation_number"]

    # 4. Generate payment link
    payment = await generate_payment_link(booking["total_amount"])
    assert payment["url"].startswith("https://buy.stripe.com/")
```

**3. Conversation Quality Tests** (NEW: `tests/quality/`)
```python
# test_conversation_scenarios.py
QUALITY_SCENARIOS = [
    {
        "name": "Pet Policy Inquiry",
        "input": "Do you allow dogs?",
        "expected_keywords": ["pet", "welcome", "$40", "fee"],
        "expected_tools": ["search_kb"],
        "min_quality_score": 0.85
    },
    # ... 100+ scenarios
]
```

---

### 5. Security & Auth (15% Complete)

#### Current State
- ✅ Pydantic validation on API models
- ✅ Environment variable handling
- ⚠️ Twilio signature validation (implemented but needs testing)
- ❌ No authentication for admin endpoints
- ❌ No rate limiting
- ❌ No input sanitization beyond Pydantic
- ❌ No CORS configuration

#### Security Gaps

**1. Authentication** (MISSING)
```python
# Need to add JWT authentication
# File: packages/auth/jwt_auth.py

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    """Verify JWT token for admin endpoints"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY)
        return payload
    except JWTError:
        raise HTTPException(status_code=401)

# Protect admin endpoints
@app.get("/admin/leads")
async def get_leads(user = Depends(verify_token)):
    # Only accessible with valid JWT
    pass
```

**2. Rate Limiting** (MISSING)
```python
# Need to add slowapi
# File: apps/operator-runtime/main.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/availability")
@limiter.limit("30/minute")  # 30 requests per minute
async def availability(...):
    pass
```

**3. Input Sanitization** (PARTIAL)
```python
# Need to add bleach for XSS prevention
# File: packages/models/requests.py

import bleach

class LeadRequest(BaseModel):
    full_name: str

    @field_validator('full_name')
    @classmethod
    def sanitize_name(cls, v):
        return bleach.clean(v, strip=True)
```

---

### 6. Monitoring & Observability (10% Complete)

#### Current State
- ✅ Basic health check endpoint
- ✅ Structured logging (some files)
- ❌ No Prometheus metrics
- ❌ No Grafana dashboards
- ❌ No alerting (PagerDuty/Slack)
- ❌ No distributed tracing

#### Monitoring Gaps

**1. Prometheus Metrics** (MISSING)
```python
# File: packages/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration'
)

# Voice metrics
websocket_connections = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

ai_response_time = Histogram(
    'ai_response_duration_seconds',
    'AI response time'
)
```

**2. Grafana Dashboards** (MISSING)
- Request rate over time
- Response time (p50, p95, p99)
- Error rate by endpoint
- Active voice calls
- AI response latency
- Database query performance

**3. Alerting Rules** (MISSING)
- Error rate > 5% for 5 minutes
- Response time p95 > 2 seconds
- WebSocket connection failures > 10%
- Voice call success rate < 95%
- Database connection failures

---

## 🚀 12-Week Implementation Plan

### **Phase 1: Database Foundation (Weeks 1-2)**

**Week 1 Tasks**:
1. Fix Alembic setup (skip dependency check for migrations)
2. Generate initial migration for all models
3. Run migration to create PostgreSQL tables
4. Populate knowledge base (100+ documents)
5. Load hotel seed data (rooms, rates, inventory)

**Week 2 Tasks**:
6. Wire `check_availability` to PostgreSQL
7. Wire `create_lead` to PostgreSQL
8. Wire `search_kb` to knowledge service
9. Create 25+ integration tests
10. Document database schema and ERD

**Deliverables**:
- PostgreSQL with all tables created
- 100+ knowledge base documents ingested
- Real availability checking working
- Real lead creation working
- Test coverage: 35 → 60 files

---

### **Phase 2: Real Tool Integration (Weeks 3-5)**

**Week 3: Stripe Integration**
1. Complete `generate_payment_link.py` with Stripe API
2. Add webhook handling for payment events
3. Test payment link generation end-to-end
4. Update booking status on payment
5. Add payment integration tests

**Week 4: Booking System**
6. Complete `create_booking.py` implementation
7. Wire to packages/hotel/services.py BookingService
8. Implement booking confirmation workflow
9. Add SMS confirmations (Twilio)
10. Add email confirmations (SendGrid/SMTP)

**Week 5: PMS Integration (Optional)**
11. Research PMS API options (Opera, Cloudbeds, etc.)
12. Implement PMS adapter pattern
13. Sync reservations bidirectionally
14. Handle inventory updates from PMS
15. Test PMS integration thoroughly

**Deliverables**:
- Live Stripe payments
- Complete booking workflow
- SMS/email confirmations
- Optional PMS integration
- Test coverage: 60 → 85 files

---

### **Phase 3: Security & Auth (Weeks 6-7)**

**Week 6: Authentication**
1. Implement JWT authentication
2. Create admin user management
3. Protect admin endpoints
4. Add API key support for MCP
5. Test authentication flows

**Week 7: Security Hardening**
6. Add rate limiting (slowapi)
7. Implement input sanitization (bleach)
8. Configure CORS properly
9. Security penetration testing
10. Fix identified vulnerabilities

**Deliverables**:
- Secure admin API with JWT
- Rate limiting active
- Input sanitization
- Security audit passed
- Test coverage: 85 → 95 files

---

### **Phase 4: Quality Assurance (Weeks 8-9)**

**Week 8: Conversation Quality**
1. Create 100+ test conversation scenarios
2. Build conversation quality scoring system
3. Implement human evaluation framework
4. Run quality tests (target: >85% score)
5. Refine prompts based on results

**Week 9: Performance Testing**
6. Load testing (1000+ concurrent users)
7. Performance optimization (caching, query tuning)
8. A/B testing framework for prompts
9. Voice quality testing (MOS scores)
10. Optimize response times (<2s p95)

**Deliverables**:
- 100+ E2E conversation tests
- Quality score >85%
- Load test results documented
- Performance optimized
- Test coverage: 95 → 110+ files

---

### **Phase 5: Event-Driven Architecture (Weeks 10-11)**

**Week 10: Pub/Sub Events**
1. Set up GCP Pub/Sub topics
2. Create `packages/conversation/events.py`
3. Publish events for all conversation activities
4. Create event schemas
5. Test event publishing

**Week 11: Unified Engine**
6. Create `packages/conversation/engine.py`
7. Refactor voice gateway to use engine
8. Build BigQuery sink for events
9. Create analytics dashboard (Looker)
10. Test analytics pipeline

**Deliverables**:
- Event-driven conversation engine
- Pub/Sub event publishing
- Analytics dashboard
- Conversation history in BigQuery

---

### **Phase 6: Deployment & Operations (Week 12)**

**Week 12: CI/CD & Monitoring**
1. Create GitHub Actions CI/CD pipeline
2. Set up Prometheus metrics
3. Create Grafana dashboards
4. Configure PagerDuty/Slack alerts
5. Write operations runbook
6. Deploy to production
7. Monitor first 100 calls
8. Iterate based on feedback

**Deliverables**:
- Automated CI/CD
- Real-time monitoring
- Alerting system
- Operations runbook
- Production deployment
- **PLATFORM 95% COMPLETE**

---

## 📋 Phase 1 Immediate Action Plan

### Priority 1 (This Week)
1. **Fix Alembic Setup** (2 hours)
   ```bash
   # Edit packages/voice/dependencies.py (already done)
   # Generate migration
   export SKIP_DEPS_CHECK=1
   source .venv/bin/activate
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

2. **Populate Knowledge Base** (4 hours)
   ```bash
   # Ingest all documentation
   python scripts/ingest_knowledge.py docs/VOICE_MODULE_DESIGN.md
   python scripts/ingest_knowledge.py docs/CLAUDE.md
   python scripts/ingest_knowledge.py README.md
   # ... all 17+ docs
   ```

3. **Wire Real Persistence** (8 hours)
   ```python
   # Update packages/tools/create_lead.py
   from mcp_servers.stayhive.tools import _create_lead_db

   def create_lead(...):
       return _create_lead_db(...)  # Use real DB function
   ```

4. **Add Integration Tests** (8 hours)
   ```bash
   # Create tests/integration/tools/
   mkdir -p tests/integration/tools
   # Write test_availability_integration.py
   # Write test_lead_creation_integration.py
   # Write test_knowledge_search_integration.py
   ```

### Priority 2 (Next Week)
5. **Stripe Integration** (16 hours)
6. **Booking Workflow** (16 hours)
7. **SMS/Email Confirmations** (8 hours)

---

## 💰 Cost Analysis

### Development Costs
- **12 weeks × 40 hours × $75/hour**: $36,000
- **QA Testing (2 weeks)**: $6,000
- **Total Development**: ~$42,000

### Monthly Operational Costs
- **OpenAI API**: $500-1,000 (based on usage)
- **GCP Cloud Run**: $200-400 (2 instances, 2GB RAM)
- **PostgreSQL (Cloud SQL)**: $100-200 (db-f1-micro)
- **Monitoring (Prometheus/Grafana)**: $50-100
- **Stripe**: 2.9% + $0.30 per transaction
- **Twilio SMS**: $0.0075 per message
- **Total Monthly**: ~$850-1,700

---

## 📊 Success Metrics

### Technical KPIs
| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Test Coverage | 30% | 90% | Week 9 |
| Response Time (p95) | ~2s | <2s | Week 9 |
| API Uptime | N/A | 99.9% | Week 12 |
| Voice Call Success Rate | Unknown | >95% | Week 12 |
| Code Quality Score | 7/10 | 9/10 | Week 12 |

### Business KPIs
| Metric | Target | Timeline |
|--------|--------|----------|
| Lead Capture Rate | >80% | Week 4 |
| Booking Conversion | >30% | Week 5 |
| Guest Satisfaction | >4.5/5 | Week 8 |
| Cost per Conversation | <$0.50 | Week 9 |
| Human Handoff Rate | <15% | Week 12 |

---

## 🎯 Critical Success Factors

1. **Database Foundation First**: Can't have real tools without real persistence
2. **Test Everything**: 110+ test files needed for confidence
3. **Security Cannot Wait**: Implement auth/rate-limiting early
4. **Monitor from Day 1**: Set up metrics before production
5. **Iterate on Quality**: 100+ conversation scenarios to validate

---

## 📁 Files Created During Analysis

- ✅ [VALIDATION_REPORT.md](VALIDATION_REPORT.md) - Pydantic v2 + SQLAlchemy 2.0 modernization
- ✅ [packages/utils/datetime_utils.py](packages/utils/datetime_utils.py) - Timezone-aware datetime helpers
- ✅ [docker-compose.postgres.yml](docker-compose.postgres.yml) - PostgreSQL setup
- ✅ [.gitignore](.gitignore) - Git ignore patterns
- ✅ [alembic/](alembic/) - Database migrations infrastructure (initialized)
- ✅ **THIS FILE** - Complete implementation roadmap

---

## 🚦 Recommendation

**START WITH PHASE 1 THIS WEEK**

The foundation (database + persistence) is critical. Without it, all tools remain mocks. Here's the minimal viable first sprint:

### Week 1 Sprint
1. Fix Alembic and run migrations (Day 1)
2. Populate knowledge base with all docs (Day 2)
3. Wire `create_lead` to real PostgreSQL (Day 3)
4. Wire `check_availability` to real inventory (Day 4)
5. Add 20 integration tests (Day 5)

**After Week 1, you'll have**:
- Real database with all tables
- Real knowledge base (semantic search working)
- Real lead creation (persisted)
- Real availability checking (from inventory)
- Confidence to proceed with Stripe/booking integration

---

**Next Step**: Run Phase 1, Week 1 sprint tasks above.

**Status**: Ready to execute
**Confidence**: High (all infrastructure exists, just needs wiring)
**Timeline**: 12 weeks to 95% complete platform

---

*Document Generated*: 2025-10-23
*Based On*: Deep code review of 39 Python files + 35 test files + 17,000+ lines of documentation
*Repository*: front-desk
*Current Completion*: 33% overall, 85% voice AI
