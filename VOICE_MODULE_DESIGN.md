# Voice Module Design - Hotel Operator Agent

## Executive Summary

This document outlines the design and implementation of a voice module for the Hotel Operator Agent, enabling 24/7 voice-based guest services through phone calls, WebRTC, and real-time voice interactions.

**Key Capabilities**:
- Inbound/outbound phone calls via Twilio
- WebRTC browser-based voice chat
- OpenAI Realtime API integration for natural conversations
- Session management and call recording
- Voice analytics and sentiment analysis
- Multi-language support
- Integration with existing hotel tools (availability, bookings, payments)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Voice Module Architecture                 │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Twilio     │────▶│   Voice      │────▶│   OpenAI     │
│   Phone      │     │   Gateway    │     │   Realtime   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
┌──────────────┐            │              ┌──────────────┐
│   WebRTC     │────────────┼─────────────▶│   Session    │
│   Browser    │            │              │   Manager    │
└──────────────┘            │              └──────────────┘
                            │
                     ┌──────▼──────┐
                     │   Audio     │
                     │  Processing │
                     └──────┬──────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
         ┌──────▼────┐ ┌───▼────┐ ┌───▼────┐
         │    STT    │ │  TTS   │ │  VAD   │
         │  Engine   │ │ Engine │ │ Engine │
         └──────┬────┘ └───┬────┘ └───┬────┘
                │           │           │
         ┌──────▼───────────▼───────────▼────┐
         │         Tool Orchestrator          │
         │  (check_availability, create_lead, │
         │   generate_payment_link, etc.)     │
         └────────────────┬───────────────────┘
                          │
                 ┌────────▼─────────┐
                 │  Database &      │
                 │  Cloud Sync      │
                 └──────────────────┘
```

---

## Component Design

### 1. Voice Gateway (`packages/voice/gateway.py`)

**Responsibilities**:
- Handle incoming/outgoing calls
- WebSocket connection management for real-time audio
- Protocol translation (Twilio ↔ WebRTC ↔ OpenAI Realtime)
- Audio stream routing

**Key Classes**:

```python
class VoiceGateway:
    """Main entry point for all voice interactions"""

    async def handle_twilio_call(self, call_sid: str, from_number: str)
    async def handle_webrtc_connection(self, websocket: WebSocket)
    async def handle_realtime_connection(self, session_id: str)
    async def route_audio_stream(self, stream: AudioStream, destination: str)
```

**Endpoints**:
- `POST /voice/twilio/inbound` - Twilio webhook for incoming calls
- `POST /voice/twilio/outbound` - Initiate outbound call
- `WS /voice/webrtc` - WebRTC audio streaming
- `WS /voice/realtime` - OpenAI Realtime API connection

---

### 2. Session Manager (`packages/voice/session.py`)

**Responsibilities**:
- Track active voice sessions
- Manage conversation state
- Handle session lifecycle (start, pause, resume, end)
- Store session metadata and recordings

**Key Classes**:

```python
class VoiceSession:
    """Represents a single voice interaction session"""

    session_id: str
    channel: str  # 'phone', 'webrtc', 'realtime'
    caller_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # 'active', 'on_hold', 'completed', 'failed'
    conversation_history: List[Message]
    tools_used: List[str]
    recording_url: Optional[str]

    async def add_message(self, role: str, content: str)
    async def execute_tool(self, tool_name: str, params: dict)
    async def end_session(self)

class SessionManager:
    """Manages all active voice sessions"""

    async def create_session(self, channel: str, caller_id: str) -> VoiceSession
    async def get_session(self, session_id: str) -> VoiceSession
    async def end_session(self, session_id: str)
    async def get_active_sessions(self) -> List[VoiceSession]
