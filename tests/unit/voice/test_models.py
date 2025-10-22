"""
Unit tests for voice database models
"""

import pytest
from datetime import datetime
from packages.voice.models import (
    VoiceCall,
    ConversationTurn,
    VoiceAnalytics,
    VoiceMetrics
)


def test_voice_call_creation():
    """Test creating a VoiceCall instance"""
    call = VoiceCall(
        session_id="test-session-123",
        channel="phone",
        caller_id="+15551234567",
        direction="inbound",
        start_time=datetime.utcnow(),
        status="active",
        language="en-US"
    )

    assert call.session_id == "test-session-123"
    assert call.channel == "phone"
    assert call.caller_id == "+15551234567"
    assert call.direction == "inbound"
    assert call.status == "active"
    assert call.language == "en-US"
    # duration_seconds defaults to None until set
    assert call.duration_seconds is None or call.duration_seconds == 0


def test_voice_call_to_dict():
    """Test VoiceCall serialization"""
    call = VoiceCall(
        session_id="test-123",
        channel="webrtc",
        caller_id="user_456",
        direction="outbound",
        start_time=datetime.utcnow(),
        status="completed",
        duration_seconds=120,
        sentiment_score=0.85
    )

    data = call.to_dict()

    assert data["session_id"] == "test-123"
    assert data["channel"] == "webrtc"
    assert data["caller_id"] == "user_456"
    assert data["direction"] == "outbound"
    assert data["status"] == "completed"
    assert data["duration_seconds"] == 120
    assert data["sentiment_score"] == 0.85
    assert "start_time" in data


def test_voice_call_with_tools():
    """Test VoiceCall with tools executed"""
    call = VoiceCall(
        session_id="test-789",
        channel="phone",
        caller_id="+15559876543",
        direction="inbound",
        tools_executed=["check_availability", "create_lead", "send_sms_confirmation"]
    )

    assert len(call.tools_executed) == 3
    assert "check_availability" in call.tools_executed
    assert "create_lead" in call.tools_executed


def test_voice_call_with_metadata():
    """Test VoiceCall with custom metadata"""
    metadata = {
        "call_source": "website",
        "referrer": "google_ads",
        "campaign": "summer_2025"
    }

    call = VoiceCall(
        session_id="test-meta",
        channel="webrtc",
        caller_id="user_web",
        direction="inbound",
        call_metadata=metadata
    )

    assert call.call_metadata == metadata
    assert call.call_metadata["call_source"] == "website"
    assert call.call_metadata["campaign"] == "summer_2025"


def test_conversation_turn_creation():
    """Test creating a ConversationTurn"""
    turn = ConversationTurn(
        call_id=1,
        turn_number=1,
        role="user",
        content="I'd like to book a room",
        timestamp=datetime.utcnow(),
        latency_ms=250
    )

    assert turn.call_id == 1
    assert turn.turn_number == 1
    assert turn.role == "user"
    assert turn.content == "I'd like to book a room"
    assert turn.latency_ms == 250


def test_conversation_turn_to_dict():
    """Test ConversationTurn serialization"""
    turn = ConversationTurn(
        call_id=2,
        turn_number=3,
        role="assistant",
        content="Let me check availability for you",
        timestamp=datetime.utcnow(),
        latency_ms=180,
        audio_url="https://example.com/audio/turn3.mp3"
    )

    data = turn.to_dict()

    assert data["call_id"] == 2
    assert data["turn_number"] == 3
    assert data["role"] == "assistant"
    assert data["content"] == "Let me check availability for you"
    assert data["latency_ms"] == 180
    assert data["audio_url"] == "https://example.com/audio/turn3.mp3"


def test_conversation_turn_with_metadata():
    """Test ConversationTurn with metadata"""
    turn_meta = {
        "confidence": 0.95,
        "language": "en",
        "speaker_id": "guest_123"
    }

    turn = ConversationTurn(
        call_id=3,
        turn_number=5,
        role="user",
        content="What time is checkout?",
        turn_metadata=turn_meta
    )

    assert turn.turn_metadata == turn_meta
    assert turn.turn_metadata["confidence"] == 0.95


