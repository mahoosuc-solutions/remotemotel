#!/bin/bash
# Quick ingestion of essential documents for Codespaces

set -e

export DATABASE_URL="postgresql://stayhive:stayhive@localhost:5433/stayhive"
export PYTHONPATH=$(pwd)

if [ -z "$OPENAI_API_KEY" ]; then
  echo "❌ OPENAI_API_KEY not set"
  exit 1
fi

echo "🔄 Quick knowledge ingestion (4 essential documents)..."

# Core documentation only
python3 scripts/ingest_knowledge.py VOICE_MODULE_DESIGN.md \
  --hotel remotemotel \
  --title "Voice Module Design" \
  --tags "voice,design,architecture"

python3 scripts/ingest_knowledge.py INTEGRATION_PLAN.md \
  --hotel remotemotel \
  --title "Platform Integration Plan" \
  --tags "integration,plan"

python3 scripts/ingest_knowledge.py PLATFORM_100_COMPLETE.md \
  --hotel remotemotel \
  --title "Platform 100% Complete Status" \
  --tags "status,platform"

python3 scripts/ingest_knowledge.py COMPLETE_IMPLEMENTATION_ROADMAP.md \
  --hotel remotemotel \
  --title "Complete Implementation Roadmap" \
  --tags "roadmap,implementation"

echo "✅ Essential knowledge base ready!"
