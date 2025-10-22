# Voice Module Implementation Plan

## Quick Start Guide

### Prerequisites
```bash
# 1. Set up Twilio account
- Sign up at https://www.twilio.com
- Get Account SID, Auth Token, and Phone Number
- Configure webhook URL

# 2. Set up OpenAI account
- API key with Realtime API access
- Enable GPT-4o Realtime model

# 3. Install dependencies
pip install -r requirements.txt
```

### Rapid Deployment (5 Minutes)

```bash
# 1. Configure environment
cp .env.local .env
# Edit .env with your credentials

# 2. Build and run
./deploy-cloud-run.sh

# 3. Test voice endpoint
curl http://localhost:8000/health
```

---

## Phase 1: Core Infrastructure (Days 1-2)

### Day 1: Voice Gateway & Session Management

**Files to Create**:
- `packages/voice/__init__.py`
- `packages/voice/gateway.py`
- `packages/voice/session.py`
- `packages/voice/models.py`

**Implementation Checklist**:
- [x] Voice module structure
- [ ] VoiceGateway class with Twilio integration
- [ ] SessionManager for call tracking
- [ ] Database models (VoiceCall, ConversationTurn)
- [ ] Basic Twilio webhook handlers (inbound/status)
- [ ] Session CRUD operations

**Testing**:
```bash
# Unit tests
pytest tests/unit/test_voice_gateway.py
pytest tests/unit/test_session_manager.py

# Integration test with Twilio
# (Requires Twilio test credentials)
pytest tests/integration/test_twilio_webhook.py
```

**Validation Criteria**:
- ✓ Can receive Twilio webhook and create session
- ✓ Can track active sessions in memory
- ✓ Can save session to database
- ✓ Can retrieve session history

---

### Day 2: Audio Processing Pipeline

**Files to Create**:
- `packages/voice/audio.py`
- `packages/voice/codecs.py`
- `packages/voice/recording.py`

**Implementation Checklist**:
- [ ] AudioProcessor class
- [ ] Codec support (μ-law, PCM, Opus)
- [ ] Audio buffering and chunking
- [ ] Voice Activity Detection (VAD)
- [ ] AudioRecorder for call recording
- [ ] Format conversion utilities

**Testing**:
```bash
pytest tests/unit/test_audio_processor.py
pytest tests/unit/test_audio_recording.py

# Test with sample audio files
python -m packages.voice.audio --test-file tests/fixtures/sample_call.wav
```

**Validation Criteria**:
- ✓ Can decode Twilio μ-law audio
- ✓ Can detect speech vs silence
- ✓ Can record and save audio files
- ✓ Can convert between audio formats

---

## Phase 2: Speech Services (Days 3-4)

### Day 3: Speech-to-Text (STT)

**Files to Create**:
- `packages/voice/stt.py`
- `packages/voice/engines/whisper.py`
- `packages/voice/engines/deepgram.py` (optional)

**Implementation Checklist**:
- [ ] STTEngine base class
- [ ] WhisperSTT implementation (batch)
- [ ] WhisperSTT streaming support
- [ ] Language detection
- [ ] Error handling and retries
- [ ] Caching for repeated phrases

**Testing**:
```bash
pytest tests/unit/test_stt_engine.py

# Test with real audio
python -m packages.voice.stt --audio tests/fixtures/hello.wav
```

**Validation Criteria**:
- ✓ Can transcribe English audio with >90% accuracy
- ✓ Can detect language (English, Spanish, etc.)
- ✓ Can handle streaming audio
- ✓ Latency < 1 second for short utterances

---

### Day 4: Text-to-Speech (TTS)

**Files to Create**:
- `packages/voice/tts.py`
- `packages/voice/engines/openai_tts.py`
- `packages/voice/engines/elevenlabs.py` (optional)

**Implementation Checklist**:
- [ ] TTSEngine base class
- [ ] OpenAITTS implementation
- [ ] Voice selection (alloy, echo, nova, etc.)
- [ ] SSML support for pronunciations
- [ ] Streaming TTS for low latency
- [ ] Audio caching for common phrases

**Testing**:
```bash
pytest tests/unit/test_tts_engine.py

# Test synthesis
python -m packages.voice.tts --text "Welcome to our hotel" --voice alloy
```

**Validation Criteria**:
- ✓ Can synthesize natural-sounding speech
- ✓ Multiple voice options available
- ✓ Streaming TTS works smoothly
- ✓ Latency < 500ms for short responses

