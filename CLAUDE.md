# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Hotel Operator Agent — A locally-runnable AI concierge that gives independent hotels, B&Bs, and hostels the digital capabilities of a chain without vendor lock-in. This FastAPI-based service is designed to run entirely offline or locally, providing 24/7 guest inquiry handling, availability checking, lead management, and payment link generation.

**Vision**: The "front-desk brain in a box" — a self-contained agent that runs on-premise and can optionally connect to cloud infrastructure (StayHive.ai / BizHive.cloud) for synchronization and analytics.

**Design Philosophy**:
- Offline-first operation (no external API dependencies required)
- Modular tool architecture for easy extension
- Rapid deployment (<60 seconds with Docker)
- Foundation for future OpenAI AgentKit and Realtime API integration

## Technology Stack
- **Framework**: FastAPI (Python 3.11)
- **Runtime**: Uvicorn ASGI server
- **Deployment**: Docker containers (local and Cloud Run)
- **Dependencies**: OpenAI, ChromaDB, FastAPI, Uvicorn

## Architecture

### Project Structure
```
front-desk/
├── apps/
│   └── operator-runtime/
│       └── main.py              # FastAPI application entry point
├── packages/
│   ├── tools/                   # Modular tool implementations
│   │   ├── check_availability.py
│   │   ├── create_lead.py
│   │   ├── generate_payment_link.py
│   │   ├── search_kb.py
│   │   └── computer_use.py
│   └── voice/                   # Voice interaction module (NEW)
│       ├── gateway.py           # Voice gateway (Twilio, WebRTC)
│       ├── session.py           # Session management
│       ├── models.py            # Database models
│       ├── tools.py             # Voice-specific tools
│       └── README.md            # Voice module documentation
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container build config
├── deploy-cloud-run.sh         # Build and run script
├── VOICE_MODULE_DESIGN.md      # Voice architecture design
└── VOICE_IMPLEMENTATION_PLAN.md # Voice implementation roadmap
```

### Application Entry Point
[main.py](apps/operator-runtime/main.py) defines the FastAPI application with:
- `/health` endpoint for health checks (includes voice session count)
- `/ws` WebSocket endpoint for real-time communication
- `/availability` endpoint that wraps the check_availability tool
- `/voice/*` endpoints for voice interactions (phone calls, WebRTC)
- Tool imports from `packages.tools` and `packages.voice`

### Tools Module
The `packages/tools/` directory contains standalone Python functions that implement business logic. These are currently mock implementations demonstrating the interface:

| Tool | Purpose | Current Implementation |
|------|---------|----------------------|
| **search_kb** | Knowledge base search for hotel policies | Returns static policies (pet policy, check-in/out times) |
| **check_availability** | Room availability checker | Returns mock data (5 rooms always available) |
| **create_lead** | Guest lead capture | Returns mock lead ID |
| **generate_payment_link** | Payment link generation | Returns example.com URL |
| **computer_use** | Task execution interface | Returns success message |

Each tool is a pure Python function with a clear signature, making it easy to:
- Test in isolation
- Mock for development
- Replace with real integrations (e.g., PMS systems, Stripe, OpenAI)

## Development Commands

### Local Development
```bash
# Build and run locally with Docker
./deploy-cloud-run.sh

# Alternative (calls deploy-cloud-run.sh)
./run_local.sh

# Install dependencies (if running without Docker)
pip install -r requirements.txt

# Run directly with Python (without Docker)
python apps/operator-runtime/main.py
```

### Testing the Service
```bash
# Health check
curl http://localhost:8000/health

# Check availability
curl "http://localhost:8000/availability?check_in=2025-10-20&check_out=2025-10-22&adults=2&pets=true"
```

### Docker Commands
```bash
# Build image manually
docker build -t hotel-operator-agent:local .

# Run container with environment variables
docker run --rm -it -p 8000:8000 \
  -e ENV=local \
  -e PROJECT_ID=local-test-project \
  hotel-operator-agent:local
```

## Environment Configuration
Environment variables are set in [.env.local](.env.local):
- `ENV`: Runtime environment (local/dev/prod)
- `PROJECT_ID`: Google Cloud project identifier
- `REGION`: Cloud deployment region (us-central1)

## Adding New Tools
1. Create a new Python file in `packages/tools/` with a function implementation
2. Import the function in `packages/tools/__init__.py`
3. Import and use in [apps/operator-runtime/main.py](apps/operator-runtime/main.py)
4. Add FastAPI route if exposing as HTTP endpoint

