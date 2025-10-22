# Hotel Operator Agent - Complete Implementation & Training Plan

## Executive Summary

This plan outlines the comprehensive development, testing, and training strategy to transform the Hotel Operator Agent from a mock prototype into a production-ready AI concierge system. The focus is on rigorous testing, incremental implementation, and measurable customer satisfaction metrics.

---

## Current State Analysis

### Implemented (Mock/Prototype)
- ✅ FastAPI application structure with health endpoint
- ✅ WebSocket endpoint (echo functionality)
- ✅ Basic REST endpoint (`/availability`)
- ✅ 5 tool modules with mock implementations
- ✅ Docker deployment infrastructure
- ✅ Basic project structure

### Implementation Gaps
- ❌ No actual AI conversational capabilities
- ❌ No real integrations (payment, booking, CRM)
- ❌ No persistent data storage
- ❌ No authentication or security
- ❌ No logging or monitoring
- ❌ No error handling or validation
- ❌ No unit/integration tests
- ❌ No performance benchmarking
- ❌ No customer satisfaction measurement

---

## Phase 1: Foundation & Testing Infrastructure (Week 1-2)

### 1.1 Testing Framework Setup

**Goal**: Establish comprehensive testing infrastructure before adding features.

#### Unit Testing
```bash
# Add to requirements.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.24.0  # For FastAPI testing
```

**Test Structure**:
```
tests/
├── unit/
│   ├── test_search_kb.py
│   ├── test_check_availability.py
│   ├── test_create_lead.py
│   ├── test_generate_payment_link.py
│   └── test_computer_use.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_websocket.py
│   └── test_tool_integration.py
├── e2e/
│   ├── test_guest_journey.py
│   └── test_operator_workflows.py
└── fixtures/
    ├── hotel_data.py
    └── guest_scenarios.py
```

#### Test Coverage Requirements
- **Unit Tests**: 100% coverage for all tool functions
- **Integration Tests**: All API endpoints and WebSocket
- **E2E Tests**: Complete guest journey scenarios

#### Test Scenarios to Develop

**Unit Test Examples**:
- `test_search_kb_returns_matching_policies()`
- `test_search_kb_case_insensitive()`
- `test_search_kb_empty_query()`
- `test_check_availability_valid_dates()`
- `test_check_availability_invalid_dates()`
- `test_create_lead_all_fields()`
- `test_create_lead_missing_optional_fields()`
- `test_generate_payment_link_formats_correctly()`
- `test_computer_use_returns_success()`

**Integration Test Examples**:
- `test_health_endpoint_returns_200()`
- `test_availability_endpoint_with_params()`
- `test_websocket_accepts_connection()`
- `test_websocket_echoes_messages()`
- `test_invalid_endpoint_returns_404()`

**E2E Test Examples**:
- `test_guest_inquires_about_pet_policy()`
- `test_guest_checks_availability_and_books()`
- `test_guest_generates_payment_link()`
- `test_operator_creates_lead_from_inquiry()`

### 1.2 Code Quality Infrastructure

**Linting & Formatting**:
```bash
# Add to requirements.txt
black>=23.0.0
ruff>=0.0.280
mypy>=1.4.0
```

**Configuration Files**:
- `pyproject.toml` - Black and tool configuration
- `.ruff.toml` - Linting rules
- `mypy.ini` - Type checking configuration

**Pre-commit Hooks**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    hooks:
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

### 1.3 Logging & Monitoring Setup

**Structured Logging**:
```python
# packages/logging/logger.py
import logging
import structlog

def setup_logging(env: str = "local"):
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

**Metrics to Track**:
- Request count by endpoint
- Response time by endpoint
- WebSocket connection duration
- Error rate by type
- Tool execution time
- Memory and CPU usage

### 1.4 Data Validation Layer

**Add Pydantic Models**:
```python
# packages/models/requests.py
from pydantic import BaseModel, EmailStr, validator
from datetime import date

class AvailabilityRequest(BaseModel):
    check_in: date
    check_out: date
    adults: int = 1
    pets: bool = False

    @validator('check_out')
    def check_out_after_check_in(cls, v, values):
        if 'check_in' in values and v <= values['check_in']:
            raise ValueError('check_out must be after check_in')
        return v

    @validator('adults')
    def adults_positive(cls, v):
        if v < 1 or v > 10:
            raise ValueError('adults must be between 1 and 10')
        return v

class LeadRequest(BaseModel):
    full_name: str
    channel: str
    email: EmailStr
    phone: str
    interest: str

    @validator('phone')
    def phone_valid(cls, v):
        # Basic validation - extend as needed
        import re
        if not re.match(r'^\+?1?\d{10,15}$', v):
            raise ValueError('Invalid phone number format')
        return v
```

**Deliverables**:
- [ ] Complete test suite with 100+ test cases
- [ ] pytest configuration with coverage reporting
- [ ] CI/CD pipeline configuration (GitHub Actions)
- [ ] Logging infrastructure with structured logs
- [ ] Pydantic models for all request/response types
- [ ] Code quality tools configured (black, ruff, mypy)
- [ ] Pre-commit hooks setup

---

## Phase 2: Core AI Integration (Week 3-4)

### 2.1 OpenAI Integration for Conversational AI

**Goal**: Transform WebSocket endpoint into intelligent conversational agent.

#### Agent Architecture

**OpenAI Function Calling Pattern**:
```python
# packages/ai/agent.py
from openai import AsyncOpenAI
import json

