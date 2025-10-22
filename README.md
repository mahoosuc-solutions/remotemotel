# BizHive Agent Platform

**Local-first AI operator platform using Model Context Protocol (MCP)**

BizHive Agent provides intelligent AI assistance for different types of businesses through modular MCP servers. Each business module (Hospitality, Tech Support, etc.) runs as an independent MCP server that can operate entirely locally with optional cloud synchronization to BizHive.cloud.

## 🎯 Overview

- **Local-First**: Runs entirely on-premise, no cloud required
- **MCP Standard**: Compatible with Claude Desktop, Cursor, and any MCP client
- **Modular**: Each business type is a separate MCP server
- **Cloud Optional**: Sync to BizHive.cloud for analytics when desired
- **Privacy-Focused**: Your data stays local unless you enable cloud sync

## 🏢 Business Modules

### StayHive - Hospitality Module
AI front desk agent for hotels, motels, and B&Bs

**Features:**
- 📞 **Voice Calls** - Natural phone conversations with AI (OpenAI Realtime API)
- 🏨 Check room availability
- 📋 Create reservations
- 💼 Capture guest leads
- 💳 Generate payment links
- 📖 Answer policy questions
- 🗺️ Provide local recommendations
- 🔄 Transfer to human staff
- 📱 Send SMS confirmations

**✅ Voice Module: Production Ready**
- Complete phone integration via Twilio
- OpenAI Realtime API for natural conversations
- Function calling for 6 hotel tools
- Bidirectional audio streaming
- Context injection with hotel information
- See [VOICE_MODULE_SUMMARY_FINAL.md](VOICE_MODULE_SUMMARY_FINAL.md) for details

**🎙️ Quick Twilio Setup:**
1. Get credentials from [twilio.com](https://twilio.com/try-twilio)
2. Add to [.env.local](.env.local): Account SID, Auth Token, Phone Number
3. Run: `./start_voice_server.sh`
4. Setup ngrok: `./scripts/setup_ngrok.sh && ngrok http 8000`
5. Configure webhooks at [Twilio Console](https://console.twilio.com)
6. **Call your number and test!**

📚 Guides: [Quick Start](docs/TWILIO_QUICK_START.md) | [Full Setup](docs/TWILIO_SETUP_GUIDE.md) | [Verify](scripts/verify_twilio_setup.py)

### TechHive - Tech Support Module *(Coming Soon)*
AI helpdesk agent for IT support

**Features:**
- Create support tickets
- Search knowledge base
- Check ticket status
- Escalate issues
- Provide troubleshooting guidance

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip or uv package manager

### Installation

```bash
# Clone repository
cd bizhive-agent

# Install dependencies
pip install -r requirements.txt

# Or using uv
uv pip install -r requirements.txt
```

### Running StayHive MCP Server

```bash
# Run locally (standalone)
python -m mcp_servers.stayhive.server

# Run with cloud sync (optional)
export BIZHIVE_CLOUD_ENABLED=true
export BIZHIVE_CLOUD_API_KEY=your_api_key
python -m mcp_servers.stayhive.server
```

### Using with Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "stayhive": {
      "command": "python",
      "args": ["-m", "mcp_servers.stayhive.server"],
      "cwd": "/path/to/bizhive-agent"
    },
    "stripe": {
      "url": "https://mcp.stripe.com"
    }
  }
}
```

**Note**: Adding Stripe's official MCP server enables secure payment processing. See [Stripe Integration Guide](docs/STRIPE_INTEGRATION.md) for details.

## 📁 Project Structure

```
bizhive-agent/
├── mcp_servers/
│   ├── stayhive/              # Hospitality MCP server
│   │   ├── server.py          # MCP server implementation
│   │   ├── tools.py           # MCP tools (check_availability, etc.)
│   │   ├── resources.py       # MCP resources (policies, room info)
│   │   ├── prompts.py         # MCP prompts (templates)
│   │   └── config.yaml        # Business configuration
│   ├── techhive/              # Tech support MCP server (coming soon)
│   └── shared/                # Shared utilities
│       ├── database.py        # Local database management
│       └── cloud_sync.py      # BizHive.cloud sync
├── packages/
│   ├── core/                  # Core framework (coming soon)
│   ├── models/                # Pydantic models
│   └── integrations/          # Third-party integrations
├── tests/                     # Comprehensive test suite
└── docs/                      # Documentation
```

## 🔧 Configuration

### StayHive Configuration

Edit `mcp_servers/stayhive/config.yaml` to customize your property:

```yaml
business:
  name: "Your Hotel Name"
  type: "hospitality"
  location: "Your Location"

