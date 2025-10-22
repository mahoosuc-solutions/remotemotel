# Voice Module

Voice interaction capabilities for the Hotel Operator Agent.

## Features

- **Phone Calls via Twilio**: Handle inbound/outbound calls with real-time audio streaming
- **WebRTC Support**: Browser-based voice chat for web guests
- **Session Management**: Track all voice interactions with full conversation history
- **Voice Tools**: Call transfer, hold music, SMS confirmations, IVR menus
- **Analytics**: Call metrics, sentiment analysis, and performance tracking
- **Database Persistence**: Store call records, transcriptions, and analytics

## Architecture

```
packages/voice/
├── __init__.py           # Module exports
├── gateway.py            # Main voice gateway (Twilio, WebRTC)
├── session.py            # Session management
├── models.py             # Database models
├── tools.py              # Voice-specific tools
├── audio.py              # Audio processing (coming soon)
├── stt.py                # Speech-to-text (coming soon)
├── tts.py                # Text-to-speech (coming soon)
├── realtime.py           # OpenAI Realtime API (coming soon)
└── README.md             # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env.local` with your credentials:

```env
VOICE_ENABLED=true
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567
OPENAI_API_KEY=your_openai_key
```

### 3. Run the Server

```bash
./deploy-cloud-run.sh
```

### 4. Test the Voice Module

```bash
# Health check
curl http://localhost:8000/voice/health

# List active sessions
curl http://localhost:8000/voice/sessions
```

## Usage Examples

### Creating a Voice Session

```python
from packages.voice import SessionManager

manager = SessionManager()

session = await manager.create_session(
    channel="phone",
    caller_id="+15551234567",
    language="en-US"
)

print(f"Session ID: {session.session_id}")
```

### Adding Messages to Conversation

```python
session.add_message(
    role="user",
    content="I'd like to book a room"
)

session.add_message(
    role="assistant",
    content="I'd be happy to help you with that",
    latency_ms=250
)
```

### Using Voice Tools

```python
from packages.voice.tools import transfer_to_human, send_sms_confirmation

# Transfer call to front desk
result = await transfer_to_human(
    session_id=session.session_id,
    department="front_desk",
    reason="Guest needs special assistance"
)

# Send SMS confirmation
result = await send_sms_confirmation(
    phone="+15551234567",
    message="Your reservation is confirmed for January 15th. Confirmation: ABC123"
)
```

### Formatting Data for Voice

```python
from packages.voice.tools import format_for_voice

availability_data = {
    "available": 5,
    "check_in": "January 15th",
    "check_out": "January 17th"
}

voice_response = format_for_voice(availability_data, "availability")
# Returns: "Excellent! We have 5 rooms available from January 15th to January 17th."
```

## API Endpoints

All voice endpoints are prefixed with `/voice`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/voice/health` | GET | Voice service health check |
| `/voice/twilio/inbound` | POST | Twilio webhook for incoming calls |
| `/voice/twilio/status` | POST | Twilio status callbacks |
| `/voice/twilio/stream` | WS | Twilio media stream WebSocket |
| `/voice/sessions` | GET | List all active sessions |
| `/voice/sessions/{id}` | GET | Get specific session details |
| `/voice/sessions/{id}/end` | POST | End a session |
| `/voice/webrtc` | WS | WebRTC audio streaming |

## Voice Tools

### Built-in Tools

- **transfer_to_human**: Transfer call to a human operator
- **play_hold_music**: Play music while processing requests
- **send_sms_confirmation**: Send SMS to guest
- **schedule_callback**: Schedule a callback
- **handle_ivr_menu**: Process IVR menu selections
- **get_caller_history**: Retrieve previous interactions
- **record_voice_note**: Record a voice message
- **announce_to_session**: Speak a message via TTS
- **format_for_voice**: Format data for voice output

### Using Tools

```python
from packages.voice.tools import execute_voice_tool