class HotelAgent:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.tools = self._define_tools()
        self.system_prompt = self._load_system_prompt()

    def _define_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "Search hotel policies and information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_room_availability",
                    "description": "Check if rooms are available for given dates",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "check_in": {"type": "string", "format": "date"},
                            "check_out": {"type": "string", "format": "date"},
                            "adults": {"type": "integer", "default": 1},
                            "pets": {"type": "boolean", "default": False}
                        },
                        "required": ["check_in", "check_out"]
                    }
                }
            },
            # ... other tools
        ]

    async def process_message(self, message: str, conversation_history: list):
        messages = conversation_history + [{"role": "user", "content": message}]

        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "system", "content": self.system_prompt}] + messages,
            tools=self.tools,
            tool_choice="auto"
        )

        return await self._handle_response(response, messages)
```

#### System Prompt Engineering

**Base System Prompt**:
```
You are a friendly and professional hotel front desk agent for an independent boutique hotel.
Your role is to assist guests with:
- Answering questions about hotel policies, amenities, and local area
- Checking room availability
- Creating guest leads and capturing booking intent
- Generating payment links for deposits or full payment
- Providing exceptional, personalized service

Hotel Details:
- Name: [Property Name]
- Location: [City, State]
- Room Types: Standard Queen, King Suite, Pet-Friendly Rooms
- Amenities: Free WiFi, Continental Breakfast, Parking
- Check-in: 4:00 PM | Check-out: 10:00 AM
- Pet Policy: Pets welcome for $20/night fee

Tone Guidelines:
- Warm and welcoming, not robotic
- Professional but conversational
- Proactive in offering help
- Clear and concise
- Always confirm guest intent before taking actions like creating bookings

When you need information:
- Use search_knowledge_base for policies and hotel information
- Use check_room_availability to verify room availability
- Use create_lead when a guest expresses booking interest
- Use generate_payment_link when guest is ready to pay

Always prioritize guest satisfaction and clarity.
```

#### Conversation State Management

**Session Storage**:
```python
# packages/ai/session_manager.py
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio

class ConversationSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict] = []
        self.context: Dict = {}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_activity = datetime.now()

    def set_context(self, key: str, value: any):
        self.context[key] = value

    def is_expired(self, timeout_minutes: int = 30):
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}

    def get_or_create(self, session_id: str) -> ConversationSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(session_id)
        return self.sessions[session_id]

    async def cleanup_expired_sessions(self):
        while True:
            expired = [
                sid for sid, session in self.sessions.items()
                if session.is_expired()
            ]
            for sid in expired:
                del self.sessions[sid]
            await asyncio.sleep(300)  # Clean up every 5 minutes
```

### 2.2 Enhanced WebSocket Implementation

**Updated WebSocket Endpoint**:
```python
# apps/operator-runtime/main.py (updated)
from fastapi import WebSocket, WebSocketDisconnect
from packages.ai.agent import HotelAgent
from packages.ai.session_manager import SessionManager
import os

