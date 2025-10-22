"""
Unit tests for voice-specific tools
"""

import pytest
from packages.voice.tools import (
    transfer_to_human,
    play_hold_music,
    handle_ivr_menu,
    format_for_voice,
    execute_voice_tool
)


@pytest.mark.asyncio
async def test_transfer_to_human():
    """Test call transfer functionality"""
    result = await transfer_to_human(
        session_id="test-123",
        department="front_desk",
        reason="Guest needs special assistance"
    )

    assert result["success"] is True
    assert result["department"] == "front_desk"
    assert "phone_number" in result
    assert "Transferring you" in result["message"]
    assert result["twiml_action"] == "dial"


@pytest.mark.asyncio
async def test_transfer_invalid_department():
    """Test transfer to invalid department"""
    result = await transfer_to_human(
        session_id="test-123",
        department="invalid_dept"
    )

    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_play_hold_music():
    """Test hold music playback"""
    result = await play_hold_music(
        session_id="test-123",
        duration_seconds=30
    )

    assert result["success"] is True
    assert result["duration_seconds"] == 30
    assert "music_url" in result
    assert result["twiml_action"] == "play"


@pytest.mark.asyncio
async def test_handle_ivr_menu():
    """Test IVR menu handling"""
    # Test valid selection (1 = check availability)
    result = await handle_ivr_menu(
        session_id="test-123",
        dtmf_input="1",
        menu_level=1
    )

    assert result["success"] is True
    assert result["action"] == "check_availability"
    assert result["next_level"] == 2

    # Test operator (0)
    result = await handle_ivr_menu(
        session_id="test-123",
        dtmf_input="0",
        menu_level=1
    )

    assert result["success"] is True
    assert result["action"] == "operator"

    # Test invalid input
    result = await handle_ivr_menu(
        session_id="test-123",
        dtmf_input="9",
        menu_level=1
    )

    assert result["success"] is True
    assert result["action"] == "invalid"
    assert "Invalid selection" in result["message"]


@pytest.mark.asyncio
async def test_format_availability_for_voice():
    """Test formatting availability data for voice"""
    # No rooms available
    data = {
        "available": 0,
        "check_in": "January 15th",
        "check_out": "January 17th"
    }
    result = await format_for_voice(data, "availability")
    assert "don't have any rooms available" in result
    assert "January 15th" in result

    # One room available
    data = {
        "available": 1,
        "check_in": "January 15th",
        "check_out": "January 17th"
    }
    result = await format_for_voice(data, "availability")
    assert "1 room available" in result

    # Multiple rooms available
    data = {
        "available": 5,
        "check_in": "January 15th",
        "check_out": "January 17th"
    }
    result = await format_for_voice(data, "availability")
    assert "5 rooms available" in result


@pytest.mark.asyncio
async def test_format_reservation_for_voice():
    """Test formatting reservation data for voice"""
    data = {
        "confirmation_number": "ABC123",
        "guest_name": "John Smith",
        "check_in": "January 15th"
    }
    result = await format_for_voice(data, "reservation")

    assert "ABC123" in result
    assert "John Smith" in result
    assert "January 15th" in result
    assert "confirmed" in result.lower()


@pytest.mark.asyncio
async def test_format_lead_for_voice():
    """Test formatting lead data for voice"""
    data = {
        "lead_id": "LEAD-456"
    }
    result = await format_for_voice(data, "lead")

    assert "LEAD-456" in result
    assert "recorded" in result.lower()


@pytest.mark.asyncio
async def test_execute_voice_tool():
    """Test executing voice tools by name"""
    # Test valid tool
    result = await execute_voice_tool(
        "play_hold_music",
        session_id="test-123",
        duration_seconds=20
    )

    assert result["success"] is True
    assert result["duration_seconds"] == 20

    # Test invalid tool
    result = await execute_voice_tool(
        "nonexistent_tool",
        session_id="test-123"
    )

    assert result["success"] is False
    assert "not found" in result["error"]
    assert "available_tools" in result