def test_voice_analytics_creation():
    """Test creating VoiceAnalytics"""
    analytics = VoiceAnalytics(
        call_id=1,
        metric_name=VoiceMetrics.RESPONSE_LATENCY,
        metric_value=250.5,
        timestamp=datetime.utcnow()
    )

    assert analytics.call_id == 1
    assert analytics.metric_name == VoiceMetrics.RESPONSE_LATENCY
    assert analytics.metric_value == 250.5


def test_voice_analytics_to_dict():
    """Test VoiceAnalytics serialization"""
    analytics = VoiceAnalytics(
        call_id=2,
        metric_name=VoiceMetrics.SENTIMENT_SCORE,
        metric_value=0.85,
        timestamp=datetime.utcnow(),
        analytics_metadata={"source": "openai"}
    )

    data = analytics.to_dict()

    assert data["call_id"] == 2
    assert data["metric_name"] == VoiceMetrics.SENTIMENT_SCORE
    assert data["metric_value"] == 0.85
    assert "timestamp" in data
    assert data["analytics_metadata"]["source"] == "openai"


def test_voice_metrics_constants():
    """Test VoiceMetrics constants are defined"""
    assert VoiceMetrics.CALL_DURATION == "call_duration_seconds"
    assert VoiceMetrics.RESPONSE_LATENCY == "response_latency_ms"
    assert VoiceMetrics.STT_LATENCY == "stt_latency_ms"
    assert VoiceMetrics.TTS_LATENCY == "tts_latency_ms"
    assert VoiceMetrics.SENTIMENT_SCORE == "sentiment_score"
    assert VoiceMetrics.CALL_SUCCESS == "call_success_rate"


def test_voice_call_repr():
    """Test VoiceCall string representation"""
    call = VoiceCall(
        session_id="test-repr",
        channel="phone",
        caller_id="+15551234567",
        direction="inbound",
        status="active"
    )

    repr_str = repr(call)
    assert "test-repr" in repr_str
    assert "+15551234567" in repr_str
    assert "active" in repr_str


def test_conversation_turn_repr():
    """Test ConversationTurn string representation"""
    turn = ConversationTurn(
        call_id=1,
        turn_number=2,
        role="user",
        content="Hello, I need help"
    )

    repr_str = repr(turn)
    assert "turn=2" in repr_str
    assert "user" in repr_str
    assert "Hello" in repr_str


def test_voice_analytics_repr():
    """Test VoiceAnalytics string representation"""
    analytics = VoiceAnalytics(
        call_id=1,
        metric_name="test_metric",
        metric_value=123.45
    )

    repr_str = repr(analytics)
    assert "test_metric" in repr_str
    assert "123.45" in repr_str


def test_voice_call_complete_lifecycle():
    """Test a complete call lifecycle with all fields"""
    start = datetime.utcnow()

    # Create call
    call = VoiceCall(
        session_id="lifecycle-test",
        channel="phone",
        caller_id="+15551234567",
        direction="inbound",
        start_time=start,
        status="active",
        language="en-US",
        call_metadata={"source": "direct_dial"}
    )

    # Simulate call progression
    call.tools_executed = ["check_availability", "create_lead"]
    call.lead_id = 123
    call.sentiment_score = 0.9

    # End call
    end = datetime.utcnow()
    call.end_time = end
    call.status = "completed"
    call.duration_seconds = 180
    call.recording_url = "https://s3.example.com/recordings/lifecycle-test.wav"
    call.transcription = "Full conversation transcription..."

    # Validate
    assert call.session_id == "lifecycle-test"
    assert call.status == "completed"
    assert call.duration_seconds == 180
    assert len(call.tools_executed) == 2
    assert call.lead_id == 123
    assert call.sentiment_score == 0.9
    assert call.recording_url is not None
    assert call.transcription is not None

    # Serialize
    data = call.to_dict()
    assert data["status"] == "completed"
    assert data["duration_seconds"] == 180
    assert len(data["tools_executed"]) == 2
