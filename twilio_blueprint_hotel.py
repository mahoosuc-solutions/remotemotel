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

# Load environment variables from .env.local (our existing config)
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
else:
    load_dotenv()

# Configuration - Using our existing hotel settings
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 8000))
TEMPERATURE = float(os.getenv('OPENAI_REALTIME_TEMPERATURE', 0.8))
HOTEL_NAME = os.getenv('HOTEL_NAME', 'West Bethel Motel')
HOTEL_LOCATION = os.getenv('HOTEL_LOCATION', 'West Bethel, ME')

# Hotel-specific system message
SYSTEM_MESSAGE = f"""You are a professional AI assistant for {HOTEL_NAME}, located in {HOTEL_LOCATION}. 

Your role is to help guests with:
- Room availability and booking assistance
- Hotel amenities and services information  
- Check-in/check-out procedures
- Local recommendations
- Billing inquiries
- General hotel policies

Hotel Details:
- Check-in: {os.getenv('HOTEL_CHECKIN_TIME', '4:00 PM')}
- Check-out: {os.getenv('HOTEL_CHECKOUT_TIME', '10:00 AM')}
- Amenities: {os.getenv('HOTEL_AMENITIES', 'Free Wi-Fi, Breakfast, Pool, Fitness Center')}
- Pet Policy: {os.getenv('HOTEL_PET_POLICY', 'Pets welcome with fee')}

When guests ask about availability:
- For "tonight" or "today": Use check_room_availability with check_in as "tonight"
- For "this weekend": Use check_room_availability with check_in as "this weekend"  
- For "next Friday" or similar: Use check_room_availability with check_in as "next friday"
- Always ask for number of guests if not specified

Always be professional, friendly, and helpful. Keep responses concise for phone conversations. When checking availability, use the exact natural language terms the guest uses."""

VOICE = os.getenv('OPENAI_REALTIME_VOICE', 'alloy')
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created', 'session.updated'
]
SHOW_TIMING_MATH = False

