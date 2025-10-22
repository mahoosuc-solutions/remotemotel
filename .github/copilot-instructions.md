# Copilot Instructions for Front Desk Hotel Operator Agent

## Project Architecture

This is a FastAPI-based hotel automation service with a modular tools architecture:

- **Entry Point**: `apps/operator-runtime/main.py` - FastAPI app with health, WebSocket, and REST endpoints
- **Tools Module**: `packages/tools/` - Standalone business logic functions (availability, leads, payments, KB search)
- **Import Pattern**: Tools are directly imported in main.py (not through `__init__.py`)

## Key Development Patterns

### Adding New Tools
1. Create new `.py` file in `packages/tools/` with a simple function
2. Import directly in `main.py`: `from packages.tools import new_tool`
3. Add FastAPI route if exposing as HTTP endpoint

Example tool structure:
```python
def tool_name(param1: str, param2: int = 1):
    return {"result": "data", "status": "success"}
```

### API Endpoints
- All tools return JSON responses with consistent structure
- Current endpoints: `/health`, `/ws` (WebSocket), `/availability`
- Mock data pattern: Tools return hardcoded responses for development

### Docker Workflow
Primary development command: `./deploy-cloud-run.sh` (builds and runs locally)
- Alternative: `./run_local.sh` (calls deploy-cloud-run.sh)
- Container exposes port 8000, mounts no volumes
- Environment variables: `ENV=local`, `PROJECT_ID=local-test-project`

## Technology Specifics

### Dependencies
Core stack in `requirements.txt`: FastAPI, Uvicorn, OpenAI, ChromaDB
- FastAPI for REST/WebSocket APIs
- Uvicorn ASGI server for async handling
- ChromaDB for knowledge base (currently mock implementation)

### File Structure Convention
```
apps/operator-runtime/    # Application runtime code
packages/tools/           # Business logic modules
```

### Testing Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Availability with query params
curl "http://localhost:8000/availability?check_in=2025-10-20&check_out=2025-10-22&adults=2&pets=true"
```

## Current Implementation Notes

- All tools return mock/hardcoded data for development
- WebSocket endpoint accepts any message and echoes back with agent prefix
- Knowledge base search (`search_kb`) uses hardcoded policies array
- No authentication or rate limiting implemented
- Direct function calls, no async/await in tools layer