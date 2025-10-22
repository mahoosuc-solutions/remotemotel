# StayHive MCP Server - Quick Start Guide

This guide will help you get the StayHive hospitality MCP server running locally in minutes.

## Prerequisites

- Python 3.11 or higher
- pip or uv package manager
- (Optional) Claude Desktop or other MCP client

## Installation

### 1. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using uv (recommended for faster installation)
uv pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Check Python version
python --version  # Should be 3.11+

# Check MCP SDK installed
python -c "import mcp; print('MCP SDK installed successfully')"
```

## Running the Server

### Local Standalone Mode (No Cloud)

```bash
# Run from project root
python -m mcp_servers.stayhive.server
```

You should see:
```
INFO - Starting StayHive MCP Server...
INFO - Local-first operation with optional BizHive.cloud sync
INFO - Database initialized
```

### With Cloud Sync (Optional)

```bash
# Set environment variables
export BIZHIVE_CLOUD_ENABLED=true
export BIZHIVE_CLOUD_API_KEY=your_api_key_here

# Run server
python -m mcp_servers.stayhive.server
```

## Testing the Server

### Option 1: Using Claude Desktop

1. Open Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add StayHive server:
```json
{
  "mcpServers": {
    "stayhive": {
      "command": "python",
      "args": ["-m", "mcp_servers.stayhive.server"],
      "cwd": "/full/path/to/bizhive-agent"
    }
  }
}
```

3. Restart Claude Desktop

4. Test by asking Claude:
   - "Check if there are rooms available June 1-3"
   - "What's the pet policy?"
   - "Tell me about local attractions"

### Option 2: Using MCP Inspector (Development)

```bash
# Install MCP Inspector (if not already installed)
npm install -g @modelcontextprotocol/inspector

# Run inspector
mcp-inspector python -m mcp_servers.stayhive.server
```

This opens a web interface where you can:
- List available tools, resources, and prompts
- Test tool execution
- View resource data
- Test prompt templates

### Option 3: Using Cursor IDE

1. Open Cursor settings
2. Navigate to MCP servers
3. Add StayHive with the same configuration as Claude Desktop
4. Use @ to access MCP tools in Cursor

## Example Interactions

### Check Availability

**User**: "Do you have rooms available for June 1-3, 2025?"

**StayHive** (via Claude):
- Calls `check_availability` tool
- Returns available room types with pricing
- Suggests next steps (booking, questions)

### Create a Reservation

**User**: "I'd like to book a Standard Queen room for those dates. I'm John Doe, john@example.com, 555-1234"

**StayHive** (via Claude):
- Calls `create_reservation` tool
- Creates reservation in local database
- Returns confirmation number (e.g., RSV-20251017-A1B2C3)
- Optionally syncs to BizHive.cloud if enabled

### Get Hotel Information

**User**: "What amenities do you have?"

**StayHive** (via Claude):
- Reads `amenities` resource
- Provides comprehensive amenity list
- Includes breakfast hours, WiFi details, parking

### Local Recommendations

**User**: "What are the best hiking trails nearby?"

**StayHive** (via Claude):
- Reads `local_area_guide` resource
- Provides seasonal recommendations
- Suggests Grafton Notch State Park and other nearby trails

## Configuration

### Customize Your Property

Edit `mcp_servers/stayhive/config.yaml`:

```yaml
business:
  name: "West Bethel Motel"  # Change to your property name
  type: "hospitality"
  location: "Bethel, Maine"  # Change to your location

property:
  check_in_time: "16:00"     # Customize check-in time
  check_out_time: "10:00"    # Customize check-out time
  room_types:
    - name: "Standard Queen"
      capacity: 2
      pets_allowed: false
      base_price: 120         # Set your pricing
```

### Data Storage

All data is stored locally in:
```
data/stayhive/local.db
```

This SQLite database contains:
- Room inventory
- Reservations
- Guest leads
- Conversation history (if enabled)

## Troubleshooting

### Server Won't Start

**Error**: `ModuleNotFoundError: No module named 'mcp'`
**Solution**: Install dependencies: `pip install -r requirements.txt`

**Error**: `ImportError: cannot import name 'Server' from 'mcp.server'`
**Solution**: Update MCP SDK: `pip install --upgrade mcp`

### Database Issues

**Error**: `OperationalError: unable to open database file`
**Solution**: Ensure `data/stayhive/` directory exists: `mkdir -p data/stayhive`

### Claude Desktop Not Showing Tools

**Solution**:
1. Verify configuration path is correct in `claude_desktop_config.json`
2. Use absolute paths, not relative paths
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors

## Next Steps

1. **Customize Configuration**: Edit `config.yaml` for your property
2. **Add More Rooms**: Modify room types and pricing
3. **Test All Features**: Try creating reservations, checking availability
4. **Add Knowledge Base**: Extend resources with local information
5. **Enable Cloud Sync** (Optional): Connect to BizHive.cloud for analytics

## Available MCP Capabilities

### Tools (Functions)
- `check_availability` - Check room availability
- `create_reservation` - Create reservations
- `create_lead` - Capture guest leads
- `generate_payment_link` - Generate payment URLs

### Resources (Data)
- `hotel_policies` - Check-in/out, pets, cancellation
- `room_information` - Room types and features
- `amenities` - Breakfast, WiFi, parking, etc.
- `local_area_guide` - Nearby attractions and restaurants
- `seasonal_information` - Season-specific recommendations

### Prompts (Templates)
- `guest_greeting` - Welcome messages
- `availability_inquiry` - Availability flow
- `booking_confirmation` - Reservation process
- `pet_policy` - Pet-related questions
- `local_recommendations` - Area suggestions
- `problem_resolution` - Issue handling

## Support

- **Documentation**: See `/docs` folder
- **Issues**: Check GitHub issues or contact development team
- **Configuration Help**: Review `IMPLEMENTATION_PLAN.md`

---

**You're ready to go!** The StayHive MCP server is now running and ready to assist with hotel operations through any MCP-compatible AI client.