---

## Phase 3: Tool Integration (Days 5-6)

### Day 5: Voice-Enabled Tools

**Files to Create**:
- `packages/voice/tools.py`
- `packages/voice/tool_orchestrator.py`

**Implementation Checklist**:
- [ ] Voice-specific tools (transfer, hold, SMS)
- [ ] Modify existing tools for voice context
- [ ] Tool orchestrator for function routing
- [ ] Response formatting for voice
- [ ] Error handling with voice feedback

**Modify Existing Files**:
- `packages/tools/check_availability.py` - Add voice_session_id param
- `packages/tools/create_lead.py` - Add voice confirmation
- `packages/tools/generate_payment_link.py` - Send via SMS

**Testing**:
```bash
pytest tests/unit/test_voice_tools.py
pytest tests/integration/test_tool_orchestration.py

# E2E test: Complete booking via voice
pytest tests/e2e/test_voice_booking_flow.py
```

**Validation Criteria**:
- ✓ Can check availability via voice
- ✓ Can create lead from phone conversation
- ✓ Can send payment link via SMS
- ✓ Can transfer call to human

---

### Day 6: IVR & Call Flow

**Files to Create**:
- `packages/voice/ivr.py`
- `packages/voice/call_flow.py`

**Implementation Checklist**:
- [ ] IVR menu system
- [ ] DTMF input handling
- [ ] Multi-level menu navigation
- [ ] Call routing logic
- [ ] Hold music and announcements
- [ ] Callback scheduling

**Testing**:
```bash
pytest tests/unit/test_ivr_menu.py
pytest tests/integration/test_call_flow.py
```

**Validation Criteria**:
- ✓ Can navigate IVR menu via DTMF
- ✓ Can route to appropriate department
- ✓ Can schedule callbacks
- ✓ Hold music plays during processing

---

## Phase 4: OpenAI Realtime API (Days 7-8)

### Day 7: Realtime API Client

**Files to Create**:
- `packages/voice/realtime.py`
- `packages/voice/realtime_client.py`
- `packages/voice/function_registry.py`

**Implementation Checklist**:
- [ ] RealtimeAPIClient with WebSocket
- [ ] Audio streaming to/from Realtime API
- [ ] Function calling registration
- [ ] Context injection for hotel info
- [ ] Error handling and reconnection
- [ ] Session state management

**Testing**:
```bash
pytest tests/unit/test_realtime_client.py
pytest tests/integration/test_realtime_api.py

# Live test with OpenAI
python -m packages.voice.realtime --test-conversation
```

**Validation Criteria**:
- ✓ Can establish WebSocket to Realtime API
- ✓ Can stream audio bidirectionally
- ✓ Can register and call functions
- ✓ Low latency (<500ms round-trip)

---

### Day 8: Twilio ↔ Realtime Bridge

**Files to Create**:
- `packages/voice/bridges/twilio_realtime.py`

**Implementation Checklist**:
- [ ] Bridge Twilio audio stream to Realtime API
- [ ] Handle audio format conversion
- [ ] Manage dual WebSocket connections
- [ ] Handle interruptions and barge-in
- [ ] Stream recording while bridging
- [ ] Error recovery

**Testing**:
```bash
# Full integration test
pytest tests/integration/test_twilio_realtime_bridge.py

# Manual test: Call phone number and verify AI responds
```

**Validation Criteria**:
- ✓ Can receive phone call and connect to Realtime API
- ✓ Guest can have natural conversation
- ✓ AI can call functions (check availability, etc.)
- ✓ Conversation feels natural (<500ms latency)

---

## Phase 5: WebRTC Support (Days 9-10)

### Day 9: WebRTC Server

**Files to Create**:
- `packages/voice/webrtc.py`
- `packages/voice/signaling.py`
- `static/voice-client.html`
- `static/js/voice-client.js`

**Implementation Checklist**:
- [ ] WebRTC signaling server
- [ ] ICE candidate exchange
- [ ] STUN/TURN server configuration
- [ ] Browser audio capture/playback
- [ ] Connection quality monitoring
- [ ] Fallback to HTTP polling

**Testing**:
```bash
pytest tests/integration/test_webrtc_signaling.py

# Manual browser test
# Open http://localhost:8000/static/voice-client.html
```

**Validation Criteria**:
- ✓ Can establish WebRTC connection from browser
- ✓ Can stream audio to/from browser
- ✓ Works across different browsers
- ✓ Handles network quality issues gracefully