agent = HotelAgent(api_key=os.getenv("OPENAI_API_KEY"))
session_manager = SessionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    session = session_manager.get_or_create(session_id)

    try:
        while True:
            # Receive message
            message = await websocket.receive_text()
            session.add_message("user", message)

            # Process with AI
            response = await agent.process_message(
                message,
                session.messages
            )

            session.add_message("assistant", response)

            # Send response
            await websocket.send_json({
                "type": "message",
                "content": response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        logger.info(f"Session {session_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")
```

### 2.3 Testing Strategy for AI Integration

**AI Response Quality Tests**:
```python
# tests/integration/test_ai_agent.py
import pytest
from packages.ai.agent import HotelAgent

@pytest.mark.asyncio
async def test_agent_answers_pet_policy_question():
    agent = HotelAgent(api_key=os.getenv("OPENAI_API_KEY"))
    response = await agent.process_message(
        "Do you allow pets?",
        []
    )
    assert "pet" in response.lower()
    assert "$20" in response or "20" in response

@pytest.mark.asyncio
async def test_agent_checks_availability_when_asked():
    agent = HotelAgent(api_key=os.getenv("OPENAI_API_KEY"))
    response = await agent.process_message(
        "Do you have rooms available June 1-3 for 2 adults?",
        []
    )
    # Verify tool was called and response includes availability info
    assert any(keyword in response.lower() for keyword in ["available", "room", "book"])

@pytest.mark.asyncio
async def test_agent_creates_lead_when_guest_shows_interest():
    agent = HotelAgent(api_key=os.getenv("OPENAI_API_KEY"))
    conversation = [
        {"role": "assistant", "content": "Welcome! How can I help?"},
        {"role": "user", "content": "I'd like to book a room for June 1-3"},
        {"role": "assistant", "content": "Great! We have availability. May I get your name and email?"}
    ]
    response = await agent.process_message(
        "Sure, I'm John Doe, john@example.com",
        conversation
    )
    # Verify lead creation tool was called
    assert "john" in response.lower()
```

**Conversation Flow Tests**:
```python
# tests/e2e/test_guest_journey.py
@pytest.mark.asyncio
async def test_complete_booking_journey():
    """Test a guest from inquiry to payment link"""
    session = ConversationSession("test-session")
    agent = HotelAgent(api_key=os.getenv("OPENAI_API_KEY"))

    # Step 1: Initial greeting
    response1 = await agent.process_message("Hello", session.messages)
    assert any(word in response1.lower() for word in ["hello", "welcome", "help"])

    # Step 2: Availability inquiry
    response2 = await agent.process_message(
        "Do you have rooms for June 1-3?",
        session.messages
    )
    assert "available" in response2.lower()

    # Step 3: Booking intent
    response3 = await agent.process_message(
        "Yes, I'd like to book. I'm Jane Smith, jane@example.com, 555-1234",
        session.messages
    )
    assert any(word in response3.lower() for word in ["book", "reservation", "confirm"])

    # Step 4: Payment
    response4 = await agent.process_message(
        "Can I pay a deposit now?",
        session.messages
    )
    assert "payment" in response4.lower() or "link" in response4.lower()
```

**Deliverables**:
- [ ] OpenAI integration with function calling
- [ ] System prompt with hotel-specific context
- [ ] Session management with conversation history
- [ ] Enhanced WebSocket with AI responses
- [ ] Tool execution framework (AI → Tool → Response)
- [ ] 50+ AI conversation test cases
- [ ] Response quality validation tests
- [ ] Latency benchmarks (<2s response time)

---

## Phase 3: Tool Implementation & Integration (Week 5-7)

### 3.1 Knowledge Base Implementation

**ChromaDB Vector Store**:
```python
# packages/tools/search_kb.py (production version)
import chromadb
from chromadb.config import Settings
from typing import List, Dict
import os

class KnowledgeBase:
    def __init__(self, persist_directory: str = "./data/chroma"):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory
        ))
        self.collection = self.client.get_or_create_collection(
            name="hotel_policies",
            metadata={"hnsw:space": "cosine"}
        )
        self._initialize_if_empty()

    def _initialize_if_empty(self):
        """Load default policies if collection is empty"""
        if self.collection.count() == 0:
            self._load_default_policies()

    def _load_default_policies(self):
        policies = [
            {
                "id": "pet-policy",
                "title": "Pet Policy",
                "content": "We welcome pets! There is a $20 per night fee for each pet. Please inform us at booking so we can assign a pet-friendly room. Maximum 2 pets per room.",
                "category": "policies"
            },
            {
                "id": "checkin-time",
                "title": "Check-in Time",
                "content": "Check-in time is after 4:00 PM. Early check-in may be available upon request, subject to availability. Please contact us in advance.",
                "category": "policies"
            },
            {
                "id": "checkout-time",
                "title": "Check-out Time",
                "content": "Check-out time is 10:00 AM. Late check-out until 12:00 PM can be arranged for $25, subject to availability.",
                "category": "policies"
            },
            # Add 50+ more policies covering:
            # - Cancellation policy
            # - Parking information
            # - WiFi details
            # - Breakfast hours
            # - Pool/gym hours
            # - Local attractions
            # - Transportation options
            # - Accessibility features
        ]

        self.collection.add(
            documents=[p["content"] for p in policies],
            metadatas=[{"title": p["title"], "category": p["category"]} for p in policies],
            ids=[p["id"] for p in policies]
        )

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        return [
            {
                "title": results["metadatas"][0][i]["title"],
                "content": results["documents"][0][i],
                "relevance": 1 - results["distances"][0][i]  # Convert distance to similarity
            }
            for i in range(len(results["ids"][0]))
        ]

# Updated function signature
def search_kb(query: str, top_k: int = 5) -> List[Dict]:
    kb = KnowledgeBase()
    return kb.search(query, top_k)
```

**Knowledge Base Content Strategy**:
- Hotel policies (20+ entries)
- Local area information (30+ entries)
- Amenity details (15+ entries)
- FAQ responses (40+ entries)
- Troubleshooting guides (10+ entries)

### 3.2 Availability System Integration

**Options for Implementation**:
1. **Mock Database** (for testing)
2. **SQLite** (for simple deployments)
3. **PostgreSQL** (for production)
4. **External PMS API** (for integration with existing systems)

**PostgreSQL Implementation**:
```python
# packages/db/database.py
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/hotel")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RoomInventory(Base):
    __tablename__ = "room_inventory"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    standard_queen_available = Column(Integer, default=10)
    king_suite_available = Column(Integer, default=5)
    pet_friendly_available = Column(Integer, default=3)

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    guest_name = Column(String)
    guest_email = Column(String, index=True)
    guest_phone = Column(String)
    check_in = Column(Date, index=True)
    check_out = Column(Date, index=True)
    room_type = Column(String)
    adults = Column(Integer)
    pets = Column(Boolean)
    status = Column(String, default="pending")  # pending, confirmed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
```

**Updated Availability Tool**:
```python
# packages/tools/check_availability.py (production version)
from packages.db.database import SessionLocal, RoomInventory
from datetime import date, timedelta
from typing import Dict

