#!/bin/bash
# Smart test runner for Codespaces

set -e

echo "=================================="
echo "Codespaces Test Suite"
echo "=================================="

# Activate environment
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

# Load environment variables
if [ -f ".env.local" ]; then
  export $(grep -v '^#' .env.local | xargs -0)
fi

# Check which services are available
HAS_OPENAI=false
HAS_TWILIO=false

if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "MOCK" ] && [ "$OPENAI_API_KEY" != "\${OPENAI_API_KEY}" ]; then
  HAS_OPENAI=true
fi

if [ -n "$TWILIO_ACCOUNT_SID" ] && [ "$TWILIO_ACCOUNT_SID" != "MOCK" ] && [ "$TWILIO_ACCOUNT_SID" != "\${TWILIO_ACCOUNT_SID}" ]; then
  HAS_TWILIO=true
fi

echo ""
echo "Test Configuration:"
echo "  Database: ✓ (local PostgreSQL)"
echo "  OpenAI: $([ "$HAS_OPENAI" = true ] && echo "✓" || echo "⚠️  MOCK")"
echo "  Twilio: $([ "$HAS_TWILIO" = true ] && echo "✓" || echo "⚠️  MOCK")"
echo ""

# Build test command
TEST_MARKERS=""

if [ "$HAS_OPENAI" = false ]; then
  TEST_MARKERS="not knowledge"
fi

if [ "$HAS_TWILIO" = false ]; then
  if [ -n "$TEST_MARKERS" ]; then
    TEST_MARKERS="$TEST_MARKERS and not voice"
  else
    TEST_MARKERS="not voice"
  fi
fi

# Run tests
if [ -n "$TEST_MARKERS" ]; then
  echo "Running tests (excluding: $TEST_MARKERS)..."
  pytest tests/integration/ -v -m "$TEST_MARKERS"
else
  echo "Running all tests..."
  pytest tests/integration/ -v
fi

echo ""
echo "✓ Tests complete!"
