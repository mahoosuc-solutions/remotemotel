#!/bin/bash
# Ingest all key documentation files into knowledge base

set -e

export DATABASE_URL="postgresql://stayhive:stayhive@localhost:5433/stayhive"
export OPENAI_API_KEY="${OPENAI_API_KEY:-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}"
export PYTHONPATH=/home/webemo-aaron/projects/front-desk

echo "🔄 Starting knowledge base ingestion..."

# Core voice module documentation
echo "📝 Ingesting Voice Module Design..."
python3 scripts/ingest_knowledge.py VOICE_MODULE_DESIGN.md \
  --hotel remotemotel \
  --title "Voice Module Design" \
  --tags "voice,design,architecture"

echo "📝 Ingesting Voice Implementation Plan..."
python3 scripts/ingest_knowledge.py VOICE_IMPLEMENTATION_PLAN.md \
  --hotel remotemotel \
  --title "Voice Implementation Plan" \
  --tags "voice,implementation,plan"

echo "📝 Ingesting Voice Phase 3 Complete..."
python3 scripts/ingest_knowledge.py VOICE_PHASE3_COMPLETE.md \
  --hotel remotemotel \
  --title "Voice Phase 3 - OpenAI Realtime API" \
  --tags "voice,realtime,openai"

echo "📝 Ingesting Realtime Activation Guide..."
python3 scripts/ingest_knowledge.py REALTIME_ACTIVATION_GUIDE.md \
  --hotel remotemotel \
  --title "Realtime API Activation Guide" \
  --tags "voice,realtime,setup"

# Integration and implementation documentation
echo "📝 Ingesting Integration Plan..."
python3 scripts/ingest_knowledge.py INTEGRATION_PLAN.md \
  --hotel remotemotel \
  --title "Platform Integration Plan" \
  --tags "integration,plan,implementation"

echo "📝 Ingesting Complete Implementation Roadmap..."
python3 scripts/ingest_knowledge.py COMPLETE_IMPLEMENTATION_ROADMAP.md \
  --hotel remotemotel \
  --title "Complete Implementation Roadmap" \
  --tags "roadmap,implementation,gaps"

echo "📝 Ingesting Guest and Staff Features Roadmap..."
python3 scripts/ingest_knowledge.py GUEST_AND_STAFF_FEATURES_ROADMAP.md \
  --hotel remotemotel \
  --title "Guest and Staff Features Roadmap" \
  --tags "features,roadmap,guest,staff"

# Setup guides
echo "📝 Ingesting Twilio Setup Guide..."
python3 scripts/ingest_knowledge.py docs/TWILIO_SETUP_GUIDE.md \
  --hotel remotemotel \
  --title "Twilio Setup Guide" \
  --tags "twilio,setup,voice"

echo "📝 Ingesting Stripe Integration..."
python3 scripts/ingest_knowledge.py docs/STRIPE_INTEGRATION.md \
  --hotel remotemotel \
  --title "Stripe Payment Integration" \
  --tags "stripe,payments,setup"

echo "📝 Ingesting StayHive Quickstart..."
python3 scripts/ingest_knowledge.py docs/STAYHIVE_QUICKSTART.md \
  --hotel remotemotel \
  --title "StayHive Platform Quickstart" \
  --tags "quickstart,setup,platform"

echo "✅ Knowledge base ingestion complete!"
echo "📊 Checking ingested documents..."

python3 -c "
import asyncio
from packages.knowledge.service import KnowledgeService

async def list_docs():
    service = KnowledgeService()
    docs = await service.list_documents('remotemotel', limit=50)
    print(f'\n📚 Ingested {len(docs)} documents:')
    for doc in docs:
        print(f'  - {doc.title} (tags: {', '.join(doc.tags)})')

asyncio.run(list_docs())
"
