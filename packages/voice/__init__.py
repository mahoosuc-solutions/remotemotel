"""
Voice Module for Hotel Operator Agent

Provides voice interaction capabilities including:
- Phone calls via Twilio
- WebRTC browser-based voice chat
- OpenAI Realtime API integration
- Speech-to-text and text-to-speech
- Call recording and analytics

Usage:
    from packages.voice import VoiceGateway, SessionManager

    gateway = VoiceGateway()
    session_mgr = SessionManager()
"""

from packages.voice.dependencies import check_required_dependencies

check_required_dependencies()

# Core components (no external dependencies)
from packages.voice.session import SessionManager, VoiceSession
from packages.voice.models import VoiceCall, ConversationTurn, VoiceAnalytics

# Optional components (require Twilio)
try:
    from packages.voice.gateway import VoiceGateway
    _GATEWAY_AVAILABLE = True
except ImportError:
    VoiceGateway = None
    _GATEWAY_AVAILABLE = False

# Optional components (require OpenAI Realtime API)
try:
    from packages.voice.realtime import RealtimeAPIClient
    _REALTIME_AVAILABLE = True
except ImportError:
    RealtimeAPIClient = None
    _REALTIME_AVAILABLE = False

# Optional components (require audio processing)
try:
    from packages.voice.relay import TwilioOpenAIRelay
    _RELAY_AVAILABLE = True
except ImportError:
    TwilioOpenAIRelay = None
    _RELAY_AVAILABLE = False

__all__ = [
    "SessionManager",
    "VoiceSession",
    "VoiceCall",
    "ConversationTurn",
    "VoiceAnalytics",
]

if _GATEWAY_AVAILABLE:
    __all__.append("VoiceGateway")

if _REALTIME_AVAILABLE:
    __all__.append("RealtimeAPIClient")

if _RELAY_AVAILABLE:
    __all__.append("TwilioOpenAIRelay")

__version__ = "0.1.0"