```

---

### 3. Audio Processing Pipeline (`packages/voice/audio.py`)

**Responsibilities**:
- Audio codec handling (μ-law, PCM, Opus, etc.)
- Audio stream buffering and chunking
- Voice Activity Detection (VAD)
- Audio format conversion
- Recording and playback

**Key Classes**:

```python
class AudioProcessor:
    """Process audio streams for voice interactions"""

    async def decode_audio(self, audio_data: bytes, codec: str) -> np.ndarray
    async def encode_audio(self, audio_array: np.ndarray, codec: str) -> bytes
    async def detect_speech(self, audio_data: bytes) -> bool
    async def chunk_audio(self, stream: AudioStream, chunk_size: int)

class AudioRecorder:
    """Record and store voice sessions"""

    async def start_recording(self, session_id: str)
    async def append_audio(self, audio_data: bytes)
    async def stop_recording(self) -> str  # Returns recording URL
```

---

### 4. Speech-to-Text Engine (`packages/voice/stt.py`)

**Responsibilities**:
- Convert audio to text
- Support multiple providers (OpenAI Whisper, Google STT, Deepgram)
- Handle streaming and batch transcription
- Language detection

**Key Classes**:

```python
class STTEngine:
    """Base class for speech-to-text engines"""

    async def transcribe_stream(self, audio_stream: AudioStream) -> AsyncIterator[str]
    async def transcribe_batch(self, audio_data: bytes) -> str
    async def detect_language(self, audio_data: bytes) -> str

class WhisperSTT(STTEngine):
    """OpenAI Whisper implementation"""

class DeepgramSTT(STTEngine):
    """Deepgram streaming STT implementation"""
```

---

### 5. Text-to-Speech Engine (`packages/voice/tts.py`)

**Responsibilities**:
- Convert text to natural speech
- Support multiple voices and languages
- Handle SSML for pronunciation control
- Streaming TTS for low latency

**Key Classes**:

```python
class TTSEngine:
    """Base class for text-to-speech engines"""

    async def synthesize_stream(self, text: str, voice: str) -> AsyncIterator[bytes]
    async def synthesize_batch(self, text: str, voice: str) -> bytes
    async def list_voices(self) -> List[Voice]

class OpenAITTS(TTSEngine):
    """OpenAI TTS implementation"""

class ElevenLabsTTS(TTSEngine):
    """ElevenLabs high-quality TTS"""
```

---

### 6. Realtime API Integration (`packages/voice/realtime.py`)

**Responsibilities**:
- Integration with OpenAI Realtime API
- Function calling for hotel tools
- Conversation flow management
- Context injection

**Key Classes**:

```python
class RealtimeAPIClient:
    """OpenAI Realtime API client for voice conversations"""

    async def connect(self, session_id: str)
    async def send_audio(self, audio_data: bytes)
    async def receive_audio(self) -> AsyncIterator[bytes]
    async def register_functions(self, functions: List[Function])
    async def inject_context(self, context: dict)
    async def handle_function_call(self, function_name: str, args: dict)
```

---

### 7. Voice Tools (`packages/voice/tools.py`)

**Responsibilities**:
- Voice-specific tool implementations
- Integration with existing hotel tools
- Call transfer and escalation
- IVR menu handling

**Voice-Specific Tools**:

```python
async def transfer_to_human(session_id: str, department: str) -> dict:
    """Transfer call to a human operator"""

async def play_hold_music(session_id: str, duration: int) -> dict:
    """Play music while processing request"""

async def send_sms_confirmation(phone: str, message: str) -> dict:
    """Send SMS confirmation of booking or inquiry"""

async def schedule_callback(phone: str, time: datetime) -> dict:
    """Schedule a callback to guest"""

async def handle_ivr_menu(session_id: str, dtmf_input: str) -> dict:
    """Handle IVR menu selections"""

async def get_caller_history(phone: str) -> dict:
    """Retrieve previous interactions with this caller"""
