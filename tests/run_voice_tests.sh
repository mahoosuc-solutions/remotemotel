#!/bin/bash
#
# Voice Module Test Runner
#
# Runs all voice module tests and generates coverage report
#

set -e

echo "=================================="
echo "Voice Module Test Suite"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found${NC}"
    echo "Install with: pip install pytest pytest-asyncio pytest-cov"
    exit 1
fi

# Change to project root
cd "$(dirname "$0")/.."

echo "Running voice module tests..."
echo ""

PYTEST_ARGS=(-v -W ignore::DeprecationWarning)

if pytest --help 2>/dev/null | grep -q -- "--cov="; then
    PYTEST_ARGS+=(
        --cov=packages/voice
        --cov-report=term-missing
        --cov-report=html:htmlcov/voice
    )
else
    echo -e "${YELLOW}Warning: pytest-cov plugin not available; running without coverage${NC}"
fi

pytest tests/unit/voice/ "${PYTEST_ARGS[@]}" "$@"

TEST_EXIT_CODE=$?

echo ""
echo "=================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi
echo "=================================="
echo ""

# Show coverage summary
echo "Coverage report generated at: htmlcov/voice/index.html"
echo ""

exit $TEST_EXIT_CODE