## Key Implementation Details
- **Port**: Service runs on port 8000 by default
- **WebSocket**: `/ws` endpoint accepts connections and echoes messages with "🤖 Front Desk Agent received:" prefix
- **Mock Data**: All tools currently return mock data to demonstrate the interface
- **Offline-First**: No external API calls are made; everything runs locally
- **Function Pattern**: All tools use simple function signatures (no classes) for easy testing and mocking

## Voice Module (NEW)

The voice module enables phone and WebRTC-based voice interactions with guests. See [packages/voice/README.md](packages/voice/README.md) for detailed documentation.

### Voice Features
- ✅ **Phone Calls**: Handle inbound/outbound calls via Twilio
- ✅ **Session Management**: Track all voice interactions with conversation history
- ✅ **Voice Tools**: Call transfer, hold music, SMS confirmations, IVR menus
- ✅ **Audio Processing**: STT (Whisper), TTS (OpenAI), VAD, recording
- ✅ **OpenAI Realtime API**: Natural voice conversations with function calling (ACTIVATED)
- 🔜 **WebRTC Support**: Browser-based voice chat
- 🔜 **Analytics Dashboard**: Call metrics and sentiment analysis

### Voice API Endpoints
All voice endpoints are prefixed with `/voice`:
- `GET /voice/health` - Voice service health check
- `POST /voice/twilio/inbound` - Twilio webhook for incoming calls
- `POST /voice/twilio/status` - Call status callbacks
- `WS /voice/twilio/stream` - Real-time audio streaming
- `GET /voice/sessions` - List active voice sessions
- `GET /voice/sessions/{id}` - Get session details
- `POST /voice/sessions/{id}/end` - End a session

### Voice Configuration
Set these environment variables in [.env.local](.env.local):
```env
VOICE_ENABLED=true
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567
OPENAI_API_KEY=your_openai_key
```

### Testing Voice Module
```bash
# Run example
python examples/voice/simple_call.py

# Run unit tests
pytest tests/unit/voice/

# Check voice health
curl http://localhost:8000/voice/health
```

### Voice Documentation
- **Architecture**: [VOICE_MODULE_DESIGN.md](VOICE_MODULE_DESIGN.md) - Complete design document (1000+ lines)
- **Implementation**: [VOICE_IMPLEMENTATION_PLAN.md](VOICE_IMPLEMENTATION_PLAN.md) - 14-day roadmap
- **Module README**: [packages/voice/README.md](packages/voice/README.md) - API reference
- **Phase 3 Complete**: [VOICE_PHASE3_COMPLETE.md](VOICE_PHASE3_COMPLETE.md) - Realtime API documentation
- **Activation Guide**: [REALTIME_ACTIVATION_GUIDE.md](REALTIME_ACTIVATION_GUIDE.md) - Setup instructions
- **Test Report**: [VOICE_TEST_REPORT.md](VOICE_TEST_REPORT.md) - Phase 1 & 2 test results (70/70 passing)

### Voice Implementation Status

**✅ Phase 1 - Core Infrastructure** (Complete)
- Voice gateway with Twilio integration
- Session management and conversation tracking
- 9 voice-specific tools (transfer, hold music, SMS, etc.)
- Database models for calls and analytics

**✅ Phase 2 - Audio Processing** (Complete)
- Speech-to-Text with OpenAI Whisper
- Text-to-Speech with OpenAI (6 voices)
- Voice Activity Detection (VAD)
- Audio recording and storage (local/S3)
- Codec conversion (μ-law, PCM16, etc.)
- Audio resampling and format conversion

**✅ Phase 3 - OpenAI Realtime API** (Complete - ACTIVATED)
- RealtimeAPIClient with WebSocket connection (800+ lines)
- FunctionRegistry for tool integration (400+ lines)
- ConversationManager with context injection (500+ lines)
- RealtimeBridge connecting Twilio to Realtime API (600+ lines)
- Bidirectional audio streaming
- Function calling for 6 hotel tools
- Interruption handling (barge-in support)
- **Total Phase 3 Code**: 2,300+ lines
- **Total Voice Module**: 6,000+ lines

**🔜 Future Phases**
- **Phase 4**: WebRTC browser-based voice chat
- **Phase 5**: Voice analytics dashboard and cloud sync
- **Phase 6**: Multi-tenant mode for managing multiple properties

## Business Context
- Part of the **StayHive.ai** hospitality ecosystem (connected to BizHive.cloud)
- Designed for independent hotels, B&Bs, and hostels that need enterprise capabilities
- Can operate completely standalone or sync to cloud for analytics and remote monitoring
