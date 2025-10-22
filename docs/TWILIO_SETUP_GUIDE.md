# Twilio Setup Guide for Front Desk Operator Agent

This guide walks you through setting up Twilio for voice interactions with your hotel AI concierge.

## Prerequisites

- [x] Python 3.11+ installed
- [x] Virtual environment activated
- [x] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Twilio account (free trial works!)
- [ ] ngrok installed (for local testing)

## Step 1: Get Your Twilio Credentials

### 1.1 Create/Login to Twilio Account
1. Go to [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up for a free account (includes $15 credit)
3. Verify your phone number

### 1.2 Find Your Account SID and Auth Token
1. Go to [Twilio Console](https://console.twilio.com/)
2. On the dashboard, you'll see:
   - **Account SID**: Starts with `AC...` (e.g., `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
   - **Auth Token**: Click "Show" to reveal it
3. **IMPORTANT**: Use the main Account SID (starts with `AC`), NOT an API Key SID (starts with `SK`)

### 1.3 Get a Phone Number
1. Go to [Phone Numbers → Manage → Buy a number](https://console.twilio.com/us1/develop/phone-numbers/manage/search)
2. Select your country
3. Check "Voice" under capabilities
4. Click "Search" and choose a number
5. Click "Buy" (uses your free credit)

## Step 2: Configure Environment Variables

Edit your [.env.local](../.env.local) file:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Your Account SID (starts with AC)
TWILIO_AUTH_TOKEN=your_auth_token_here                  # Your Auth Token
TWILIO_PHONE_NUMBER=+1234567890                        # Your Twilio number

# Webhook URLs (update after ngrok setup)
TWILIO_WEBHOOK_URL=http://localhost:8000               # Will update to ngrok URL
VOICE_WEBSOCKET_URL=ws://localhost:8000                # Will update to ngrok URL
```

### Important Notes:
- **TWILIO_ACCOUNT_SID**: Must be your main Account SID (starts with `AC`)
  - ❌ NOT an API Key SID (starts with `SK`)
  - ✅ Main Account SID (starts with `AC`)
- **TWILIO_AUTH_TOKEN**: Your Auth Token (not an API Key Secret)
- **TWILIO_PHONE_NUMBER**: Include country code (e.g., `+1` for US)

## Step 3: Verify Your Setup

Run the verification script:

```bash
# From project root
. venv/bin/activate
python scripts/verify_twilio_setup.py
```

You should see:
```
✅ Env Vars
✅ Credentials
✅ Phone Number
✅ Webhook
```

If you see errors:
- **❌ Credentials**: Check your Account SID (must start with `AC`)
- **❌ Phone Number**: Verify the number is in your Twilio account
- **❌ Webhook**: Server might not be running (this is OK for now)

## Step 4: Start the Server

```bash
# Terminal 1: Start the FastAPI server
cd /home/webemo-aaron/projects/front-desk
. venv/bin/activate
export PYTHONPATH=/home/webemo-aaron/projects/front-desk:$PYTHONPATH
python apps/operator-runtime/main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Test it:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/voice/health
```

## Step 5: Setup ngrok (for Local Testing)

Twilio needs a public URL to send webhooks. ngrok creates a tunnel to your localhost.

### 5.1 Install ngrok

**Option 1: Download from website**
```bash
# Go to https://ngrok.com/download
# Download for your OS and follow instructions
```

**Option 2: Package manager (recommended for WSL/Linux)**
```bash
# Debian/Ubuntu
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# Sign up at https://ngrok.com to get your auth token
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### 5.2 Start ngrok

```bash
# Terminal 2: Start ngrok
ngrok http 8000
```

You'll see something like:
```
Forwarding    https://abc123def456.ngrok.io -> http://localhost:8000
```

**Copy the `https://` URL** - you'll need it for the next step!

## Step 6: Configure Twilio Webhooks

1. Go to [Twilio Console → Phone Numbers](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
2. Click on your phone number
3. Scroll to **Voice Configuration**

Configure these settings:

| Setting | Value |
|---------|-------|
| **A CALL COMES IN** | Webhook |
| **URL** | `https://YOUR-NGROK-URL.ngrok.io/voice/twilio/inbound` |
| **HTTP** | POST |
| **PRIMARY HANDLER FAILS** | (leave default) |

4. Scroll to **Call Status Changes**

| Setting | Value |
|---------|-------|
| **URL** | `https://YOUR-NGROK-URL.ngrok.io/voice/twilio/status` |
| **HTTP** | POST |

5. Click **Save Configuration**

### Example with real ngrok URL:
If ngrok shows `https://abc123def456.ngrok.io`, configure:
- **Voice URL**: `https://abc123def456.ngrok.io/voice/twilio/inbound`
- **Status URL**: `https://abc123def456.ngrok.io/voice/twilio/status`

## Step 7: Test Your Setup!

### 7.1 Call Your Number
Call your Twilio number from your phone: **+12072203501** (or your number)

You should hear:
> "Thank you for calling. Please wait while we connect you to our AI concierge."

### 7.2 Monitor the Call

**Terminal 3: Watch sessions**
```bash
# Check active sessions
curl http://localhost:8000/voice/sessions | jq

# Get specific session details
curl http://localhost:8000/voice/sessions/SESSION_ID | jq
```

**Terminal 1 (server logs)**: You'll see:
```
INFO:     Incoming call from +1234567890 to +12072203501 (SID: CA...)
INFO:     Created session abc-123 for call CA...
INFO:     Media stream WebSocket connected
```

**Twilio Console**:
- Go to [Monitor → Logs → Calls](https://console.twilio.com/us1/monitor/logs/calls)
- You'll see the call details and any errors

### 7.3 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Call doesn't connect** | Check ngrok is running and webhook URLs are correct |
| **"Application error" message** | Check server logs (Terminal 1) for errors |
| **No voice/silence** | Check audio processing is working (OpenAI API key set) |
| **Webhook errors** | Verify webhook URLs end with `/voice/twilio/inbound` |
| **Call connects but ends immediately** | Check WebSocket URL is configured correctly |

## Step 8: Production Deployment (Optional)

For production, replace ngrok with:

### Option 1: Google Cloud Run
```bash
# Already configured! See deploy-cloud-run.sh
./deploy-cloud-run.sh

# Get your Cloud Run URL
gcloud run services describe hotel-operator-agent --region us-central1 --format 'value(status.url)'
```

Update Twilio webhooks to:
- **Voice URL**: `https://YOUR-CLOUD-RUN-URL.run.app/voice/twilio/inbound`
- **Status URL**: `https://YOUR-CLOUD-RUN-URL.run.app/voice/twilio/status`

### Option 2: Your Own Domain
If you have your own server/domain:

1. Deploy the app to your server
2. Set up SSL/TLS (required by Twilio)
3. Update webhook URLs to `https://yourdomain.com/voice/twilio/inbound`

## Available Voice Endpoints

Once configured, your voice gateway exposes these endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/voice/health` | GET | Voice service health check |
| `/voice/twilio/inbound` | POST | Twilio incoming call webhook |
| `/voice/twilio/status` | POST | Call status updates |
| `/voice/twilio/stream` | WebSocket | Real-time audio streaming |
| `/voice/sessions` | GET | List active voice sessions |
| `/voice/sessions/{id}` | GET | Get session details |
| `/voice/sessions/{id}/end` | POST | End a session |

## Testing Without a Phone Call

You can test the endpoints directly:

```bash
# Health check
curl http://localhost:8000/voice/health

# Simulate incoming call (POST with Twilio parameters)
curl -X POST http://localhost:8000/voice/twilio/inbound \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=CAtest123" \
  -d "From=%2B1234567890" \
  -d "To=%2B12072203501"

# List sessions
curl http://localhost:8000/voice/sessions
```

## Environment Variables Reference

Complete list of voice-related environment variables:

```bash
# === REQUIRED ===
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Main Account SID (starts with AC)
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# === WEBHOOK URLS ===
TWILIO_WEBHOOK_URL=https://your-ngrok-or-domain.com  # No trailing slash
VOICE_WEBSOCKET_URL=wss://your-ngrok-or-domain.com   # Use wss:// for production

# === VOICE MODULE ===
VOICE_ENABLED=true
VOICE_RECORDING_ENABLED=true
DEFAULT_LANGUAGE=en-US
MAX_CALL_DURATION_MINUTES=30

# === OPENAI (for voice AI) ===
OPENAI_API_KEY=sk-...
OPENAI_REALTIME_ENABLED=true
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17
OPENAI_REALTIME_VOICE=alloy  # alloy, echo, fable, onyx, nova, shimmer

# === HOTEL CONTEXT ===
HOTEL_NAME=West Bethel Motel
HOTEL_LOCATION=West Bethel, ME
HOTEL_CHECKIN_TIME=4:00 PM
HOTEL_CHECKOUT_TIME=10:00 AM
HOTEL_PET_POLICY=Pets welcome with $40 fee

# === DEPARTMENT PHONES (for call transfer) ===
FRONT_DESK_PHONE=+12072203501
HOUSEKEEPING_PHONE=+12072004023
MANAGEMENT_PHONE=+12072204023

# === HOLD MUSIC ===
HOLD_MUSIC_URL=https://assets.stayhive.ai/hold-music/gentle-piano.mp3
```

## Next Steps

1. ✅ **Test basic call handling** - Call your number and verify it connects
2. 🔄 **Enable OpenAI Realtime API** - For natural voice conversations
3. 📊 **Monitor call quality** - Check session logs and recordings
4. 🚀 **Deploy to production** - Use Cloud Run or your own server
5. 🎨 **Customize greetings** - Update voice prompts in gateway.py
6. 📞 **Add more tools** - Call transfer, SMS confirmations, etc.

## Resources

- [Twilio Console](https://console.twilio.com/)
- [Twilio Voice Webhooks Docs](https://www.twilio.com/docs/voice/twiml/webhook)
- [ngrok Documentation](https://ngrok.com/docs)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [Project Voice Module README](../packages/voice/README.md)

## Support

If you run into issues:

1. **Run the verification script**: `python scripts/verify_twilio_setup.py`
2. **Check server logs**: Look at Terminal 1 where the server is running
3. **Check Twilio logs**: [console.twilio.com/monitor/logs](https://console.twilio.com/us1/monitor/logs/calls)
4. **Check ngrok logs**: Look at the ngrok terminal or visit [http://localhost:4040](http://localhost:4040)

---

**Ready to test?** Follow Steps 1-7 above and call your Twilio number! 📞
