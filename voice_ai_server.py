#!/usr/bin/env python3
"""
Twilio Voice AI Assistant using OpenAI Realtime API
Based on official Twilio documentation and best practices
Uses existing project configuration from .env.local
"""
import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv

# Load environment variables - try .env.local first, then system env
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
else:
    load_dotenv()

# Configuration from existing project settings
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 8000))
ENV = os.getenv('ENV', 'local')
HOTEL_NAME = os.getenv('HOTEL_NAME', 'StayHive Hotels')
HOTEL_LOCATION = os.getenv('HOTEL_LOCATION', 'West Bethel, ME')
HOTEL_AMENITIES = os.getenv('HOTEL_AMENITIES', 'Free Wi-Fi, Complimentary Breakfast, Swimming Pool, Fitness Center')
HOTEL_CHECKIN_TIME = os.getenv('HOTEL_CHECKIN_TIME', '4:00 PM')
HOTEL_CHECKOUT_TIME = os.getenv('HOTEL_CHECKOUT_TIME', '10:00 AM')
HOTEL_PET_POLICY = os.getenv('HOTEL_PET_POLICY', 'Pets welcome with $40 fee')

# OpenAI Realtime Configuration
OPENAI_REALTIME_MODEL = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview-2024-12-17')
VOICE = os.getenv('OPENAI_REALTIME_VOICE', 'alloy')
TEMPERATURE = float(os.getenv('OPENAI_REALTIME_TEMPERATURE', 0.8))

# AI System Message with hotel context
SYSTEM_MESSAGE = f"""You are a professional hotel front desk assistant for {HOTEL_NAME} in {HOTEL_LOCATION}.

Hotel Information:
- Check-in time: {HOTEL_CHECKIN_TIME}
- Check-out time: {HOTEL_CHECKOUT_TIME}  
- Amenities: {HOTEL_AMENITIES}
- Pet policy: {HOTEL_PET_POLICY}

You can help guests with:
- Room reservations and availability
- Hotel amenities and services information
- Check-in/check-out procedures
- Local recommendations and directions
- Billing inquiries
- General hotel policies

Always be professional, friendly, and helpful. If you need to transfer a call or don't have specific information, 
offer to connect them with the appropriate department or a human staff member.

Keep responses concise but informative, as this is a phone conversation."""

# Event types to log for debugging
LOG_EVENT_TYPES = [
    'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created', 'session.updated',
    'conversation.item.created'
]

app = FastAPI(title=f"{HOTEL_NAME} Voice AI Assistant")

# Check OpenAI API key
if not OPENAI_API_KEY:
    print("⚠️  WARNING: OpenAI API key not configured. Voice AI will not work.")
    print("   Please check OPENAI_API_KEY in .env.local file.")
else:
    print(f"✅ OpenAI API key configured (ending in: ...{OPENAI_API_KEY[-8:]})")