def check_availability(
    check_in: str,
    check_out: str,
    adults: int = 1,
    pets: bool = False
) -> Dict:
    """Check actual room availability from database"""
    db = SessionLocal()

    try:
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)

        # Query inventory for date range
        current_date = check_in_date
        min_rooms = float('inf')

        while current_date < check_out_date:
            inventory = db.query(RoomInventory).filter(
                RoomInventory.date == current_date
            ).first()

            if inventory:
                available = (
                    inventory.pet_friendly_available if pets
                    else inventory.standard_queen_available + inventory.king_suite_available
                )
                min_rooms = min(min_rooms, available)
            else:
                # No inventory record = assume available
                min_rooms = min(min_rooms, 10)

            current_date += timedelta(days=1)

        return {
            "check_in": check_in,
            "check_out": check_out,
            "adults": adults,
            "pets": pets,
            "rooms_available": int(min_rooms) if min_rooms != float('inf') else 0,
            "available": min_rooms > 0,
            "room_types": ["Standard Queen", "King Suite"] if not pets else ["Pet-Friendly Room"],
            "price_per_night": 120 if not pets else 140,  # Base pricing
            "total_nights": (check_out_date - check_in_date).days
        }

    finally:
        db.close()
```

### 3.3 Lead Management System

**CRM Integration Options**:
1. **Local SQLite** (self-contained)
2. **PostgreSQL** (production)
3. **External CRM API** (Salesforce, HubSpot)
4. **StayHive Integration** (future)

**Production Lead Tool**:
```python
# packages/tools/create_lead.py (production version)
from packages.db.database import SessionLocal, Base
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(String, unique=True, index=True)
    full_name = Column(String)
    channel = Column(String)  # web, phone, email, chat
    email = Column(String, index=True)
    phone = Column(String)
    interest = Column(Text)
    status = Column(String, default="new")  # new, contacted, qualified, converted, lost
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def create_lead(
    full_name: str,
    channel: str,
    email: str,
    phone: str,
    interest: str
) -> Dict:
    """Create a new guest lead in the system"""
    db = SessionLocal()

    try:
        # Generate unique lead ID
        import uuid
        lead_id = f"LD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        lead = Lead(
            lead_id=lead_id,
            full_name=full_name,
            channel=channel,
            email=email,
            phone=phone,
            interest=interest
        )

        db.add(lead)
        db.commit()
        db.refresh(lead)

        return {
            "lead_id": lead.lead_id,
            "status": "saved",
            "created_at": lead.created_at.isoformat(),
            "message": f"Lead created successfully for {full_name}"
        }

    except Exception as e:
        db.rollback()
        return {
            "lead_id": None,
            "status": "error",
            "message": str(e)
        }
    finally:
        db.close()
```

### 3.4 Payment Link Generation

**Stripe Integration**:
```python
# packages/tools/generate_payment_link.py (production version)
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def generate_payment_link(amount_cents: int, description: str) -> Dict:
    """Generate a Stripe payment link"""
    try:
        # Create a product
        product = stripe.Product.create(
            name=f"Hotel Booking - {description}",
            description=description
        )

        # Create a price
        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount_cents,
            currency="usd"
        )

        # Create payment link
        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
            after_completion={
                "type": "redirect",
                "redirect": {"url": "https://yourhotel.com/booking-confirmed"}
            }
        )

        return {
            "url": payment_link.url,
            "payment_link_id": payment_link.id,
            "amount_cents": amount_cents,
            "description": description,
            "expires_at": None,  # Stripe links don't expire by default
            "status": "active"
        }

    except stripe.error.StripeError as e:
        return {
            "url": None,
            "error": str(e),
            "status": "error"
        }
```

**Testing Payment Links**:
```python
# tests/integration/test_payment_links.py
def test_generate_payment_link_creates_stripe_link(mocker):
    # Mock Stripe API
    mock_stripe = mocker.patch('stripe.PaymentLink.create')
    mock_stripe.return_value = MagicMock(
        url="https://buy.stripe.com/test_123",
        id="plink_123"
    )

    result = generate_payment_link(20000, "Deposit for June 1-3")

    assert result["url"].startswith("https://buy.stripe.com/")
    assert result["amount_cents"] == 20000
    assert result["status"] == "active"
```

### 3.5 Computer Use / Automation Tool

**Purpose**: Execute administrative tasks (update reservations, send emails, etc.)

```python
# packages/tools/computer_use.py (production version)
from typing import Dict, Any
import asyncio

async def send_confirmation_email(guest_email: str, reservation_details: Dict):
    """Send booking confirmation email"""
    # Integration with SendGrid, Mailgun, or SMTP
    pass

async def update_reservation_status(reservation_id: str, status: str):
    """Update reservation status in database"""
    pass

async def send_sms_reminder(phone: str, message: str):
    """Send SMS reminder via Twilio"""
    pass

def computer_use(task: str, **kwargs) -> Dict[str, Any]:
    """
    Execute automation tasks

    Supported tasks:
    - send_confirmation_email
    - update_reservation
    - send_sms
    - generate_invoice
    """
    task_handlers = {
        "send_confirmation_email": send_confirmation_email,
        "update_reservation": update_reservation_status,
        "send_sms": send_sms_reminder,
    }

    if task not in task_handlers:
        return {
            "task": task,
            "result": "error",
            "message": f"Unknown task: {task}"
        }

    try:
        handler = task_handlers[task]
        result = asyncio.run(handler(**kwargs))
        return {
            "task": task,
            "result": "success",
            "data": result
        }
    except Exception as e:
        return {
            "task": task,
            "result": "error",
            "message": str(e)
        }