app = FastAPI(title=f"{HOTEL_NAME} Voice AI Assistant")

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set OPENAI_API_KEY in .env.local file.')

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {
        "message": f"{HOTEL_NAME} Voice AI Assistant is running!",
        "hotel": HOTEL_NAME,
        "location": HOTEL_LOCATION,
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": f"{HOTEL_NAME.lower().replace(' ', '-')}-voice-ai",
        "hotel": HOTEL_NAME,
        "openai_configured": bool(OPENAI_API_KEY)
    }

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    print(f"📞 Incoming call to {HOTEL_NAME}")
    
    response = VoiceResponse()
    # Personalized greeting for the hotel
    response.say(
        f"Hello! Welcome to {HOTEL_NAME}. Please wait while we connect you to our A.I. assistant.",
        voice="Google.en-US-Neural2-D"
    )
    response.pause(length=1)
    response.say(   
        "You can start talking now!",
        voice="Google.en-US-Neural2-D"
    )
    
    # Get host and build WebSocket URL
    host = request.url.hostname
    port = request.url.port
    
    # Handle different URL formats
    if port and port not in [80, 443]:
        ws_url = f'wss://{host}:{port}/media-stream'
    else:
        ws_url = f'wss://{host}/media-stream'
    
    connect = Connect()
    connect.stream(url=ws_url)
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print(f"🎯 Client connected to {HOTEL_NAME} media stream")
    await websocket.accept()

    async with websockets.connect(
        f"wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01&temperature={TEMPERATURE}",
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
    ) as openai_ws:
        print("🤖 Connected to OpenAI Realtime API")
        await initialize_session(openai_ws)

        # Connection specific state
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None
        
        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.state.name == 'OPEN':
                        latest_media_timestamp = int(data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"📡 Media stream started: {stream_sid}")
                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
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
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"🤖 OpenAI Event: {response['type']}")
                    
                    if response['type'] == 'session.updated':
                        print("✅ OpenAI session updated successfully")

                    if response['type'] == 'response.created':
                        last_assistant_item = response['response']['output'][0]['id']

                    if response['type'] == 'response.audio.delta' and response.get('delta'):
                        if stream_sid:
                            try:
                                # Send audio back to Twilio
                                audio_delta = {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": response['delta']
                                    }
                                }
                                await websocket.send_json(audio_delta)
                            except Exception as e:
                                print(f"❌ Error processing audio data: {e}")

                    # Handle other events for debugging
                    if response['type'] == 'input_audio_buffer.speech_started':
                        print("🗣️  User started speaking")

                    if response['type'] == 'input_audio_buffer.speech_stopped':
                        print("🤐 User stopped speaking")

                    if response['type'] == 'response.done':
                        print("✅ Assistant response completed")

                    # Handle function calls
                    if response['type'] == 'response.function_call_delta':
                        print(f"🔧 Function call delta: {response}")
                        
                    if response['type'] == 'response.output_item.done' and response.get('item', {}).get('type') == 'function_call':
                        # Extract function call details
                        function_call = response['item']
                        function_name = function_call.get('name')
                        call_id = function_call.get('call_id')
                        
                        try:
                            arguments = json.loads(function_call.get('arguments', '{}'))
                            print(f"🔧 Function call: {function_name} with args: {arguments}")
                            
                            # Handle the function call
                            if function_name == 'check_room_availability':
                                result = await handle_check_room_availability(arguments)
                            elif function_name == 'get_hotel_info':
                                result = await handle_get_hotel_info(arguments)
                            else:
                                result = {"error": f"Unknown function: {function_name}"}
                            
                            # Send function result back to OpenAI
                            function_result = {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_id,
                                    "output": json.dumps(result)
                                }
                            }
                            await openai_ws.send(json.dumps(function_result))
                            
                            # Request response generation
                            response_create = {"type": "response.create"}
                            await openai_ws.send(json.dumps(response_create))
                            
                        except Exception as e:
                            print(f"❌ Error handling function call: {e}")
                            # Send error result
                            error_result = {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_id,
                                    "output": json.dumps({"error": str(e)})
                                }
                            }
                            await openai_ws.send(json.dumps(error_result))

            except Exception as e:
                print(f"❌ Error in send_to_twilio: {e}")

        # Run both coroutines concurrently
        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def handle_check_room_availability(arguments):
    """Handle room availability check function call."""
    from datetime import datetime, timedelta
    
    check_in = arguments.get('check_in', '')
    check_out = arguments.get('check_out', '')
    guests = arguments.get('guests', 1)
    
    print(f"🏨 Checking availability: {check_in} to {check_out} for {guests} guests")
    
    # Parse today's date for relative date handling
    today = datetime.now()
    
    # Handle natural language dates
    if check_in.lower() in ['tonight', 'today']:
        check_in_date = today
        check_out_date = today + timedelta(days=1)
    elif 'this weekend' in check_in.lower():
        # Find next Saturday
        days_ahead = 5 - today.weekday()  # Saturday = 5
        if days_ahead <= 0:
            days_ahead += 7
        check_in_date = today + timedelta(days_ahead)
        check_out_date = check_in_date + timedelta(days=2)  # Weekend = Sat-Sun
    elif 'next friday' in check_in.lower():
        # Find next Friday
        days_ahead = 4 - today.weekday()  # Friday = 4
        if days_ahead <= 0:
            days_ahead += 7
        check_in_date = today + timedelta(days_ahead)
        check_out_date = check_in_date + timedelta(days=1)
    else:
        # Try to parse exact dates
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
        except:
            check_in_date = today
            check_out_date = today + timedelta(days=1)
    
    # Format dates for response
    formatted_check_in = check_in_date.strftime('%B %d, %Y')
    formatted_check_out = check_out_date.strftime('%B %d, %Y')
    
    # Mock availability data for West Bethel Motel
    available_rooms = [
        {
            "room_type": "Standard Queen Room",
            "rate": 89,
            "available": True,
            "features": ["Queen bed", "Free WiFi", "Mountain views", "Private bathroom"]
        },
        {
            "room_type": "King Suite",
            "rate": 129,
            "available": True,
            "features": ["King bed", "Kitchenette", "Separate sitting area", "Mountain views"]
        },
        {
            "room_type": "Family Room",
            "rate": 149,
            "available": guests > 2,
            "features": ["Two queen beds", "Microwave", "Mini fridge", "Sleeps up to 4"]
        }
    ]
    
    available = [room for room in available_rooms if room["available"]]
    
    return {
        "hotel": HOTEL_NAME,
        "check_in": formatted_check_in,
        "check_out": formatted_check_out,
        "guests": guests,
        "nights": (check_out_date - check_in_date).days,
        "available_rooms": available,
        "total_available": len(available),
        "message": f"We have {len(available)} room types available for your stay from {formatted_check_in} to {formatted_check_out}"
    }

