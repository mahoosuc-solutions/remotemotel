# Twilio Quick Start Guide

**Get your AI hotel concierge answering calls in 10 minutes!**

## ⚡ Quick Setup (5 steps)

### 1️⃣ Get Twilio Credentials (2 min)

1. Sign up at [twilio.com/try-twilio](https://www.twilio.com/try-twilio) (free $15 credit)
2. From [Twilio Console](https://console.twilio.com/):
   - Copy **Account SID** (starts with `AC...`)
   - Copy **Auth Token** (click "Show")
3. Buy a phone number: [Phone Numbers → Buy](https://console.twilio.com/us1/develop/phone-numbers/manage/search)

### 2️⃣ Configure Environment (1 min)

Edit [.env.local](../.env.local):

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # ⚠️ Must start with AC
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

**Important**: Use Account SID (starts with `AC`), NOT API Key SID (starts with `SK`)

### 3️⃣ Start Server (1 min)

```bash
./start_voice_server.sh
```

Or manually:
```bash
. venv/bin/activate
export PYTHONPATH=/home/webemo-aaron/projects/front-desk:$PYTHONPATH
python apps/operator-runtime/main.py
```

Verify it's running:
```bash
curl http://localhost:8000/voice/health
```

### 4️⃣ Setup ngrok (2 min)

**Install ngrok** (one-time):
```bash
./scripts/setup_ngrok.sh
```

**Start ngrok** (every time):
```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### 5️⃣ Configure Twilio Webhooks (2 min)

1. Go to [Phone Numbers](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
2. Click your phone number
3. Under "Voice Configuration":
   - **A CALL COMES IN**: Webhook → `https://YOUR-NGROK-URL/voice/twilio/inbound` → POST
4. Under "Call Status Changes":
   - **URL**: `https://YOUR-NGROK-URL/voice/twilio/status` → POST
5. Click **Save**

## 🎉 Test It!

Call your Twilio number: **+12072203501** (or your number)

You should hear:
> "Thank you for calling. Please wait while we connect you to our AI concierge."

## 🔍 Troubleshooting

### Call doesn't connect
```bash
# Check server is running
curl http://localhost:8000/voice/health

# Check ngrok is running
curl https://YOUR-NGROK-URL/voice/health

# Verify credentials
python scripts/verify_twilio_setup.py
```

### "Application error" message
- Check server logs (terminal running server)
- Check [Twilio Logs](https://console.twilio.com/us1/monitor/logs/calls)
- Verify webhook URLs end with `/voice/twilio/inbound`

### Credential errors
Common mistake: Using API Key SID instead of Account SID

❌ **Wrong**: `TWILIO_ACCOUNT_SID=SKbb0d3bf...` (starts with SK)
✅ **Correct**: `TWILIO_ACCOUNT_SID=ACxxxxxxx...` (starts with AC)

Find your Account SID at the top of [Twilio Console](https://console.twilio.com/)

## 📊 Monitor Calls

**View active sessions:**
```bash
curl http://localhost:8000/voice/sessions | jq
```

**Twilio call logs:**
[console.twilio.com/monitor/logs/calls](https://console.twilio.com/us1/monitor/logs/calls)

**ngrok request inspector:**
[http://localhost:4040](http://localhost:4040) (when ngrok is running)

## 📚 Next Steps

- **Full Setup Guide**: [docs/TWILIO_SETUP_GUIDE.md](TWILIO_SETUP_GUIDE.md)
- **Voice Module Docs**: [packages/voice/README.md](../packages/voice/README.md)
- **Deploy to Production**: [TWILIO_SETUP_GUIDE.md#step-8-production-deployment-optional](TWILIO_SETUP_GUIDE.md#step-8-production-deployment-optional)

## 🆘 Still Having Issues?

Run the verification script for detailed diagnostics:
```bash
python scripts/verify_twilio_setup.py
```

Check the common issues and solutions in the [Full Setup Guide](TWILIO_SETUP_GUIDE.md#troubleshooting).

---

**Need help?** See the [Complete Twilio Setup Guide](TWILIO_SETUP_GUIDE.md) for detailed instructions.