@app.get("/", response_class=JSONResponse)
async def index_page():
    """Health check endpoint"""
    return {
        "message": f"{HOTEL_NAME} Voice AI Assistant is running!",
        "status": "healthy",
        "hotel": HOTEL_NAME,
        "location": HOTEL_LOCATION,
        "openai_configured": bool(OPENAI_API_KEY)
    }

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    print(f"📞 Incoming call to {HOTEL_NAME}")
    
    response = VoiceResponse()
    
    # Personalized greeting message
    response.say(
        f"Hello! Welcome to {HOTEL_NAME}. Please wait while we connect you to our A.I. assistant.",
        voice="Google.en-US-Neural2-D"
    )
    response.pause(length=1)
    response.say(
        "You can start speaking now!",
        voice="Google.en-US-Neural2-D"
    )
    
    # Get the host from request and set up WebSocket connection
    host = request.url.hostname
    port = request.url.port
    
    # Build WebSocket URL - handle different environments
    if port and port not in [80, 443]:
        ws_url = f'wss://{host}:{port}/media-stream'
    else:
        ws_url = f'wss://{host}/media-stream'
    
    print(f"🔗 Connecting to WebSocket: {ws_url}")
    
    # Connect to media stream
    connect = Connect()
    connect.stream(url=ws_url)
    response.append(connect)
    
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print(f"🎯 WebSocket connection attempt to {HOTEL_NAME} media stream")
    print(f"🔍 WebSocket headers: {websocket.headers}")
    
    try:
        await websocket.accept()
        print(f"✅ WebSocket connection accepted for {HOTEL_NAME}")
    except Exception as e:
        print(f"❌ Failed to accept WebSocket connection: {e}")
        return
    
    # Check if API key is configured
    if not OPENAI_API_KEY:
        await websocket.close(code=1008, reason="OpenAI API key not configured")
        print("❌ WebSocket closed: OpenAI API key not configured")
        return
    
    # Connect to OpenAI Realtime API
    openai_url = f"wss://api.openai.com/v1/realtime?model={OPENAI_REALTIME_MODEL}&temperature={TEMPERATURE}"
    
    try:
        async with websockets.connect(
            openai_url,
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
        ) as openai_ws:
            print("🤖 Connected to OpenAI Realtime API")
            
            # Send session configuration to OpenAI
            await send_session_update(openai_ws)
            
            stream_sid = None
            
            async def receive_from_twilio():
                """Receive audio data from Twilio and send it to OpenAI Realtime API."""
                nonlocal stream_sid
                try:
                    async for message in websocket.iter_text():
                        data = json.loads(message)
                        
                        if data['event'] == 'media' and openai_ws.state.name == 'OPEN':
                            # Forward audio from Twilio to OpenAI
                            audio_append = {
                                "type": "input_audio_buffer.append",
                                "audio": data['media']['payload']
                            }
                            await openai_ws.send(json.dumps(audio_append))
                            
                        elif data['event'] == 'start':
                            stream_sid = data['start']['streamSid']
                            print(f"📡 Media stream started: {stream_sid}")
                            
                        elif data['event'] == 'stop':
                            print("🛑 Media stream stopped")
                            break
                            
                except WebSocketDisconnect:
                    print("📞 Client disconnected")
                    if openai_ws.state.name == 'OPEN':
                        await openai_ws.close()
                except Exception as e:
                    print(f"❌ Error in receive_from_twilio: {e}")
            
            async def send_to_twilio():
                """Receive events from OpenAI Realtime API, send audio back to Twilio."""
                nonlocal stream_sid
                try:
                    async for openai_message in openai_ws:
                        response = json.loads(openai_message)
                        response_type = response.get('type')
                        
                        # Log important events
                        if response_type in LOG_EVENT_TYPES:
                            print(f"🤖 OpenAI Event: {response_type}")
                        
                        # Handle session update confirmation
                        if response_type == 'session.updated':
                            print("✅ OpenAI session updated successfully")
                        
                        # Forward audio from OpenAI to Twilio
                        if response_type in ('response.audio.delta', 'response.output_audio.delta') and response.get('delta'):
                            if stream_sid:
                                try:
                                    audio_delta = build_twilio_audio_event(stream_sid, response['delta'])
                                    if audio_delta:
                                        await websocket.send_json(audio_delta)
                                        await send_mark(websocket, stream_sid)
                                except Exception as e:
                                    print(f"❌ Error processing audio data: {e}")
                        
                        # Handle function calls (for hotel services)
                        elif response_type == 'response.function_call_arguments.done':
                            print(f"🔧 Function call: {response.get('name', 'unknown')}")
                            
                        # Handle conversation events for debugging
                        elif response_type == 'conversation.item.created':
                            item = response.get('item', {})
                            if item.get('type') == 'message':
                                role = item.get('role', 'unknown')
                                print(f"💬 Conversation: {role} message created")
                                
                except Exception as e:
                    print(f"❌ Error in send_to_twilio: {e}")

            async def send_mark(connection, stream_sid_value):
                """Inform Twilio that a new chunk of audio has been sent."""
                if stream_sid_value:
                    mark_event = {
                        "event": "mark",
                        "streamSid": stream_sid_value,
                        "mark": {"name": "responsePart"}
                    }
                    await connection.send_json(mark_event)
            
            # Run both coroutines concurrently
            await asyncio.gather(receive_from_twilio(), send_to_twilio())
            
    except Exception as e:
        print(f"❌ Failed to connect to OpenAI: {e}")
        await websocket.close(code=1011, reason="Failed to connect to OpenAI")

