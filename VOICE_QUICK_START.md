# Voice Module - Quick Start Guide

Get the voice module up and running in 5 minutes.

## Prerequisites

- Python 3.11+
- Docker (optional, recommended)
- Twilio account (for phone calls)
- OpenAI API key (for future AI features)

---

## Option 1: Test Locally (No Phone Calls)

### Step 1: Install Dependencies

```bash
cd /home/webemo-aaron/projects/front-desk
pip install -r requirements.txt
```

### Step 2: Run the Example

```bash
python examples/voice/simple_call.py
```

**Expected Output**:
```
=== Voice Module - Simple Call Example ===

INFO:__main__:Creating new call session...
INFO:__main__:Session created: abc-123-xyz
INFO:__main__:Guest: Hello, I'd like to check room availability
INFO:__main__:AI: I'd be happy to help you check availability...
...
=== Example Complete ===
```

### Step 3: Run Unit Tests

```bash
pytest tests/unit/voice/ -v
```

**Expected Output**:
```
==================== 15 passed ====================
```

---

## Option 2: Run with Docker (Recommended)

### Step 1: Build and Run

```bash
./deploy-cloud-run.sh
```

### Step 2: Test Health Endpoint

```bash
curl http://localhost:8000/health
```

**Expected Response**:
```json
{
  "status": "ok",
  "service": "hotel-operator-agent",
  "version": "0.2.0",
  "voice_enabled": true,
  "voice_sessions": 0
}
```

### Step 3: Test Voice Health

```bash
curl http://localhost:8000/voice/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "voice_gateway",
  "twilio_configured": false,
  "active_sessions": 0
}
```

---

## Option 3: Connect Real Phone Calls (Twilio)

### Step 1: Get Twilio Credentials

1. Sign up at https://www.twilio.com/try-twilio
2. Get a phone number (free trial includes $15 credit)
3. Copy your Account SID and Auth Token

### Step 2: Configure Environment

Edit `.env.local`:

```env
VOICE_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567
```

### Step 3: Expose Local Server (for testing)

```bash
# Install ngrok (if you don't have it)
# https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8000
```

**Copy the ngrok URL** (e.g., `https://abc123.ngrok.io`)

### Step 4: Configure Twilio Webhook

1. Go to https://console.twilio.com/
2. Navigate to: **Phone Numbers → Manage → Active Numbers**
3. Click your phone number
4. Under "Voice & Fax":
   - **A Call Comes In**: Webhook
   - **URL**: `https://abc123.ngrok.io/voice/twilio/inbound`
   - **HTTP Method**: POST
5. Click **Save**

### Step 5: Test Phone Call

**Call your Twilio number** and you should hear:
> "Thank you for calling. Please wait while we connect you to our AI concierge."

### Step 6: Check Session in API

```bash
curl http://localhost:8000/voice/sessions
```

**You should see your active call session!**

---

## Troubleshooting

### "Voice module not available"

**Problem**: Voice dependencies not installed

**Solution**:
```bash
pip install twilio websockets pydub numpy scipy webrtcvad aiortc
```

---

### "Twilio webhook returns 500 error"

**Problem**: Server not running or webhook URL incorrect

**Solution**:
1. Ensure server is running: `./deploy-cloud-run.sh`
2. Check ngrok is running: `ngrok http 8000`
3. Update Twilio webhook with correct ngrok URL
4. Check server logs: `docker logs hotel-operator-agent`

---

### "No audio on phone call"

**Problem**: WebSocket connection issues

**Solution**:
1. This is expected in Phase 1 (audio processing not yet implemented)
2. Check logs for connection attempts
3. Verify ngrok is forwarding WebSocket connections
4. Phase 2 will implement full audio pipeline

---

### "twilio_configured: false"

**Problem**: Twilio credentials not set

**Solution**:
1. Check `.env.local` has correct credentials
2. Restart server after updating environment
3. Verify credentials at https://console.twilio.com/

---

## Next Steps

### 1. Explore the API

```bash
# List all active sessions
curl http://localhost:8000/voice/sessions

# Get specific session
curl http://localhost:8000/voice/sessions/{session_id}

# End a session
curl -X POST http://localhost:8000/voice/sessions/{session_id}/end
```

### 2. Test Voice Tools

```python
from packages.voice.tools import execute_voice_tool

# Transfer call
result = await execute_voice_tool(
    "transfer_to_human",
    session_id="abc-123",
    department="front_desk"
)

# Send SMS
result = await execute_voice_tool(
    "send_sms_confirmation",
    phone="+15551234567",
    message="Your reservation is confirmed!"
)
```

### 3. Customize Voice Responses

Edit department phone numbers in `.env.local`:

```env
FRONT_DESK_PHONE=+15555551234
HOUSEKEEPING_PHONE=+15555551235
MANAGEMENT_PHONE=+15555551236
```

### 4. Read Full Documentation

- **Architecture**: [VOICE_MODULE_DESIGN.md](VOICE_MODULE_DESIGN.md)
- **Implementation Plan**: [VOICE_IMPLEMENTATION_PLAN.md](VOICE_IMPLEMENTATION_PLAN.md)
- **API Reference**: [packages/voice/README.md](packages/voice/README.md)
- **Summary**: [VOICE_MODULE_SUMMARY.md](VOICE_MODULE_SUMMARY.md)

---

## Common Commands

```bash
# Start server
./deploy-cloud-run.sh

# Run tests
pytest tests/unit/voice/

# Run example
python examples/voice/simple_call.py

# Check health
curl http://localhost:8000/health

# Check voice health
curl http://localhost:8000/voice/health

# View active sessions
curl http://localhost:8000/voice/sessions

# Stop server
docker stop hotel-operator-agent
```

---

## What's Working Now (Phase 1)

✅ Session management
✅ Twilio webhook integration
✅ Call status tracking
✅ Voice tools (transfer, hold, SMS, IVR)
✅ Database models
✅ API endpoints
✅ Unit tests

## What's Coming Next (Phase 2+)

⏳ Audio processing (STT, TTS)
⏳ OpenAI Realtime API
⏳ WebRTC browser client
⏳ Voice analytics
⏳ Multi-language support

---

## Help & Support

- **Issues**: Check [VOICE_MODULE_DESIGN.md](VOICE_MODULE_DESIGN.md) troubleshooting section
- **Examples**: See [examples/voice/](examples/voice/)
- **Tests**: See [tests/unit/voice/](tests/unit/voice/)
- **GitHub**: https://github.com/stayhive/front-desk/issues

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Install deps | `pip install -r requirements.txt` |
| Run server | `./deploy-cloud-run.sh` |
| Test locally | `python examples/voice/simple_call.py` |
| Run tests | `pytest tests/unit/voice/` |
| Check health | `curl http://localhost:8000/voice/health` |
| List sessions | `curl http://localhost:8000/voice/sessions` |
| Expose local | `ngrok http 8000` |
| Stop server | `docker stop hotel-operator-agent` |

---

**You're ready to start using the voice module!** 🎉

For detailed information, see [VOICE_MODULE_SUMMARY.md](VOICE_MODULE_SUMMARY.md)