async def handle_get_hotel_info(arguments):
    """Handle hotel information request."""
    info_type = arguments.get('info_type', 'general')
    
    info_responses = {
        "general": {
            "name": HOTEL_NAME,
            "location": HOTEL_LOCATION,
            "description": "A charming mountain motel offering comfortable accommodations with beautiful views of the White Mountains.",
            "amenities": ["Free WiFi", "Mountain views", "Kitchenettes available", "Pet-friendly rooms", "Free parking"],
            "contact": {
                "phone": "+1 (207) 220-3501",
                "address": "2 Mayville Rd, Bethel, ME 04217"
            }
        },
        "amenities": {
            "wifi": "Free high-speed WiFi throughout the property",
            "parking": "Free on-site parking for all guests",
            "pets": "Pet-friendly rooms available with advance notice",
            "kitchenettes": "Select rooms include kitchenettes with microwave and mini fridge",
            "views": "Many rooms offer stunning mountain views"
        },
        "location": {
            "address": "2 Mayville Rd, Bethel, ME 04217",
            "nearby": [
                "Sunday River Ski Resort - 8 miles",
                "White Mountain National Forest - 5 miles",
                "Bethel Village - 2 miles",
                "Grafton Notch State Park - 15 miles"
            ],
            "activities": ["Skiing", "Hiking", "Mountain biking", "Fall foliage viewing"]
        },
        "policies": {
            "check_in": "3:00 PM",
            "check_out": "11:00 AM",
            "cancellation": "Free cancellation up to 24 hours before arrival",
            "pets": "Pet fee of $25 per night per pet",
            "smoking": "Non-smoking property"
        }
    }
    
    return info_responses.get(info_type, info_responses["general"])

async def initialize_session(openai_ws):
    """Send session update to OpenAI WebSocket."""
    session_update = {
        "type": "session.update",
        "session": {
            "modalities": ["text", "audio"],
            "instructions": SYSTEM_MESSAGE,
            "voice": VOICE,
            "input_audio_format": "g711_ulaw",
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
                    "description": f"Check room availability at {HOTEL_NAME}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "check_in": {"type": "string", "description": "Check-in date"},
                            "check_out": {"type": "string", "description": "Check-out date"},
                            "guests": {"type": "integer", "description": "Number of guests"}
                        },
                        "required": ["check_in", "check_out", "guests"]
                    }
                },
                {
                    "type": "function",
                    "name": "get_hotel_info",
                    "description": f"Get information about {HOTEL_NAME}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "info_type": {"type": "string", "description": "Type of info requested"}
                        },
                        "required": ["info_type"]
                    }
                }
            ]
        }
    }
    
    print(f"🚀 Sending session update to OpenAI for {HOTEL_NAME}")
    await openai_ws.send(json.dumps(session_update))

if __name__ == "__main__":
    import uvicorn
    print(f"🏨 Starting {HOTEL_NAME} Voice AI Assistant on port {PORT}")
    print(f"📍 Location: {HOTEL_LOCATION}")
    print(f"🗣️  Voice: {VOICE}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)