result = await execute_voice_tool(
    "transfer_to_human",
    session_id="abc-123",
    department="front_desk",
    reason="Special request"
)
```

## Database Models

### VoiceCall

Represents a complete voice call session.

**Fields**:
- `session_id`: Unique identifier
- `channel`: 'phone', 'webrtc', 'realtime'
- `caller_id`: Phone number or user ID
- `direction`: 'inbound' or 'outbound'
- `start_time`, `end_time`: Call timestamps
- `duration_seconds`: Call duration
- `status`: 'active', 'completed', 'failed', etc.
- `recording_url`: Link to call recording
- `transcription`: Full conversation transcript
- `sentiment_score`: -1.0 to 1.0
- `tools_executed`: List of tools used
- `lead_id`, `reservation_id`: Related records

### ConversationTurn

Individual messages in a conversation.

**Fields**:
- `turn_number`: Sequential turn number
- `role`: 'user', 'assistant', 'system'
- `content`: Message text
- `audio_url`: Link to audio segment
- `latency_ms`: Response time
- `timestamp`: When message was sent

### VoiceAnalytics

Metrics and analytics for calls.

**Fields**:
- `metric_name`: Name of metric (e.g., 'response_latency_ms')
- `metric_value`: Numeric value
- `timestamp`: When metric was recorded

## Configuration

### Environment Variables

#### Required
- `VOICE_ENABLED`: Enable voice module (default: true)
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number

#### Optional
- `VOICE_RECORDING_ENABLED`: Enable call recording (default: true)
- `DEFAULT_LANGUAGE`: Language code (default: en-US)
- `MAX_CALL_DURATION_MINUTES`: Maximum call length (default: 30)
- `OPENAI_API_KEY`: For future Realtime API integration
- `OPENAI_REALTIME_MODEL`: Realtime model name
- `OPENAI_VOICE`: TTS voice (alloy, echo, nova, etc.)

#### Department Phones (for call transfer)
- `FRONT_DESK_PHONE`: Front desk number
- `HOUSEKEEPING_PHONE`: Housekeeping number
- `MANAGEMENT_PHONE`: Management number
- `MAINTENANCE_PHONE`: Maintenance number

#### Storage
- `RECORDING_STORAGE`: 'local' or 's3'
- `S3_RECORDINGS_BUCKET`: S3 bucket for recordings
- `AWS_ACCESS_KEY_ID`: AWS credentials
- `AWS_SECRET_ACCESS_KEY`: AWS credentials

### Twilio Webhook Configuration

1. Log in to Twilio Console
2. Go to Phone Numbers → Manage → Active Numbers
3. Select your phone number
4. Under "Voice & Fax":
   - A Call Comes In: **Webhook**
   - URL: `https://your-domain.com/voice/twilio/inbound`
   - HTTP Method: **POST**
5. Save

## Testing

### Unit Tests

```bash
# Run all voice tests
pytest tests/unit/voice/

# Run specific test file
pytest tests/unit/voice/test_session.py

# Run with coverage
pytest tests/unit/voice/ --cov=packages.voice
```

### Integration Tests

```bash
# Requires Twilio test credentials
pytest tests/integration/voice/
```

### Manual Testing

```bash
# 1. Start server
./deploy-cloud-run.sh

# 2. Use ngrok for public URL (required for Twilio)
ngrok http 8000

# 3. Update Twilio webhook to ngrok URL
# https://YOUR-NGROK-ID.ngrok.io/voice/twilio/inbound

# 4. Call your Twilio number
# You should hear the greeting and be connected
```

## Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Voice gateway with Twilio integration
- [x] Session management
- [x] Database models
- [x] Voice-specific tools
- [x] FastAPI integration
- [x] Unit tests

### Phase 2: Audio Processing (In Progress)
- [ ] Audio codec handling
- [ ] Voice Activity Detection
- [ ] Call recording
- [ ] Audio format conversion

### Phase 3: Speech Services (Planned)
- [ ] Speech-to-text (Whisper)
- [ ] Text-to-speech (OpenAI TTS)
- [ ] Streaming STT/TTS
- [ ] Language detection

### Phase 4: OpenAI Realtime API (Planned)
- [ ] Realtime API client
- [ ] Function calling integration
- [ ] Streaming audio bridge
- [ ] Context injection

### Phase 5: WebRTC Support (Planned)
- [ ] WebRTC signaling server
- [ ] Browser voice client
- [ ] Connection quality monitoring

### Phase 6: Analytics & Cloud Sync (Planned)
- [ ] Voice analytics dashboard
- [ ] Sentiment analysis
- [ ] Cloud sync for voice data
- [ ] Performance metrics

## Troubleshooting

### "Voice module not available"

**Solution**: Install voice dependencies:
```bash
pip install twilio websockets pydub numpy scipy webrtcvad aiortc
```

### "Twilio webhook returns 403 Forbidden"

**Solution**: Check webhook signature validation. Set `TWILIO_AUTH_TOKEN` correctly.

### "No active sessions showing"

**Solution**: Sessions are stored in memory. Restart clears sessions. For persistence, configure database connection.

### "Call connects but no audio"

**Solution**:
1. Check Twilio webhook URL is correct
2. Ensure WebSocket URL is accessible
3. Check firewall rules for WebSocket connections

## Contributing

When adding new voice features:

1. Follow the existing architecture patterns
2. Add unit tests for all new functionality
3. Update this README with new features
4. Add examples to the examples/ directory
5. Update VOICE_MODULE_DESIGN.md if changing architecture

## License

Part of the Front Desk Operator Agent project.

## Support

- GitHub Issues: https://github.com/stayhive/front-desk/issues
- Documentation: See VOICE_MODULE_DESIGN.md
- Implementation Plan: See VOICE_IMPLEMENTATION_PLAN.md