def build_twilio_audio_event(stream_sid: str | None, delta_payload: str):
    """Prepare media payload for Twilio websocket stream."""
    if not stream_sid or not delta_payload:
        return None

    try:
        # OpenAI sends base64 PCM - re-encode to guarantee padding for Twilio
        audio_payload = base64.b64encode(base64.b64decode(delta_payload)).decode("utf-8")
    except Exception as exc:  # pragma: no cover - defensive catch
        raise ValueError("Invalid audio payload") from exc

    return {
        "event": "media",
        "streamSid": stream_sid,
        "media": {
            "payload": audio_payload
        }
    }


async def send_session_update(openai_ws):
    """Send session update to OpenAI WebSocket with hotel-specific configuration."""
    session_update = {
        "type": "session.update",
        "session": {
            "modalities": ["text", "audio"],
            "instructions": SYSTEM_MESSAGE,
            "voice": VOICE,
            "input_audio_format": "g711_ulaw",  # Twilio uses μ-law (pcmu)
            "output_audio_format": "g711_ulaw",
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500
            },
            "tools": [
                {
                    "type": "function",
                    "name": "check_room_availability",
                    "description": f"Check room availability at {HOTEL_NAME} for given dates",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                            "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                            "guests": {"type": "integer", "description": "Number of guests"}
                        },
                        "required": ["check_in", "check_out", "guests"]
                    }
                },
                {
                    "type": "function", 
                    "name": "get_hotel_info",
                    "description": f"Get information about {HOTEL_NAME} amenities and services",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "info_type": {"type": "string", "description": "Type of information requested (amenities, hours, location, policies, etc.)"}
                        },
                        "required": ["info_type"]
                    }
                },
                {
                    "type": "function",
                    "name": "transfer_to_department",
                    "description": "Transfer call to specific hotel department",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "department": {"type": "string", "description": "Department to transfer to (front_desk, housekeeping, management, maintenance)"},
                            "reason": {"type": "string", "description": "Reason for transfer"}
                        },
                        "required": ["department", "reason"]
                    }
                }
            ]
        }
    }
    
    print(f"🚀 Sending session update to OpenAI for {HOTEL_NAME}")
    await openai_ws.send(json.dumps(session_update))

# Health check for load balancers
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": f"{HOTEL_NAME.lower().replace(' ', '-')}-voice-ai",
        "hotel": HOTEL_NAME,
        "openai_configured": bool(OPENAI_API_KEY),
        "environment": ENV,
        "websocket_endpoint": "/media-stream"
    }

@app.get("/test-websocket")
async def test_websocket_endpoint():
    """Test endpoint to verify WebSocket route is registered"""
    return {
        "websocket_url": "wss://voice-ai-assistant-jvm6akkheq-uc.a.run.app/media-stream",
        "status": "WebSocket endpoint registered",
        "note": "Use a WebSocket client to test the connection"
    }

if __name__ == "__main__":
    import uvicorn
    print(f"🏨 Starting {HOTEL_NAME} Voice AI Assistant on port {PORT}")
    print(f"📍 Location: {HOTEL_LOCATION}")
    print(f"🤖 Model: {OPENAI_REALTIME_MODEL}")
    print(f"🗣️  Voice: {VOICE}")
    print(f"🌍 Environment: {ENV}")
    
    # Configure server based on environment
    if ENV == 'production':
        try:
            from hypercorn.asyncio import serve
            from hypercorn.config import Config

            config = Config()
            config.bind = [f"0.0.0.0:{PORT}"]
            config.alpn_protocols = ["http/1.1"]
            config.accesslog = '-'  # Surface access logs in Cloud Run

            asyncio.run(serve(app, config))
        except ImportError:
            print("⚠️  Hypercorn not available; falling back to Uvicorn")
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=PORT,
                log_level="info",
                access_log=True
            )
    else:
        # Development settings
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=PORT,
            log_level="debug",
            reload=False
        )