```

**Deliverables**:
- [ ] Production knowledge base with 100+ entries
- [ ] PostgreSQL database schema and migrations
- [ ] Real availability checking with inventory management
- [ ] Lead creation with CRM database
- [ ] Stripe payment link integration
- [ ] Computer use automation framework
- [ ] Integration tests for all tools
- [ ] End-to-end workflow tests

---

## Phase 4: Performance Optimization & Scalability (Week 8)

### 4.1 Caching Strategy

**Redis Implementation**:
```python
# packages/cache/redis_cache.py
import redis
import json
from typing import Optional, Any

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    def get(self, key: str) -> Optional[Any]:
        value = self.redis.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any, ttl: int = 300):
        self.redis.setex(key, ttl, json.dumps(value))

    def invalidate(self, key: str):
        self.redis.delete(key)

# Usage in tools
cache = CacheManager()

def search_kb(query: str, top_k: int = 5):
    cache_key = f"kb:{query}:{top_k}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    result = kb.search(query, top_k)
    cache.set(cache_key, result, ttl=600)  # 10 minute cache
    return result
```

### 4.2 Performance Benchmarking

**Load Testing with Locust**:
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class HotelAgentUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def check_availability(self):
        self.client.get(
            "/availability",
            params={
                "check_in": "2025-06-01",
                "check_out": "2025-06-03",
                "adults": 2
            }
        )

    @task(1)
    def health_check(self):
        self.client.get("/health")
```

**Performance Targets**:
- Health endpoint: <50ms p99
- Availability check: <200ms p99
- WebSocket message: <2s p99 (with AI)
- Knowledge base search: <100ms p99
- Payment link generation: <500ms p99

### 4.3 Database Optimization

**Indexes**:
```sql
CREATE INDEX idx_reservations_dates ON reservations(check_in, check_out);
CREATE INDEX idx_reservations_email ON reservations(guest_email);
CREATE INDEX idx_leads_created ON leads(created_at);
CREATE INDEX idx_inventory_date ON room_inventory(date);
```

**Connection Pooling**:
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

**Deliverables**:
- [ ] Redis caching layer
- [ ] Performance benchmarks for all endpoints
- [ ] Database query optimization
- [ ] Load testing results (1000+ concurrent users)
- [ ] Response time improvements (<2s for AI responses)

---

## Phase 5: Customer Satisfaction & Quality Assurance (Week 9-10)

### 5.1 Conversation Quality Metrics

**Metrics to Track**:
1. **Response Accuracy**: Does the agent answer correctly?
2. **Response Completeness**: Does it provide all needed information?
3. **Tone & Professionalism**: Is it friendly and appropriate?
4. **Task Completion Rate**: Does it successfully complete guest requests?
5. **Hallucination Rate**: Does it make up information?
6. **Tool Usage Accuracy**: Does it call the right tools?

**Quality Scoring System**:
```python
# packages/quality/conversation_scorer.py
from typing import Dict, List

class ConversationScorer:
    def score_response(
        self,
        user_message: str,
        agent_response: str,
        tools_called: List[str],
        expected_tools: List[str]
    ) -> Dict:
        scores = {
            "accuracy": self._score_accuracy(user_message, agent_response),
            "completeness": self._score_completeness(user_message, agent_response),
            "tone": self._score_tone(agent_response),
            "tool_usage": self._score_tool_usage(tools_called, expected_tools),
            "hallucination": self._detect_hallucination(agent_response)
        }

        scores["overall"] = sum(scores.values()) / len(scores)
        return scores

    def _score_accuracy(self, question: str, answer: str) -> float:
        # Use GPT-4 to evaluate if answer is factually correct
        pass

    def _score_tone(self, response: str) -> float:
        # Evaluate friendliness, professionalism
        pass
```

### 5.2 Test Conversation Library

**100+ Test Conversations**:
```python
# tests/quality/test_conversations.py

QUALITY_TEST_CONVERSATIONS = [
    {
        "name": "Pet Policy Inquiry",
        "messages": [
            {"role": "user", "content": "Do you allow dogs?"},
        ],
        "expected_keywords": ["pet", "$20", "welcome", "night"],
        "expected_tools": ["search_knowledge_base"],
        "min_quality_score": 0.85
    },
    {
        "name": "Availability Check",
        "messages": [
            {"role": "user", "content": "Do you have rooms June 1-3?"},
        ],
        "expected_keywords": ["available", "room"],
        "expected_tools": ["check_room_availability"],
        "min_quality_score": 0.85
    },
    {
        "name": "Complete Booking Flow",
        "messages": [
            {"role": "user", "content": "I need a room for June 1-3"},
            {"role": "assistant", "content": "..."},
            {"role": "user", "content": "Yes, I'd like to book. I'm Jane Smith, jane@example.com"},
        ],
        "expected_tools": ["check_room_availability", "create_lead"],
        "min_quality_score": 0.90
    },
    # ... 100+ more scenarios
]
```

