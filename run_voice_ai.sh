#!/bin/bash
# Run Voice AI Server with ngrok tunnel
# This script starts the voice AI server and exposes it via ngrok

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏨 Starting West Bethel Motel Voice AI Assistant${NC}"

# Check if .env.local file exists
if [ ! -f .env.local ]; then
    echo -e "${RED}❌ .env.local file not found${NC}"
    echo "Please ensure .env.local exists with OPENAI_API_KEY configured"
    exit 1
fi

# Load the configuration (using export to handle spaces properly)
set -a  # automatically export all variables
source .env.local
set +a  # stop automatically exporting

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ]; then
    echo -e "${RED}❌ OpenAI API key not configured in .env.local${NC}"
    echo "Please update OPENAI_API_KEY in .env.local file"
    exit 1
fi

# Check if virtual environment exists and activate it
if [ -d ".venv" ]; then
    echo -e "${YELLOW}📦 Using existing virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r voice_requirements.txt"
    exit 1
fi

# Check if required packages are installed in venv
python -c "import fastapi, websockets, twilio" 2>/dev/null || {
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    pip install -r voice_requirements.txt
}

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ ngrok is not installed${NC}"
    echo "Please install ngrok:"
    echo "1. Visit https://ngrok.com/download"
    echo "2. Download and install ngrok"
    echo "3. Run: ngrok config add-authtoken YOUR_TOKEN"
    exit 1
fi

# Configuration is already in .env.local
echo -e "${GREEN}✅ Configuration loaded from .env.local${NC}"
echo -e "   Hotel: ${HOTEL_NAME:-West Bethel Motel}"
echo -e "   Location: ${HOTEL_LOCATION:-West Bethel, ME}"

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    if [ ! -z "$NGROK_PID" ]; then
        kill $NGROK_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}🚀 Starting Voice AI Server on port 8000...${NC}"
python voice_ai_server.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Check if server started successfully
if ! ps -p $SERVER_PID > /dev/null; then
    echo -e "${RED}❌ Failed to start server${NC}"
    exit 1
fi

echo -e "${GREEN}🌐 Starting ngrok tunnel...${NC}"
ngrok http 8000 > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    if tunnels:
        print(tunnels[0]['public_url'])
    else:
        print('')
except:
    print('')
")

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}❌ Failed to get ngrok URL${NC}"
    cleanup
    exit 1
fi

echo -e "${GREEN}✅ ${HOTEL_NAME} Voice AI Assistant is ready!${NC}"
echo ""
echo -e "${BLUE}📋 Setup Instructions:${NC}"
echo "1. Go to Twilio Console: https://console.twilio.com/"
echo "2. Find your Twilio phone number: ${TWILIO_PHONE_NUMBER:-[Check .env.local]}"
echo "3. Under 'Voice & Fax' configuration:"
echo "   - Set 'A CALL COMES IN' to:"
echo -e "   ${YELLOW}${NGROK_URL}/incoming-call${NC}"
echo ""
echo -e "${GREEN}📞 Test by calling your Twilio number: ${TWILIO_PHONE_NUMBER:-[Check .env.local]}${NC}"
echo ""
echo -e "${BLUE}🔗 URLs:${NC}"
echo "  Server Health: ${NGROK_URL}/health"
echo "  Twilio Webhook: ${NGROK_URL}/incoming-call"
echo "  Local Server: http://localhost:8000"
echo ""
echo -e "${YELLOW}💡 Tip: Leave this terminal open while testing${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Wait for user to stop
wait $SERVER_PID