property:
  check_in_time: "16:00"
  check_out_time: "10:00"
  room_types:
    - name: "Standard Queen"
      capacity: 2
      base_price: 120
```

### Cloud Sync Configuration (Optional)

Enable cloud synchronization with BizHive.cloud:

```bash
export BIZHIVE_CLOUD_ENABLED=true
export BIZHIVE_CLOUD_API_KEY=your_api_key
export BIZHIVE_CLOUD_URL=https://api.bizhive.cloud  # Optional, defaults to production
```

**What Gets Synced:**
- New leads and guest inquiries
- Reservation confirmations
- Conversation analytics
- Performance metrics

**What Stays Local:**
- All guest data (unless explicitly synced)
- Knowledge base content
- Conversation history
- Room inventory

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=mcp_servers --cov=packages
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy mcp_servers/ packages/
```

## 📊 MCP Capabilities

### Tools (Executable Functions)
- `check_availability` - Check room availability for dates
- `create_reservation` - Create a new reservation
- `create_lead` - Capture guest lead for follow-up
- `generate_payment_link` - Generate payment link

### Resources (Data Sources)
- `hotel_policies` - Complete policy information
- `room_information` - Room types and features
- `amenities` - Property amenities
- `local_area_guide` - Local attractions and services
- `seasonal_information` - Season-specific recommendations

### Prompts (Interaction Templates)
- `guest_greeting` - Welcome messages
- `availability_inquiry` - Availability checking flow
- `booking_confirmation` - Reservation process
- `pet_policy` - Pet-related questions
- `local_recommendations` - Area suggestions
- `problem_resolution` - Issue handling

## 🔐 Security & Privacy

- **Local-First**: All data stored locally in SQLite by default
- **Optional Cloud**: Cloud sync is opt-in, disabled by default
- **Data Control**: You control what data is synced to cloud
- **No Vendor Lock-in**: Works standalone without BizHive.cloud

## 🌐 BizHive Ecosystem

Part of the BizHive network:
- **StayHive.ai** - Hospitality AI platform
- **TechHive** - Technical support platform (SilverSurfer.ai)
- **BizHive.cloud** - Central management and analytics (optional)

## 📖 Documentation

### General
- [Claude Code Guide](CLAUDE.md) - Complete project overview and guide
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Development roadmap
- [Stripe Integration](docs/STRIPE_INTEGRATION.md) - Payment processing setup

### Voice Module (NEW - Production Ready)
- **[Project Complete Summary](PROJECT_COMPLETE.md)** - Complete implementation overview ⭐⭐⭐
- **[Cloud Deployment Guide](CLOUD_DEPLOYMENT_GUIDE.md)** - Deploy to Google Cloud Run ⭐⭐
- **[Activation Checklist](ACTIVATION_CHECKLIST.md)** - Quick start checklist ⭐
- **[Realtime Activation Guide](REALTIME_ACTIVATION_GUIDE.md)** - Complete setup instructions
- [Deployment Complete](DEPLOYMENT_COMPLETE.md) - Local deployment summary
- [Voice Module Summary](VOICE_MODULE_SUMMARY_FINAL.md) - Complete implementation details
- [Voice Phase 3 Complete](VOICE_PHASE3_COMPLETE.md) - Realtime API documentation
- [Voice Module Design](VOICE_MODULE_DESIGN.md) - Architecture (1000+ lines)
- [Voice Implementation Plan](VOICE_IMPLEMENTATION_PLAN.md) - 14-day roadmap
- [Voice Test Report](VOICE_TEST_REPORT.md) - Test results (74/74 passing)
- [Voice Quick Start](VOICE_QUICK_START.md) - 5-minute setup

### Other
- [StayHive Quickstart](docs/STAYHIVE_QUICKSTART.md) - Getting started guide
- [Test Results](docs/TEST_RESULTS_SUMMARY.md) - Test coverage and results
- [Progress Summary](docs/PROGRESS_SUMMARY.md) - Implementation status

## 🤝 Contributing

This is a private BizHive project. For questions or support, contact the development team.

## 📝 License

Proprietary - BizHive Network

## 🆘 Support

- **Documentation**: See `/docs` folder
- **Issues**: Contact BizHive development team
- **Cloud Support**: support@bizhive.cloud (for cloud-connected instances)

---

**Built with:** Model Context Protocol (MCP) | Python 3.11 | FastAPI | SQLAlchemy | OpenAI

**Part of:** BizHive Network - Empowering independent businesses with AI