**Test Categories**:
1. **Policy Questions** (20 tests)
   - Pet policy
   - Check-in/out times
   - Cancellation policy
   - Parking
   - Amenities

2. **Availability Queries** (20 tests)
   - Simple date checks
   - Complex requirements (pets, accessibility)
   - Edge cases (same-day, long stays)

3. **Booking Flows** (30 tests)
   - Happy path
   - Missing information
   - Multi-step clarification
   - Payment generation

4. **Edge Cases** (15 tests)
   - Unclear requests
   - Multiple questions
   - Complaints/issues
   - Special requests

5. **Local Information** (15 tests)
   - Nearby restaurants
   - Attractions
   - Transportation
   - Weather/seasons

### 5.3 Human Evaluation Framework

**Review Process**:
1. Generate 100 AI conversations
2. Human reviewers score each conversation
3. Compare AI scores vs human scores
4. Identify patterns in failures
5. Refine prompts and training

**Reviewer Scorecard**:
```yaml
Conversation ID: CONV-001
Date: 2025-10-20
Reviewer: [Name]

Scores (1-5):
- Accuracy: 5 (Correct information provided)
- Completeness: 4 (Missed asking about dietary restrictions)
- Tone: 5 (Friendly and professional)
- Efficiency: 4 (Could have been more concise)
- Problem Resolution: 5 (Guest need fully addressed)

Overall: 4.6/5

Notes:
- Excellent handling of pet policy question
- Suggested late checkout without being asked (proactive!)
- Minor: Could have confirmed booking intent earlier

Recommendation: PASS ✓
```

### 5.4 Continuous Improvement Loop

**Feedback Collection**:
```python
# apps/operator-runtime/main.py
@app.post("/feedback")
async def submit_feedback(
    session_id: str,
    rating: int,  # 1-5
    comment: str = "",
    issue_type: str = ""
):
    """Collect guest feedback on AI interactions"""
    # Store in database
    # Trigger alert if rating < 3
    # Aggregate for weekly reports
    pass
```

**A/B Testing Framework**:
```python
# Test different system prompts
# Test different models (GPT-4 vs GPT-3.5)
# Test different tool-calling strategies
```

**Deliverables**:
- [ ] Conversation quality scoring system
- [ ] 100+ test conversation scenarios
- [ ] Human evaluation framework and scorecard
- [ ] Quality benchmarks (>85% accuracy, >90% completeness)
- [ ] Feedback collection system
- [ ] Weekly quality reports

---

## Phase 6: Security & Production Readiness (Week 11)

### 6.1 Security Implementation

**Authentication & Authorization**:
```python
# packages/auth/jwt_auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=24)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Protect endpoints
@app.get("/admin/leads")
async def get_leads(user = Depends(verify_token)):
    # Only accessible with valid token
    pass
```

**Rate Limiting**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/availability")
@limiter.limit("30/minute")
async def availability(...):
    pass
```

**Input Validation & Sanitization**:
```python
from pydantic import validator
import bleach

class LeadRequest(BaseModel):
    full_name: str

    @validator('full_name')
    def sanitize_name(cls, v):
        # Remove any HTML/scripts
        return bleach.clean(v, strip=True)
```

**Environment Variable Security**:
```bash
# .env.production
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_live_...
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=...
REDIS_URL=redis://...

# Never commit .env files
# Use secrets management (AWS Secrets Manager, HashiCorp Vault)
```

### 6.2 Error Handling & Resilience

**Global Exception Handler**:
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again.",
            "request_id": request.state.request_id
        }
    )
```

**Retry Logic**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_openai_with_retry(messages):
    return await openai_client.chat.completions.create(...)
```

**Circuit Breaker**:
```python
from pybreaker import CircuitBreaker

openai_breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

@openai_breaker
async def call_openai(messages):
    # If OpenAI fails 5 times, circuit opens for 60 seconds
    pass
```

### 6.3 Monitoring & Alerting

**Prometheus Metrics**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
websocket_connections = Gauge('websocket_connections_active', 'Active WebSocket connections')
ai_response_time = Histogram('ai_response_duration_seconds', 'AI response time')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    with request_duration.time():
        response = await call_next(request)
        request_count.labels(method=request.method, endpoint=request.url.path).inc()
        return response
```

**Health Checks**:
```python
@app.get("/health/liveness")
async def liveness():
    return {"status": "alive"}

@app.get("/health/readiness")
async def readiness():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "openai": await check_openai()
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_healthy else "not ready", "checks": checks}
    )
```

**Deliverables**:
- [ ] JWT authentication for admin endpoints
- [ ] Rate limiting (30 req/min per IP)
- [ ] Input validation and sanitization
- [ ] Global error handling
- [ ] Retry logic for external APIs
- [ ] Circuit breakers for resilience
- [ ] Prometheus metrics
- [ ] Health check endpoints
- [ ] Security audit and penetration testing

---

## Phase 7: Deployment & Operations (Week 12)

### 7.1 Docker Production Configuration

**Multi-stage Dockerfile**:
```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser apps/ ./apps/
COPY --chown=appuser:appuser packages/ ./packages/

USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health/liveness || exit 1

CMD ["python", "apps/operator-runtime/main.py"]
```

