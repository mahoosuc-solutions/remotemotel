#!/bin/bash
# setup_ngrok.sh - Install and configure ngrok for Twilio webhook testing

set -e

echo "========================================"
echo "🔧 ngrok Setup for Twilio Webhooks"
echo "========================================"

# Check if ngrok is already installed
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok is already installed"
    ngrok version
else
    echo "📦 Installing ngrok..."

    # Install ngrok for Debian/Ubuntu (WSL)
    if [[ -f /etc/debian_version ]]; then
        curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
            sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null

        echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
            sudo tee /etc/apt/sources.list.d/ngrok.list

        sudo apt update
        sudo apt install -y ngrok

        echo "✅ ngrok installed successfully"
    else
        echo "❌ Auto-install only supported on Debian/Ubuntu"
        echo "Please install ngrok manually from: https://ngrok.com/download"
        exit 1
    fi
fi

# Check if auth token is configured
echo ""
echo "🔑 Checking ngrok authentication..."

if ngrok config check &> /dev/null; then
    echo "✅ ngrok is configured with an auth token"
else
    echo "⚠️  ngrok auth token not configured"
    echo ""
    echo "To get your auth token:"
    echo "1. Sign up at https://ngrok.com"
    echo "2. Get your auth token from https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "3. Run: ngrok config add-authtoken YOUR_AUTH_TOKEN"
    echo ""
    read -p "Do you want to add your auth token now? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your ngrok auth token: " auth_token
        ngrok config add-authtoken "$auth_token"
        echo "✅ Auth token configured"
    fi
fi

echo ""
echo "========================================"
echo "📋 Usage Instructions"
echo "========================================"
echo ""
echo "1️⃣  Start your FastAPI server (in another terminal):"
echo "   cd /home/webemo-aaron/projects/front-desk"
echo "   . venv/bin/activate"
echo "   export PYTHONPATH=/home/webemo-aaron/projects/front-desk:\$PYTHONPATH"
echo "   python apps/operator-runtime/main.py"
echo ""
echo "2️⃣  Start ngrok to expose your server:"
echo "   ngrok http 8000"
echo ""
echo "3️⃣  Copy the 'Forwarding' HTTPS URL (e.g., https://abc123.ngrok.io)"
echo ""
echo "4️⃣  Configure Twilio webhooks at:"
echo "   https://console.twilio.com/us1/develop/phone-numbers/manage/incoming"
echo ""
echo "   Voice URL: https://YOUR-NGROK-URL/voice/twilio/inbound"
echo "   Status URL: https://YOUR-NGROK-URL/voice/twilio/status"
echo ""
echo "5️⃣  Test by calling your Twilio number!"
echo ""
echo "========================================"
echo "🚀 Ready to start ngrok? Run: ngrok http 8000"
echo "========================================"
