#!/usr/bin/env python3
"""
Standalone Twilio voice server that proxies calls to the OpenAI Realtime API.

The implementation shares the same realtime/client/register logic used by the
voice gateway so both code paths stay in sync.
"""

from __future__ import annotations

import json
import os
import asyncio
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from dotenv import load_dotenv
from twilio.twiml.voice_response import Connect, Say, Stream, VoiceResponse

from packages.voice.hotel_config import create_hotel_realtime_client, get_hotel_config
from packages.voice.function_registry import create_hotel_function_registry
from packages.voice.relay import TwilioOpenAIRelay

# Load environment variables - try .env.local first, then system env.
if os.path.exists(".env.local"):
    load_dotenv(".env.local")
else:
    load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 8000))
ENV = os.getenv("ENV", "local")
HOTEL_NAME = os.getenv("HOTEL_NAME", "StayHive Hotels")
HOTEL_LOCATION = os.getenv("HOTEL_LOCATION", "West Bethel, ME")
HOTEL_CHECKIN_TIME = os.getenv("HOTEL_CHECKIN_TIME", "4:00 PM")
HOTEL_CHECKOUT_TIME = os.getenv("HOTEL_CHECKOUT_TIME", "10:00 AM")
HOTEL_PET_POLICY = os.getenv("HOTEL_PET_POLICY", "Pets welcome with $40 fee")
OPENAI_REALTIME_MODEL = os.getenv("OPENAI_REALTIME_MODEL", "gpt-4o-realtime-preview-2024-12-17")
VOICE = os.getenv("OPENAI_REALTIME_VOICE", "alloy")
TEMPERATURE = float(os.getenv("OPENAI_REALTIME_TEMPERATURE", 0.8))


def _resolve_system_message() -> str:
    override = os.getenv("VOICE_SYSTEM_MESSAGE")
    if override:
        return override
    try:
        return get_hotel_config().get("instructions", "")
    except Exception:  # pragma: no cover - defensive
        return (
            f"You are the AI front desk assistant for {HOTEL_NAME} in {HOTEL_LOCATION}. "
            "Welcome guests, answer questions, and assist with reservations."
        )


SYSTEM_MESSAGE = _resolve_system_message()


def create_realtime_client():
    """Create the shared realtime client and registry."""

    client = create_hotel_realtime_client(api_key=OPENAI_API_KEY)
    registry = create_hotel_function_registry()

    for schema in registry.functions.values():
        client.register_function(
            name=schema.name,
            func=schema.function,
            description=schema.description,
            parameters=schema.parameters,
        )

    return client


def build_session_update_payload() -> dict:
    registry = create_hotel_function_registry()
    return {
        "type": "session.update",
        "session": {
            "modalities": ["text", "audio"],
            "instructions": SYSTEM_MESSAGE,
            "voice": VOICE,
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "input_audio_transcription": {"model": "whisper-1"},
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500,
            },
            "tools": registry.get_openai_tools(),
        },
    }


async def send_session_update(connection) -> None:
    payload = build_session_update_payload()
    await connection.send(json.dumps(payload))


app = FastAPI(title=f"{HOTEL_NAME} Voice AI Assistant")

if not OPENAI_API_KEY:
    print("⚠️  WARNING: OpenAI API key not configured. Voice AI will not work.")
else:
    print(f"✅ OpenAI API key configured (ending in …{OPENAI_API_KEY[-8:]})")


@app.get("/", response_class=JSONResponse)
async def index_page():
    return {
        "message": f"{HOTEL_NAME} Voice AI Assistant is running!",
        "status": "healthy",
        "hotel": HOTEL_NAME,
        "location": HOTEL_LOCATION,
        "openai_configured": bool(OPENAI_API_KEY),
    }


@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    response = VoiceResponse()
    response.say(
        f"Hello! Welcome to {HOTEL_NAME}. Please wait while we connect you to our A.I. assistant.",
        voice="Google.en-US-Neural2-D",
    )
    response.pause(length=1)
    response.say("You can start speaking now!", voice="Google.en-US-Neural2-D")

    host = request.url.hostname
    port = request.url.port
    if port and port not in {80, 443}:
        ws_url = f"wss://{host}:{port}/media-stream"
    else:
        ws_url = f"wss://{host}/media-stream"

    connect = Connect()
    connect.stream(url=ws_url)
    response.append(connect)

    return HTMLResponse(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    print(f"🎯 WebSocket connection attempt to {HOTEL_NAME} media stream")

    try:
        await websocket.accept()
        print(f"✅ WebSocket connection accepted for {HOTEL_NAME}")
    except Exception as exc:
        print(f"❌ Failed to accept WebSocket connection: {exc}")
        return

    if not OPENAI_API_KEY:
        await websocket.close(code=1008, reason="OpenAI API key not configured")
        print("❌ WebSocket closed: OpenAI API key not configured")
        return

    openai_client = None
    relay = None

    try:
        openai_client = create_realtime_client()
        await openai_client.connect()
        await openai_client._send_event(build_session_update_payload())  # type: ignore[attr-defined]
        print("🤖 Connected to OpenAI Realtime API via shared client")

        relay = TwilioOpenAIRelay(
            twilio_ws=websocket,
            openai_client=openai_client,
        )

        print("🔁 Starting Twilio↔OpenAI relay")
        await relay.start()
        print("✅ Relay completed")

    except WebSocketDisconnect:
        print("📞 Twilio media stream disconnected")

    except Exception as exc:  # pragma: no cover - defensive catch
        print(f"❌ Error in media stream handler: {exc}")
        try:
            await websocket.close(code=1011, reason="Voice relay error")
        except Exception:
            pass

    finally:
        if relay:
            await relay.stop()

        if openai_client and getattr(openai_client, "is_connected", False):
            await openai_client.disconnect()


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": f"{HOTEL_NAME.lower().replace(' ', '-')}-voice-ai",
        "hotel": HOTEL_NAME,
        "openai_configured": bool(OPENAI_API_KEY),
        "environment": ENV,
        "websocket_endpoint": "/media-stream",
    }


@app.get("/test-websocket")
async def test_websocket_endpoint():
    return {
        "websocket_url": "wss://voice-ai-assistant.example.com/media-stream",
        "status": "WebSocket endpoint registered",
        "note": "Use a WebSocket client to test the connection",
    }


if __name__ == "__main__":
    import uvicorn

    print(f"🏨 Starting {HOTEL_NAME} Voice AI Assistant on port {PORT}")
    print(f"📍 Location: {HOTEL_LOCATION}")
    print(f"🤖 Model: {OPENAI_REALTIME_MODEL}")
    print(f"🗣️  Voice: {VOICE}")
    print(f"🔥 Temperature: {TEMPERATURE}")
    print(f"🌍 Environment: {ENV}")

    if ENV == "production":
        try:
            from hypercorn.asyncio import serve
            from hypercorn.config import Config

            config = Config()
            config.bind = [f"0.0.0.0:{PORT}"]
            config.alpn_protocols = ["http/1.1"]
            config.accesslog = "-"

            asyncio.run(serve(app, config))
        except ImportError:
            print("⚠️  Hypercorn not available; falling back to Uvicorn")
            uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info", access_log=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="debug", reload=False)