**Docker Compose for Local Development**:
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=local
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/hotel
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=hotel
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  postgres_data:
```

### 7.2 Cloud Deployment (Google Cloud Run)

**Cloud Run Deployment Script**:
```bash
#!/usr/bin/env bash
# deploy-production.sh

set -Eeuo pipefail

PROJECT_ID=${PROJECT_ID:-"your-gcp-project"}
SERVICE_NAME=${SERVICE_NAME:-"hotel-operator-agent"}
REGION=${REGION:-"us-central1"}
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

log() { printf "\033[1;34m==>\033[0m %s\n" "$*"; }

log "Building production Docker image..."
docker build -t ${IMAGE} .

log "Pushing to Google Container Registry..."
docker push ${IMAGE}

log "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE} \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars "ENV=production" \
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest,STRIPE_SECRET_KEY=stripe-secret-key:latest,DATABASE_URL=database-url:latest"

log "Deployment complete!"
gcloud run services describe ${SERVICE_NAME} --region ${REGION}
```

### 7.3 CI/CD Pipeline

**GitHub Actions Workflow**:
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: hotel_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run linting
        run: |
          pip install black ruff mypy
          black --check .
          ruff check .
          mypy packages/ apps/

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/hotel_test
          REDIS_URL: redis://localhost:6379
        run: |
          pytest tests/ --cov=packages --cov=apps --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}

      - name: Configure Docker
        run: gcloud auth configure-docker

      - name: Build and Deploy
        run: ./deploy-production.sh
```

### 7.4 Monitoring Dashboards

**Grafana Dashboard Config**:
```json
{
  "dashboard": {
    "title": "Hotel Operator Agent Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{"expr": "rate(http_requests_total[5m])"}]
      },
      {
        "title": "Response Time (p95)",
        "targets": [{"expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"}]
      },
      {
        "title": "AI Response Time",
        "targets": [{"expr": "histogram_quantile(0.95, ai_response_duration_seconds_bucket)"}]
      },
      {
        "title": "Active WebSocket Connections",
        "targets": [{"expr": "websocket_connections_active"}]
      },
      {
        "title": "Error Rate",
        "targets": [{"expr": "rate(http_requests_total{status=~\"5..\"}[5m])"}]
      }
    ]
  }
}
```

**Deliverables**:
- [ ] Production Docker configuration
- [ ] Docker Compose for local development
- [ ] Cloud Run deployment scripts
- [ ] CI/CD pipeline with automated testing
- [ ] Monitoring dashboards (Grafana)
- [ ] Alerting rules (PagerDuty/Slack)
- [ ] Deployment documentation
- [ ] Rollback procedures

---

## Success Metrics & KPIs

### Customer Satisfaction Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Conversation Quality Score** | >85% | AI + Human evaluation of 100 test conversations |
| **Task Completion Rate** | >90% | % of guest requests successfully fulfilled |
| **Response Accuracy** | >95% | % of factually correct responses |
| **Hallucination Rate** | <2% | % of responses with made-up information |
| **Guest Satisfaction Rating** | >4.5/5 | Post-conversation surveys |
| **First Response Time** | <2s | Time to first AI response |
| **Issue Resolution Rate** | >85% | % of issues resolved without human intervention |

### Technical Performance Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **API Uptime** | >99.9% | Monthly uptime tracking |
| **Response Time (p95)** | <2s | 95th percentile response time |
| **WebSocket Latency** | <500ms | Message round-trip time |
| **Error Rate** | <0.5% | % of requests returning 5xx errors |
| **Test Coverage** | >90% | Code coverage from pytest |
| **Load Capacity** | 1000+ concurrent | Users handled simultaneously |

### Business Impact Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Lead Capture Rate** | >80% | % of inquiries converted to leads |
| **Booking Conversion** | >30% | % of leads that book |
| **Payment Link Usage** | >60% | % of bookings using AI-generated links |
| **Cost per Conversation** | <$0.10 | AI API costs per conversation |
| **Human Handoff Rate** | <15% | % requiring human intervention |

---

## Training & Improvement Strategy

### 1. Initial Training Phase (Week 1-2 of Deployment)

**Data Collection**:
- Monitor first 1,000 conversations
- Flag conversations requiring human intervention
- Collect guest feedback

**Analysis**:
- Identify common failure patterns
- Analyze hallucination instances
- Review tool usage accuracy

**Improvements**:
- Refine system prompt
- Add missing knowledge base entries
- Adjust tool-calling thresholds

### 2. Continuous Improvement Loop

**Weekly**:
- Review quality metrics
- Analyze worst-performing conversations
- Update knowledge base with new information
- Deploy prompt improvements

**Monthly**:
- Comprehensive quality audit (100 random conversations)
- Human evaluation and scoring
- A/B test new prompts or models
- Update test suite with new scenarios

**Quarterly**:
- Major feature additions
- Model upgrades (GPT-4 → GPT-5, etc.)
- Integration expansions
- Performance optimization

### 3. Feedback Mechanisms

