#!/bin/bash
# start_voice_server.sh - Start the Front Desk Voice Server

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "🎙️  Starting Front Desk Voice Server"
echo "========================================"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python -c "import twilio" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Load environment variables
if [ -f ".env.local" ]; then
    echo "🔑 Loading environment variables from .env.local..."
    while IFS= read -r line || [ -n "$line" ]; do
        # Strip comments (# ...) and whitespace
        line="${line%%\#*}"
        line="$(printf '%s' "${line}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        [ -z "$line" ] && continue

        if [[ "$line" == *=* ]]; then
            key="${line%%=*}"
            value="${line#*=}"
            key="$(printf '%s' "${key}" | tr -d '[:space:]')"

            # Remove surrounding quotes if present
            if [[ "$value" == \"*\" && "$value" == *\" ]]; then
                value="${value:1:-1}"
            elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
                value="${value:1:-1}"
            fi

            export "$key"="$value"
        fi
    done < .env.local
else
    echo -e "${YELLOW}⚠️  .env.local not found - using defaults${NC}"
fi

# Set Python path
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Run verification (optional)
echo ""
read -p "Run Twilio setup verification? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python scripts/verify_twilio_setup.py
    echo ""
    read -p "Continue to start server? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Start the server
echo ""
echo "========================================"
echo -e "${GREEN}🚀 Starting server on http://0.0.0.0:8000${NC}"
echo "========================================"
echo ""
echo "Available endpoints:"
echo "  Health:       http://localhost:8000/health"
echo "  Voice Health: http://localhost:8000/voice/health"
echo "  Sessions:     http://localhost:8000/voice/sessions"
echo "  Twilio Hook:  http://localhost:8000/voice/twilio/inbound"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start FastAPI with uvicorn
python apps/operator-runtime/main.py
