"""
Voice Gateway - Main entry point for voice interactions

Handles:
- Incoming/outgoing phone calls via Twilio
- WebRTC browser connections
- OpenAI Realtime API connections
- Audio stream routing
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from twilio.request_validator import RequestValidator

from packages.voice.session import SessionManager, SessionStatus

logger = logging.getLogger(__name__)


class VoiceGateway:
    """
    Main gateway for all voice interactions

    Provides endpoints for:
    - Twilio webhook handling
    - WebRTC connections
    - OpenAI Realtime API integration
    """

    def __init__(self, session_manager: Optional[SessionManager] = None):
        """
        Initialize voice gateway

        Args:
            session_manager: SessionManager instance (creates new if None)
        """
        self.session_manager = session_manager or SessionManager()
        self.router = APIRouter()
        self.twilio_validator = None

        # Load Twilio credentials
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

        if self.twilio_auth_token:
            self.twilio_validator = RequestValidator(self.twilio_auth_token)

        # Setup routes
        self._setup_routes()

        logger.info("VoiceGateway initialized")

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.router.post("/twilio/inbound")
        async def handle_twilio_inbound(request: Request):
            """Handle incoming Twilio calls"""
            return await self.handle_twilio_call(request)

        @self.router.post("/twilio/status")
        async def handle_twilio_status(request: Request):
            """Handle Twilio status callbacks"""
            return await self.handle_call_status(request)

        @self.router.websocket("/twilio/stream")
        async def handle_twilio_stream(websocket: WebSocket):
            """Handle Twilio media streams via WebSocket"""
            return await self.handle_media_stream(websocket)

        @self.router.get("/sessions")
        async def list_sessions():
            """List active sessions"""
            sessions = await self.session_manager.get_active_sessions()
            return {"sessions": [s.to_dict() for s in sessions]}

        @self.router.get("/sessions/{session_id}")
        async def get_session(session_id: str):
            """Get session details"""
            session = await self.session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session.to_dict()

        @self.router.post("/sessions/{session_id}/end")
        async def end_session(session_id: str):
            """End a session"""
            success = await self.session_manager.end_session(session_id)
            if not success:
                raise HTTPException(status_code=404, detail="Session not found")
            return {"status": "ended", "session_id": session_id}

        @self.router.get("/health")
        async def voice_health():
            """Voice service health check"""
            return {
                "status": "healthy",
                "service": "voice_gateway",
                "twilio_configured": bool(self.twilio_account_sid),
                "active_sessions": len(await self.session_manager.get_active_sessions())
            }

    async def handle_twilio_call(self, request: Request) -> Response:
        """
        Handle incoming Twilio call

        Creates a new session and returns TwiML to connect the call
        to a WebSocket stream for real-time audio processing.

        Args:
            request: FastAPI request object

        Returns:
            TwiML response
        """
        try:
            # Get call parameters
            form_data = await request.form()
            call_sid = form_data.get("CallSid")
            from_number = form_data.get("From")
            to_number = form_data.get("To")

            logger.info(f"Incoming call from {from_number} to {to_number} (SID: {call_sid})")

            # Verify Twilio signature if validator is configured
            if self.twilio_validator and not await self._verify_twilio_request(request):
                logger.warning(f"Invalid Twilio signature for call {call_sid}")
                raise HTTPException(status_code=403, detail="Invalid signature")

            # Create session
            session = await self.session_manager.create_session(
                channel="phone",
                caller_id=from_number,
                metadata={
                    "call_sid": call_sid,
                    "to_number": to_number,
                    "twilio_call": True,
                }
            )

            # Create TwiML response
            response = VoiceResponse()

            # Greeting
            response.say(
                "Thank you for calling. Please wait while we connect you to our AI concierge.",
                voice="Polly.Joanna"
            )

            # Connect to WebSocket stream for real-time audio
            connect = Connect()
            stream = Stream(url=self._get_stream_url(session.session_id))
            connect.append(stream)
            response.append(connect)

            logger.info(f"Created session {session.session_id} for call {call_sid}")

            return Response(content=str(response), media_type="application/xml")

        except Exception as e:
            logger.error(f"Error handling Twilio call: {e}", exc_info=True)

            # Return error TwiML
            response = VoiceResponse()
            response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
            response.hangup()

            return Response(content=str(response), media_type="application/xml")

    async def handle_call_status(self, request: Request) -> Dict[str, str]:
        """
        Handle Twilio call status callbacks

        Args:
            request: FastAPI request object

        Returns:
            Status acknowledgment
        """
        try:
            form_data = await request.form()
            call_sid = form_data.get("CallSid")
            call_status = form_data.get("CallStatus")

            logger.info(f"Call status update: {call_sid} -> {call_status}")

            # Find session by call_sid
            sessions = await self.session_manager.get_active_sessions()
            session = next(
                (s for s in sessions if s.metadata.get("call_sid") == call_sid),
                None
            )

            if session:
                # Update session status based on call status
                if call_status in ["completed", "busy", "no-answer"]:
                    status_map = {
                        "completed": SessionStatus.COMPLETED,
                        "busy": SessionStatus.FAILED,
                        "no-answer": SessionStatus.ABANDONED,
                    }
                    await self.session_manager.end_session(
                        session.session_id,
                        status_map.get(call_status, SessionStatus.COMPLETED)
                    )
                    logger.info(f"Session {session.session_id} ended with status {call_status}")

            return {"status": "received"}

        except Exception as e:
            logger.error(f"Error handling call status: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def handle_media_stream(self, websocket: WebSocket):
        """
        Handle Twilio media stream WebSocket with OpenAI Realtime API relay

        This is the core voice conversation handler. It:
        1. Accepts Twilio Media Stream WebSocket
        2. Creates OpenAI Realtime API client with hotel configuration
        3. Spawns bidirectional audio relay
        4. Manages session lifecycle

        Args:
            websocket: Twilio Media Stream WebSocket connection
        """
        await websocket.accept()
        session = None
        openai_client = None
        relay = None

        try:
            logger.info("Media stream WebSocket connected - waiting for stream start")

            # Import relay components
            from packages.voice.relay import TwilioOpenAIRelay
            from packages.voice.hotel_config import create_hotel_realtime_client

            # Wait for stream start event to get call_sid
            start_message = await websocket.receive_json()

            if start_message.get("event") != "start":
                logger.warning(f"Expected 'start' event, got '{start_message.get('event')}'")
                # Handle connected event if it comes first
                if start_message.get("event") == "connected":
                    start_message = await websocket.receive_json()

            start_data = start_message.get("start", {})
            call_sid = start_data.get("callSid", "unknown")
            stream_sid = start_message.get("streamSid", "unknown")

            logger.info(f"Stream started for call {call_sid} (stream: {stream_sid})")

            # Find or create session for tracking
            sessions = await self.session_manager.get_active_sessions()
            session = next(
                (s for s in sessions if s.metadata.get("call_sid") == call_sid),
                None
            )

            if not session:
                logger.info(f"Creating new session for call {call_sid}")
                session = await self.session_manager.create_session(
                    channel="phone",
                    caller_id="unknown",  # Will be updated from Twilio data
                    metadata={
                        "call_sid": call_sid,
                        "stream_sid": stream_sid,
                        "twilio_call": True
                    }
                )

            # Create and connect OpenAI Realtime API client with hotel configuration
            logger.info(f"Creating OpenAI Realtime client for call {call_sid}")
            openai_client = create_hotel_realtime_client()
            await openai_client.connect()

            logger.info(f"OpenAI Realtime API connected for call {call_sid}")

            # Create and start bidirectional audio relay
            logger.info(f"Starting audio relay for call {call_sid}")
            relay = TwilioOpenAIRelay(
                twilio_ws=websocket,
                openai_client=openai_client,
                call_sid=call_sid,
                stream_sid=stream_sid
            )

            # Start relay (blocks until call ends)
            await relay.start()

            logger.info(f"Relay completed for call {call_sid}")

        except WebSocketDisconnect:
            logger.info(f"Media stream WebSocket disconnected")

        except Exception as e:
            logger.error(f"Error in media stream handler: {e}", exc_info=True)
            if session:
                await self.session_manager.end_session(
                    session.session_id,
                    status=SessionStatus.FAILED
                )

        finally:
            # Cleanup
            if relay:
                logger.info(f"Stopping relay for call {session.metadata.get('call_sid') if session else 'unknown'}")
                await relay.stop()

            if openai_client:
                logger.info(f"Disconnecting OpenAI client")
                await openai_client.disconnect()

            if session:
                logger.info(f"Ending session {session.session_id}")
                await self.session_manager.end_session(
                    session.session_id,
                    status=SessionStatus.COMPLETED
                )

    async def handle_webrtc_connection(self, websocket: WebSocket):
        """
        Handle WebRTC audio connection from browser

        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        session = None

        try:
            # Create session for WebRTC call
            session = await self.session_manager.create_session(
                channel="webrtc",
                caller_id="web_user",  # TODO: Get from authentication
            )

            logger.info(f"WebRTC connection established: {session.session_id}")

            # Send session info to client
            await websocket.send_json({
                "event": "session_created",
                "session_id": session.session_id
            })

            while True:
                # Receive message from client
                message = await websocket.receive()

                if message.get("type") == "websocket.receive":
                    if "text" in message:
                        # Handle text message
                        data = message["text"]
                        logger.debug(f"WebRTC text message: {data}")

                        # Echo for now
                        await websocket.send_text(f"Received: {data}")

                    elif "bytes" in message:
                        # Handle audio data
                        audio_data = message["bytes"]
                        logger.debug(f"WebRTC audio data ({len(audio_data)} bytes)")

                        # TODO: Process audio with STT/Realtime API

        except WebSocketDisconnect:
            logger.info(f"WebRTC disconnected: {session.session_id if session else 'unknown'}")
            if session:
                await self.session_manager.end_session(session.session_id)

        except Exception as e:
            logger.error(f"Error in WebRTC connection: {e}", exc_info=True)
            if session:
                await self.session_manager.end_session(
                    session.session_id,
                    status=SessionStatus.FAILED
                )

    async def _verify_twilio_request(self, request: Request) -> bool:
        """
        Verify Twilio request signature

        Args:
            request: FastAPI request object

        Returns:
            bool: True if signature is valid
        """
        if not self.twilio_validator:
            logger.warning("Twilio validator not configured, skipping signature verification")
            return True

        try:
            # Get signature from header
            signature = request.headers.get("X-Twilio-Signature", "")

            # Get request URL and reconstruct with correct scheme for Cloud Run
            # Cloud Run terminates SSL and forwards HTTP internally, but Twilio
            # signs the request with the external HTTPS URL. We need to check
            # X-Forwarded-Proto header to reconstruct the correct URL.
            url = str(request.url)

            # Check if request came through a proxy (Cloud Run, load balancer, etc.)
            forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
            if forwarded_proto and forwarded_proto.lower() == "https":
                # Replace http:// with https:// if the original request was HTTPS
                if url.startswith("http://"):
                    url = "https://" + url[7:]
                    logger.debug(f"Reconstructed URL with HTTPS scheme: {url}")

            # Get form parameters
            form_data = await request.form()
            params = dict(form_data)

            # Validate signature
            is_valid = self.twilio_validator.validate(url, params, signature)

            if not is_valid:
                logger.warning(f"Invalid Twilio signature for URL: {url}")

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying Twilio signature: {e}", exc_info=True)
            return False

    def _get_stream_url(self, session_id: str) -> str:
        """
        Get WebSocket stream URL for a session

        Args:
            session_id: Session identifier

        Returns:
            WebSocket URL
        """
        # Get base URL from environment or construct from service URL
        base_url = os.getenv("VOICE_WEBSOCKET_URL")

        if not base_url:
            # Try to construct from project/region for Cloud Run
            project_id = os.getenv("PROJECT_ID", "localhost")
            region = os.getenv("REGION", "us-central1")

            if project_id == "localhost":
                base_url = "wss://localhost:8000"
            else:
                # Cloud Run URL pattern
                # Note: This should match your actual Cloud Run URL
                service_url = os.getenv("SERVICE_URL")
                if service_url:
                    # Convert https:// to wss://
                    base_url = service_url.replace("https://", "wss://").replace("http://", "ws://")
                else:
                    # Fallback - this may need adjustment based on actual Cloud Run URL
                    base_url = "wss://westbethel-operator-1048462921095.us-central1.run.app"

        return f"{base_url}/voice/twilio/stream?session={session_id}"

    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: Optional[str] = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call

        Args:
            to_number: Phone number to call
            from_number: Caller ID (uses default if None)
            message: Message to speak

        Returns:
            Call information
        """
        try:
            from twilio.rest import Client

            client = Client(self.twilio_account_sid, self.twilio_auth_token)

            from_number = from_number or self.twilio_phone_number
            if not from_number:
                raise ValueError("No from_number provided and TWILIO_PHONE_NUMBER not configured")

            # Create TwiML for outbound call
            twiml = VoiceResponse()
            if message:
                twiml.say(message, voice="Polly.Joanna")
            else:
                twiml.say("Hello, this is a call from the hotel AI assistant.", voice="Polly.Joanna")

            # Make call
            call = client.calls.create(
                to=to_number,
                from_=from_number,
                twiml=str(twiml),
                status_callback=self._get_status_callback_url()
            )

            # Create session
            session = await self.session_manager.create_session(
                channel="phone",
                caller_id=to_number,
                metadata={
                    "call_sid": call.sid,
                    "direction": "outbound",
                    "twilio_call": True,
                }
            )

            logger.info(f"Initiated outbound call to {to_number} (SID: {call.sid})")

            return {
                "call_sid": call.sid,
                "session_id": session.session_id,
                "to": to_number,
                "from": from_number,
                "status": call.status,
            }

        except Exception as e:
            logger.error(f"Error initiating outbound call: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

    def _get_status_callback_url(self) -> str:
        """Get status callback URL for Twilio"""
        base_url = os.getenv("TWILIO_WEBHOOK_URL", "http://localhost:8000")
        return f"{base_url}/voice/twilio/status"