**Guest Feedback**:
```python
@app.post("/api/conversation/{session_id}/feedback")
async def submit_feedback(
    session_id: str,
    rating: int,
    helpful: bool,
    comment: str = ""
):
    # Store feedback
    # If rating < 3, alert team for review
    # Aggregate for weekly reports
    pass
```

**Operator Feedback**:
- Dashboard for hotel staff to review conversations
- Flag incorrect responses
- Suggest improvements
- Mark conversations as "excellent examples"

**Automated Monitoring**:
- Flag conversations with:
  - >3 tool failures
  - >5 back-and-forth messages without resolution
  - Guest frustration indicators
  - Potential hallucinations

---

## Testing Checklist

### Unit Tests (100+ tests)
- [ ] All tool functions with valid inputs
- [ ] All tool functions with invalid inputs
- [ ] Edge cases (empty strings, null values, extreme numbers)
- [ ] Error handling paths
- [ ] Data validation logic
- [ ] Caching behavior
- [ ] Database operations

### Integration Tests (50+ tests)
- [ ] All API endpoints (health, availability, etc.)
- [ ] WebSocket connection and messaging
- [ ] Tool integration with AI agent
- [ ] Database connectivity
- [ ] Redis caching
- [ ] External API integrations (Stripe, OpenAI)
- [ ] Authentication flows
- [ ] Rate limiting

### End-to-End Tests (30+ scenarios)
- [ ] Complete booking journey
- [ ] Policy inquiry flows
- [ ] Payment generation flows
- [ ] Lead creation workflows
- [ ] Multi-step conversations
- [ ] Error recovery scenarios
- [ ] Edge case guest requests

### Performance Tests
- [ ] Load testing (1000+ concurrent users)
- [ ] Stress testing (find breaking point)
- [ ] Latency benchmarks
- [ ] Database query performance
- [ ] Cache hit rates
- [ ] Memory leak detection

### Quality Tests (100+ conversations)
- [ ] Accuracy evaluation
- [ ] Completeness evaluation
- [ ] Tone and professionalism
- [ ] Hallucination detection
- [ ] Tool usage correctness
- [ ] Multi-turn conversation coherence

### Security Tests
- [ ] Authentication bypass attempts
- [ ] SQL injection attempts
- [ ] XSS attempts
- [ ] Rate limit bypass attempts
- [ ] JWT token validation
- [ ] Input sanitization
- [ ] CORS configuration

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **OpenAI API outage** | High | Medium | Circuit breaker, fallback to basic responses, status page |
| **Database failure** | High | Low | Regular backups, replication, health checks |
| **High API costs** | Medium | Medium | Rate limiting, caching, cost monitoring alerts |
| **Hallucinations** | High | Medium | Rigorous testing, human review, confidence thresholds |
| **Security breach** | High | Low | Authentication, input validation, regular audits |

### Business Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Poor guest experience** | High | Medium | Extensive testing, human fallback, feedback collection |
| **Inaccurate information** | High | Low | Knowledge base validation, regular updates |
| **Low adoption** | Medium | Low | User training, clear value proposition, easy onboarding |

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1: Foundation** | Week 1-2 | Testing framework, logging, validation |
| **Phase 2: AI Integration** | Week 3-4 | OpenAI agent, WebSocket, session management |
| **Phase 3: Tool Implementation** | Week 5-7 | Production tools, database, integrations |
| **Phase 4: Performance** | Week 8 | Caching, optimization, benchmarks |
| **Phase 5: Quality Assurance** | Week 9-10 | Test library, evaluation, metrics |
| **Phase 6: Security** | Week 11 | Auth, rate limiting, monitoring |
| **Phase 7: Deployment** | Week 12 | CI/CD, production deployment, operations |

**Total Timeline**: 12 weeks to production-ready system

---

## Budget Estimate

### Development Costs
- **Engineering Time**: 12 weeks × 1 developer = ~$50,000
- **Testing Time**: 2 weeks QA = ~$8,000
- **Total Development**: ~$58,000

### Operational Costs (Monthly)
- **OpenAI API**: ~$500-1000 (based on usage)
- **Cloud Run**: ~$200-400 (2 instances, 2GB RAM)
- **Database (Cloud SQL)**: ~$100-200
- **Redis**: ~$50
- **Monitoring**: ~$50
- **Total Monthly**: ~$900-1,700

### Third-Party Services
- **Stripe**: Transaction fees (2.9% + $0.30 per transaction)
- **Twilio** (if SMS): ~$0.0075 per message
- **SendGrid** (if email): Free tier → $15/month

---

## Conclusion

This comprehensive plan provides a structured approach to transforming the Hotel Operator Agent from a prototype into a production-ready, high-performance AI concierge system. The focus on rigorous testing, measurable quality metrics, and continuous improvement ensures the highest possible customer satisfaction.

**Key Success Factors**:
1. ✅ Comprehensive testing at every layer (unit, integration, e2e, quality)
2. ✅ Measurable quality metrics with clear targets
3. ✅ Iterative improvement based on real feedback
4. ✅ Production-grade infrastructure and monitoring
5. ✅ Security and performance optimization
6. ✅ Clear timeline and deliverables

**Next Steps**:
1. Review and approve this plan
2. Set up development environment
3. Begin Phase 1: Testing infrastructure
4. Establish weekly check-ins for progress tracking