---

### Day 10: Browser Voice Client

**Files to Create**:
- `static/js/audio-worklet.js`
- `static/css/voice-client.css`

**Implementation Checklist**:
- [ ] Professional UI for voice chat
- [ ] Microphone permission handling
- [ ] Visual feedback (waveform, talking indicator)
- [ ] Mute/unmute controls
- [ ] Call quality indicators
- [ ] Mobile-responsive design

**Testing**:
```bash
# Browser compatibility tests
npm run test:browser

# Mobile device testing
# (Use ngrok or similar for HTTPS)
```

**Validation Criteria**:
- ✓ Works on Chrome, Firefox, Safari
- ✓ Works on mobile devices
- ✓ Clear visual feedback
- ✓ Intuitive user interface

---

## Phase 6: Analytics & Cloud Sync (Days 11-12)

### Day 11: Voice Analytics

**Files to Create**:
- `packages/voice/analytics.py`
- `packages/voice/sentiment.py`

**Implementation Checklist**:
- [ ] Call metrics collection
- [ ] Sentiment analysis
- [ ] Tool usage tracking
- [ ] Performance metrics (latency, errors)
- [ ] Guest satisfaction scoring
- [ ] Analytics dashboard endpoint

**Testing**:
```bash
pytest tests/unit/test_voice_analytics.py

# Generate analytics report
python -m packages.voice.analytics --report --days 7
```

**Validation Criteria**:
- ✓ Tracks all key metrics
- ✓ Sentiment analysis accuracy >80%
- ✓ Dashboard shows real-time data
- ✓ Can export analytics to CSV/JSON

---

### Day 12: Cloud Sync Integration

**Files to Modify**:
- `mcp_servers/shared/cloud_sync.py`

**Implementation Checklist**:
- [ ] Add `sync_voice_call()` method
- [ ] Add `push_voice_analytics()` method
- [ ] Sync conversation transcripts
- [ ] Sync recordings (if enabled)
- [ ] Handle sync failures gracefully
- [ ] Batch sync for efficiency

**Testing**:
```bash
pytest tests/integration/test_cloud_sync_voice.py

# Test with actual BizHive.cloud endpoint
BIZHIVE_CLOUD_ENABLED=true pytest tests/integration/test_cloud_sync_voice.py
```

**Validation Criteria**:
- ✓ Voice calls sync to BizHive.cloud
- ✓ Analytics push successfully
- ✓ Offline mode works without cloud
- ✓ Retry logic handles failures

---

## Phase 7: Production Hardening (Days 13-14)

### Day 13: Error Handling & Monitoring

**Files to Create**:
- `packages/voice/monitoring.py`
- `packages/voice/error_handlers.py`

**Implementation Checklist**:
- [ ] Comprehensive error handling
- [ ] Retry logic for transient failures
- [ ] Circuit breaker for external services
- [ ] Health check endpoint for voice services
- [ ] Prometheus metrics export
- [ ] Sentry error tracking integration

**Testing**:
```bash
# Chaos testing
pytest tests/chaos/test_voice_resilience.py

# Load testing
locust -f tests/load/voice_load_test.py --users 50 --spawn-rate 5
```

**Validation Criteria**:
- ✓ Handles network failures gracefully
- ✓ Recovers from API errors
- ✓ Provides clear error messages to users
- ✓ Metrics exported correctly

---

### Day 14: Security & Documentation

**Files to Create**:
- `docs/VOICE_API.md`
- `docs/VOICE_DEPLOYMENT.md`
- `docs/VOICE_TROUBLESHOOTING.md`

**Implementation Checklist**:
- [ ] Verify Twilio webhook signatures
- [ ] Rate limiting on voice endpoints
- [ ] Input validation and sanitization
- [ ] Encrypt recordings at rest
- [ ] PCI compliance review
- [ ] Security audit checklist
- [ ] Complete API documentation
- [ ] Deployment guide
- [ ] Troubleshooting guide

**Testing**:
```bash
# Security tests
pytest tests/security/test_voice_security.py

# Penetration testing
npm run test:security
```

**Validation Criteria**:
- ✓ All security tests pass
- ✓ No sensitive data in logs
- ✓ Recordings encrypted
- ✓ Documentation complete

---

## Deployment Checklist

### Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.local .env
# Edit .env with credentials

# 3. Run locally
./run_local.sh