```

---

### 8. Database Models (`packages/voice/models.py`)

**Voice-Specific Database Schema**:

```python
class VoiceCall(Base):
    __tablename__ = "voice_calls"

    id: int  # Primary key
    session_id: str  # UUID
    channel: str  # 'phone', 'webrtc', 'realtime'
    caller_id: str  # Phone number or user ID
    direction: str  # 'inbound', 'outbound'
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: int
    status: str  # 'completed', 'failed', 'missed', 'abandoned'
    recording_url: Optional[str]
    transcription: Optional[str]
    sentiment_score: Optional[float]
    language: str
    tools_executed: List[str]  # JSON array
    lead_id: Optional[int]  # Foreign key to leads
    reservation_id: Optional[int]  # Foreign key to reservations

class ConversationTurn(Base):
    __tablename__ = "conversation_turns"

    id: int
    call_id: int  # Foreign key to voice_calls
    turn_number: int
    role: str  # 'user', 'assistant', 'system'
    content: str
    audio_url: Optional[str]
    timestamp: datetime
    latency_ms: int

class VoiceAnalytics(Base):
    __tablename__ = "voice_analytics"

    id: int
    call_id: int
    metric_name: str
    metric_value: float
    timestamp: datetime
```

---

## Integration Points

### 1. FastAPI Application Integration

**Modify** `apps/operator-runtime/main.py`:

```python
from packages.voice.gateway import VoiceGateway
from packages.voice.session import SessionManager

# Initialize voice components
voice_gateway = VoiceGateway()
session_manager = SessionManager()

# Add voice routes
app.include_router(voice_gateway.router, prefix="/voice", tags=["voice"])

# WebSocket for WebRTC
@app.websocket("/voice/webrtc")
async def voice_webrtc(websocket: WebSocket):
    await voice_gateway.handle_webrtc_connection(websocket)
```

### 2. Tool Integration

**Extend existing tools for voice context**:

```python
# packages/tools/check_availability.py
async def check_availability(
    check_in: str,
    check_out: str,
    adults: int,
    pets: bool = False,
    voice_session_id: Optional[str] = None  # NEW
) -> dict:
    """
    Check room availability (voice-enabled)

    If voice_session_id is provided, can announce availability
    over the call in addition to returning data.
    """
    # Existing logic...

    if voice_session_id:
        # Format response for voice
        voice_response = format_for_voice(result)
        await announce_to_session(voice_session_id, voice_response)

    return result
