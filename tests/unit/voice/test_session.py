"""
Unit tests for voice session management
"""

import pytest
from datetime import datetime
from packages.voice.session import (
    SessionManager,
    VoiceSession,
    SessionStatus,
    Message,
    MessageRole
)


@pytest.mark.asyncio
async def test_create_session():
    """Test creating a new voice session"""
    manager = SessionManager()

    session = await manager.create_session(
        channel="phone",
        caller_id="+15551234567",
        language="en-US"
    )

    assert session is not None
    assert session.session_id is not None
    assert session.channel == "phone"
    assert session.caller_id == "+15551234567"
    assert session.language == "en-US"
    assert session.status == SessionStatus.ACTIVE
    assert len(session.conversation_history) == 0


@pytest.mark.asyncio
async def test_get_session():
    """Test retrieving a session"""
    manager = SessionManager()

    # Create session
    session = await manager.create_session(
        channel="webrtc",
        caller_id="user123"
    )

    # Retrieve session
    retrieved = await manager.get_session(session.session_id)

    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    assert retrieved.channel == "webrtc"


@pytest.mark.asyncio
async def test_add_message():
    """Test adding messages to conversation history"""
    manager = SessionManager()
    session = await manager.create_session(
        channel="phone",
        caller_id="+15551234567"
    )

    # Add user message
    session.add_message(
        role=MessageRole.USER.value,
        content="I'd like to book a room"
    )

    assert len(session.conversation_history) == 1
    assert session.conversation_history[0].role == MessageRole.USER.value
    assert session.conversation_history[0].content == "I'd like to book a room"

    # Add assistant message
    session.add_message(
        role=MessageRole.ASSISTANT.value,
        content="I'd be happy to help you book a room",
        latency_ms=250
    )

    assert len(session.conversation_history) == 2
    assert session.conversation_history[1].latency_ms == 250


@pytest.mark.asyncio
async def test_add_tool_usage():
    """Test recording tool usage"""
    manager = SessionManager()
    session = await manager.create_session(
        channel="phone",
        caller_id="+15551234567"
    )

    session.add_tool_usage("check_availability")
    session.add_tool_usage("create_lead")

    assert len(session.tools_used) == 2
    assert "check_availability" in session.tools_used
    assert "create_lead" in session.tools_used

    # Adding same tool again should not duplicate
    session.add_tool_usage("check_availability")
    assert len(session.tools_used) == 2


@pytest.mark.asyncio
async def test_end_session():
    """Test ending a session"""
    manager = SessionManager()
    session = await manager.create_session(
        channel="phone",
        caller_id="+15551234567"
    )

    # End session
    success = await manager.end_session(session.session_id)

    assert success is True

    # Verify session was removed from active sessions
    active = await manager.get_active_sessions()
    assert len(active) == 0


@pytest.mark.asyncio
async def test_get_active_sessions():
    """Test getting all active sessions"""
    manager = SessionManager()

    # Create multiple sessions
    session1 = await manager.create_session(channel="phone", caller_id="+1111")
    session2 = await manager.create_session(channel="webrtc", caller_id="user1")
    session3 = await manager.create_session(channel="phone", caller_id="+2222")

    # Get active sessions
    active = await manager.get_active_sessions()

    assert len(active) == 3

    # End one session
    await manager.end_session(session2.session_id)

    # Should now have 2 active
    active = await manager.get_active_sessions()
    assert len(active) == 2


def test_session_duration():
    """Test calculating session duration"""
    session = VoiceSession(
        session_id="test-123",
        channel="phone",
        caller_id="+15551234567"
    )

    duration = session.get_duration_seconds()
    assert duration >= 0
    assert duration < 1  # Should be very short since just created


def test_session_to_dict():
    """Test converting session to dictionary"""
    session = VoiceSession(
        session_id="test-123",
        channel="phone",
        caller_id="+15551234567",
        language="en-US"
    )

    session.add_message(
        role=MessageRole.USER.value,
        content="Hello"
    )

    data = session.to_dict()

    assert data["session_id"] == "test-123"
    assert data["channel"] == "phone"
    assert data["caller_id"] == "+15551234567"
    assert data["language"] == "en-US"
    assert data["status"] == SessionStatus.ACTIVE.value
    assert data["turn_count"] == 1
    assert len(data["conversation_history"]) == 1


def test_message_creation():
    """Test creating a message"""
    msg = Message(
        role=MessageRole.USER.value,
        content="Test message",
        latency_ms=100
    )

    assert msg.role == MessageRole.USER.value
    assert msg.content == "Test message"
    assert msg.latency_ms == 100
    assert msg.timestamp is not None

    # Test to_dict
    data = msg.to_dict()
    assert data["role"] == MessageRole.USER.value
    assert data["content"] == "Test message"