# 4. Test locally
curl http://localhost:8000/voice/health
```

### Cloud Run Deployment
```bash
# 1. Build and deploy
./deploy-cloud-run.sh

# 2. Configure Twilio webhook
# Set webhook URL to: https://YOUR-DOMAIN/voice/twilio/inbound

# 3. Test production
curl https://YOUR-DOMAIN/voice/health
```

### Twilio Configuration
1. Log in to Twilio Console
2. Navigate to Phone Numbers → Manage → Active Numbers
3. Select your phone number
4. Configure Voice & Fax:
   - **Accept Incoming**: Voice Calls
   - **Configure With**: Webhooks, TwiML Bins, Functions, Studio, or Proxy
   - **A Call Comes In**: Webhook
   - **URL**: `https://YOUR-DOMAIN/voice/twilio/inbound`
   - **HTTP Method**: POST
5. Save configuration

### Environment Variables
```env
# Required for production
VOICE_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

# Optional
VOICE_RECORDING_ENABLED=true
RECORDING_STORAGE=s3
S3_RECORDINGS_BUCKET=hotel-recordings
DEFAULT_LANGUAGE=en-US
MAX_CALL_DURATION_MINUTES=30
```

---

## Success Metrics & KPIs

### Technical Metrics
- **Uptime**: >99.9%
- **Call Success Rate**: >95%
- **Average Latency**: <500ms (STT + LLM + TTS)
- **Concurrent Calls**: Support 50+ simultaneous
- **Error Rate**: <1%

### Business Metrics
- **Automation Rate**: 80% of calls handled without human
- **Average Call Duration**: <3 minutes
- **Guest Satisfaction**: 4.5+ / 5.0
- **Booking Conversion**: 30% of inquiries → reservations
- **After-Hours Bookings**: 50% increase

### Cost Metrics
- **Cost per Call**: <$0.50 (Twilio + OpenAI)
- **Cost per Booking**: <$5.00
- **ROI**: 10x within 6 months

---

## Troubleshooting Guide

### Common Issues

**1. "Twilio webhook returns 500 error"**
```bash
# Check logs
docker logs hotel-operator-agent

# Verify webhook signature
python -m packages.voice.gateway --verify-webhook

# Test locally with ngrok
ngrok http 8000
# Update Twilio webhook to ngrok URL
```

**2. "Audio quality is poor"**
```bash
# Check codec configuration
# Ensure Twilio is sending μ-law 8kHz mono

# Test audio pipeline
python -m packages.voice.audio --test-codec ulaw

# Check network latency
ping your-domain.com
```

**3. "OpenAI Realtime API connection fails"**
```bash
# Verify API key
python -m packages.voice.realtime --test-connection

# Check model availability
# Ensure you have access to gpt-4o-realtime-preview

# Check logs for WebSocket errors
tail -f logs/voice.log | grep realtime
```

**4. "Calls are not being recorded"**
```bash
# Check recording configuration
echo $VOICE_RECORDING_ENABLED  # Should be "true"

# Check storage
python -m packages.voice.recording --test-storage

# Verify S3 credentials (if using S3)
aws s3 ls s3://$S3_RECORDINGS_BUCKET
```

---

## Next Steps

After completing all phases:

1. **Beta Testing**
   - Deploy to pilot hotel
   - Monitor first 100 calls closely
   - Gather guest feedback
   - Iterate on conversation flows

2. **Optimization**
   - Reduce latency further
   - Optimize costs
   - Improve transcription accuracy
   - Add more languages

3. **Scale**
   - Support multiple properties
   - Multi-tenant architecture
   - Load balancing
   - Geographic distribution

4. **Advanced Features**
   - Voice biometrics
   - Proactive outbound calls
   - Integration with smart rooms
   - Multilingual support

---

## Resources

### Documentation
- [Twilio Voice API Docs](https://www.twilio.com/docs/voice)
- [OpenAI Realtime API Docs](https://platform.openai.com/docs/guides/realtime)
- [WebRTC Docs](https://webrtc.org/getting-started/overview)

### Code Examples
- `examples/voice/simple_call.py` - Basic phone call handling
- `examples/voice/webrtc_demo.html` - Browser voice chat
- `examples/voice/realtime_demo.py` - OpenAI Realtime integration

### Support
- GitHub Issues: https://github.com/stayhive/front-desk/issues
- Discord Community: https://discord.gg/stayhive
- Email Support: support@stayhive.ai