```

### 3. Cloud Sync Integration

**Extend** `mcp_servers/shared/cloud_sync.py`:

```python
class CloudSyncManager:
    # Existing methods...

    async def sync_voice_call(self, call_data: dict) -> bool:
        """Sync voice call data to BizHive.cloud"""
        if not self.enabled:
            return False

        try:
            response = await self._post("/api/v1/voice/calls", call_data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to sync voice call: {e}")
            return False

    async def push_voice_analytics(self, analytics: List[dict]) -> bool:
        """Push voice analytics to cloud"""
        # Implementation...
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Voice gateway with basic Twilio integration
- [ ] Session manager for call tracking
- [ ] Audio processing pipeline (decode/encode)
- [ ] Database models for voice calls
- [ ] Basic STT/TTS with OpenAI Whisper

### Phase 2: Tool Integration (Week 2)
- [ ] Voice-enabled versions of existing tools
- [ ] IVR menu system
- [ ] Call transfer functionality
- [ ] SMS notification integration
- [ ] Voice-specific tools (hold music, callbacks)

### Phase 3: OpenAI Realtime API (Week 3)
- [ ] Realtime API client implementation
- [ ] Function calling integration
- [ ] Streaming audio to/from Realtime API
- [ ] Context injection for hotel knowledge

### Phase 4: WebRTC Support (Week 4)
- [ ] WebRTC signaling server
- [ ] Browser-based voice client
- [ ] WebSocket audio streaming
- [ ] Connection quality monitoring

### Phase 5: Analytics & Optimization (Week 5)
- [ ] Voice analytics dashboard
- [ ] Sentiment analysis integration
- [ ] Call quality metrics
- [ ] Cloud sync for voice data
- [ ] Performance optimization

### Phase 6: Production Hardening (Week 6)
- [ ] Error handling and retry logic
- [ ] Load testing and scaling
- [ ] Security audit (PCI compliance for payments)
- [ ] Documentation and deployment guides
- [ ] Monitoring and alerting

---

## Technology Stack

### Required Dependencies

**Add to `requirements.txt`**:

```txt
# Voice Processing
twilio>=8.10.0                    # Phone call handling
websockets>=12.0                  # WebSocket support
python-socketio>=5.10.0           # Socket.IO for WebRTC
aiortc>=1.6.0                     # WebRTC implementation

# Audio Processing
pydub>=0.25.1                     # Audio manipulation
numpy>=1.24.0                     # Audio array processing
scipy>=1.11.0                     # Signal processing
webrtcvad>=2.0.10                 # Voice Activity Detection

# Speech Services
openai>=1.3.0                     # Already included (Whisper + TTS)
deepgram-sdk>=3.0.0              # Streaming STT (optional)
elevenlabs>=0.2.0                # High-quality TTS (optional)

# Recording & Storage
boto3>=1.28.0                     # S3 for recordings (optional)
```

### Environment Variables

**Add to `.env.local`**:

```env
# Voice Configuration
VOICE_ENABLED=true
VOICE_RECORDING_ENABLED=true

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567
TWILIO_WEBHOOK_URL=https://your-domain.com/voice/twilio/inbound

# OpenAI Realtime
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17
OPENAI_VOICE=alloy

# Voice Settings
DEFAULT_LANGUAGE=en-US
VOICE_TIMEOUT_SECONDS=300
MAX_CALL_DURATION_MINUTES=30

# Recording Storage
RECORDING_STORAGE=s3  # or 'local'
S3_RECORDINGS_BUCKET=hotel-voice-recordings
```

---

## API Endpoints

### Voice Gateway Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/voice/twilio/inbound` | POST | Twilio webhook for incoming calls |
| `/voice/twilio/outbound` | POST | Initiate outbound call |
| `/voice/twilio/status` | POST | Twilio status callback |
| `/voice/webrtc` | WS | WebRTC audio streaming |
| `/voice/realtime` | WS | OpenAI Realtime API connection |
| `/voice/sessions` | GET | List active sessions |
| `/voice/sessions/{id}` | GET | Get session details |
| `/voice/sessions/{id}/end` | POST | End a session |
| `/voice/recordings/{id}` | GET | Retrieve call recording |
| `/voice/analytics` | GET | Voice analytics dashboard |

---

## Example Call Flow

### Inbound Phone Call (Twilio → OpenAI Realtime → Tools)

```
1. Guest calls hotel phone number
   ↓
2. Twilio receives call, sends webhook to /voice/twilio/inbound
   ↓
3. VoiceGateway creates VoiceSession
   ↓
4. VoiceGateway establishes WebSocket to OpenAI Realtime API
   ↓
5. Audio streams bidirectionally:
   Twilio → VoiceGateway → OpenAI Realtime → VoiceGateway → Twilio
   ↓
6. OpenAI Realtime calls functions (check_availability, create_lead, etc.)
   ↓
7. VoiceGateway executes tools and returns results to Realtime API
   ↓
8. OpenAI generates natural language response + TTS
   ↓
9. Guest hears response through phone
   ↓
10. Conversation continues until guest hangs up or timeout
    ↓
11. SessionManager saves call record, transcription, and analytics
    ↓
12. CloudSyncManager syncs data to BizHive.cloud (if enabled)
```

---

## Testing Strategy

### Unit Tests
- Audio codec conversions
- Session lifecycle management
- Tool execution with voice context
- Database model CRUD operations

### Integration Tests
- Twilio webhook handling
- WebRTC connection establishment
- OpenAI Realtime API integration
- Tool orchestration

### End-to-End Tests
- Complete call flow simulation
- Multi-turn conversations
- Error recovery scenarios
- Load testing with concurrent calls

### Test Files Structure
```
tests/
├── unit/
│   ├── test_voice_gateway.py
│   ├── test_session_manager.py
│   ├── test_audio_processor.py
│   └── test_voice_tools.py
├── integration/
│   ├── test_twilio_integration.py
│   ├── test_realtime_api.py
│   └── test_webrtc.py
└── e2e/
    ├── test_phone_call_flow.py
    └── test_webrtc_call_flow.py
```

---

## Security Considerations

### 1. Authentication & Authorization
- Verify Twilio webhook signatures
- Secure WebSocket connections with tokens
- Rate limiting on voice endpoints
- CAPTCHA for WebRTC connections

### 2. Data Privacy
- Encrypt recordings at rest (AES-256)
- Secure transmission (TLS 1.3)
- GDPR compliance for EU guests
- Automatic recording deletion policies

### 3. PCI Compliance
- Never record credit card numbers spoken over phone
- Use secure payment links instead of collecting cards
- Mask sensitive data in transcriptions
- Audit logs for all payment-related conversations

### 4. Infrastructure Security
- DDoS protection for WebSocket endpoints
- Input validation for DTMF and voice commands
- Prevent injection attacks in tool parameters
- Monitor for abuse and spam calls

---

## Monitoring & Observability

### Key Metrics
- **Call Volume**: Inbound/outbound calls per hour
- **Success Rate**: Completed vs failed calls
- **Average Duration**: Call length by intent
- **Latency**: STT/TTS/Tool execution times
- **Sentiment**: Customer satisfaction scores
- **Tool Usage**: Which tools are most used
- **Error Rate**: Transcription errors, tool failures

### Logging
- Structured JSON logs with correlation IDs
- Call session metadata
- Tool execution logs
- Error stack traces with context

### Alerting
- Call failure rate > 5%
- Average latency > 2 seconds
- Twilio account balance low
- Recording storage quota warning

---

## Cost Optimization

### Twilio Costs
- Use local phone numbers ($1/month vs toll-free $2/month)
- Implement call screening to reduce spam
- Set maximum call duration limits
- Monitor concurrent call capacity

### OpenAI Costs
- Cache frequently asked questions
- Use function calling to avoid verbose responses
- Implement conversation turn limits
- Consider hybrid approach (STT+GPT+TTS vs Realtime)

### Recording Storage
- Compress recordings (Opus codec)
- Auto-delete after retention period
- Use S3 Glacier for long-term archives
- Store only essential calls (filter spam)

---

## Future Enhancements

### Voice Features
- Multi-language support (Spanish, French, etc.)
- Voice biometrics for guest identification
- Proactive outbound calls (booking reminders)
- Voice-based authentication
- Integration with smart room devices

### AI Capabilities
- Emotion detection and empathy responses
- Personalized voice profiles per property
- Voice-based upselling recommendations
- Real-time translation for international guests

### Integration Expansions
- PMS system integration (Opera, Mews, etc.)
- CRM integration (Salesforce, HubSpot)
- Channel manager integration (Booking.com API)
- Smart concierge (restaurant reservations, local guides)

---

## Success Metrics

### Operational Efficiency
- **Target**: Handle 80% of routine inquiries without human intervention
- **Target**: Average call duration < 3 minutes for bookings
- **Target**: 95% accuracy in availability checks

### Guest Satisfaction
- **Target**: 4.5+ average sentiment score
- **Target**: <5% call transfer rate to humans
- **Target**: 90% of guests complete booking via voice

### Business Impact
- **Target**: 30% increase in after-hours bookings
- **Target**: 50% reduction in missed calls
- **Target**: 25% increase in direct bookings (vs OTA)

---

## Conclusion

This voice module transforms the Hotel Operator Agent into a complete 24/7 voice concierge, enabling independent hotels to provide enterprise-grade guest services without the cost of large chains. The modular architecture ensures easy integration with existing tools, scalability for multi-property deployments, and flexibility to adapt to future voice AI advancements.

**Next Steps**:
1. Review and approve this design
2. Set up Twilio account and phone numbers
3. Begin Phase 1 implementation
4. Test with pilot hotel property
5. Iterate based on real-world usage
