import os
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from .env.local
env_path = Path(__file__).parent.parent.parent / ".env.local"
load_dotenv(dotenv_path=env_path)

from packages.tools import (
    search_kb,
    check_availability,
    create_lead,
    generate_payment_link,
    computer_use,
)

# Voice module imports
try:
    from packages.voice import VoiceGateway, SessionManager
    VOICE_ENABLED = os.getenv("VOICE_ENABLED", "true").lower() == "true"
except ImportError:
    VOICE_ENABLED = False
    logging.warning("Voice module not available - install voice dependencies to enable")

app = FastAPI(
    title="Front Desk Operator Agent",
    description="AI-powered hotel concierge with voice capabilities",
    version="0.2.0"
)

# Initialize voice gateway if enabled
if VOICE_ENABLED:
    voice_gateway = VoiceGateway()
    app.include_router(voice_gateway.router, prefix="/voice", tags=["voice"])
    logging.info("Voice module enabled and routes registered")

@app.get("/health")
async def health():
    health_status = {
        "status": "ok",
        "service": "hotel-operator-agent",
        "version": "0.2.0",
        "voice_enabled": VOICE_ENABLED
    }

    if VOICE_ENABLED:
        try:
            active_sessions = await voice_gateway.session_manager.get_active_sessions()
            health_status["voice_sessions"] = len(active_sessions)
        except Exception:
            health_status["voice_sessions"] = "error"

    return health_status

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            message = await websocket.receive_text()
            response = f"🤖 Front Desk Agent received: {message}"
            await websocket.send_text(response)
        except Exception:
            break

@app.get("/availability")
async def availability(check_in: str, check_out: str, adults: int = 1, pets: bool = False):
    result = check_availability.check_availability(check_in, check_out, adults, pets)
    return {"available": True, "details": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
