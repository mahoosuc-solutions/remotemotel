"""
Voice-specific tools for hotel operations.

These helpers are designed to work with realtime voice interactions and to
wrap the core hotel logic so the agent can provide friendly, structured
responses over the phone.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def transfer_to_human(
    session_id: Optional[str] = None,
    department: str = "front_desk",
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Return contact details for transferring a caller to staff."""

    session_identifier = session_id or "unknown"
    logger.info("Session %s: Transferring to %s", session_identifier, department)

    department_phones = {
        "front_desk": os.getenv("FRONT_DESK_PHONE", "+15555551234"),
        "housekeeping": os.getenv("HOUSEKEEPING_PHONE", "+15555551235"),
        "management": os.getenv("MANAGEMENT_PHONE", "+15555551236"),
        "maintenance": os.getenv("MAINTENANCE_PHONE", "+15555551237"),
    }

    phone = department_phones.get(department)
    if not phone:
        logger.error("No phone configured for department: %s", department)
        return {
            "success": False,
            "error": f"Department '{department}' not found",
            "message": "I apologize, but I'm unable to transfer you at this time.",
        }

    return {
        "success": True,
        "session_id": session_identifier,
        "department": department,
        "phone_number": phone,
        "reason": reason,
        "message": f"Transferring you to our {department.replace('_', ' ')} team. Please hold.",
        "twiml_action": "dial",
        "twiml_number": phone,
    }


async def play_hold_music(
    session_id: Optional[str] = None,
    duration_seconds: int = 30,
    music_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Play hold music while the assistant works on a request."""

    session_identifier = session_id or "unknown"
    logger.info("Session %s: Playing hold music for %ss", session_identifier, duration_seconds)

    default_music = os.getenv(
        "HOLD_MUSIC_URL",
        "https://assets.stayhive.ai/hold-music/gentle-piano.mp3",
    )

    music_url = music_url or default_music

    return {
        "success": True,
        "session_id": session_identifier,
        "music_url": music_url,
        "duration_seconds": duration_seconds,
        "message": "Please hold while I look that up for you.",
        "twiml_action": "play",
        "twiml_url": music_url,
    }


async def send_sms_confirmation(
    phone: str,
    message: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Send an SMS confirmation via Twilio."""

    session_identifier = session_id or "unknown"
    logger.info("Session %s: Sending SMS to %s", session_identifier, phone)

    try:
        from twilio.rest import Client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not all([account_sid, auth_token, from_number]):
            logger.error("Twilio SMS credentials not configured")
            return {
                "success": False,
                "error": "SMS not configured",
                "message": "I'm unable to send an SMS at this time. Would you like email instead?",
            }

        client = Client(account_sid, auth_token)
        sms = client.messages.create(body=message, from_=from_number, to=phone)

        return {
            "success": True,
            "session_id": session_identifier,
            "message_sid": sms.sid,
            "to": phone,
            "status": sms.status,
            "message": "I've sent you a confirmation via SMS.",
        }

    except Exception as exc:  # pragma: no cover - upstream errors
        logger.error("Failed to send SMS: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": str(exc),
            "message": "I ran into an issue sending that SMS. Would you like to try another contact method?",
        }


async def schedule_callback(
    phone: str,
    callback_time: datetime,
    reason: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a scheduled callback payload (mock implementation)."""

    session_identifier = session_id or "unknown"
    logger.info(
        "Session %s: Scheduling callback to %s at %s",
        session_identifier,
        phone,
        callback_time,
    )

    return {
        "success": True,
        "session_id": session_identifier,
        "phone": phone,
        "callback_time": callback_time.isoformat(),
        "reason": reason,
        "message": f"I've scheduled a callback to {phone} at {callback_time.strftime('%I:%M %p')}.",
        "callback_id": f"CB-{datetime.utcnow().timestamp()}",
    }


async def handle_ivr_menu(
    session_id: Optional[str] = None,
    dtmf_input: Optional[str] = None,
    menu_level: int = 1,
) -> Dict[str, Any]:
    """Handle IVR DTMF input and return the next action."""

    if dtmf_input is None:
        raise ValueError("dtmf_input is required")

    session_identifier = session_id or "unknown"
    logger.info(
        "Session %s: IVR input '%s' at level %s",
        session_identifier,
        dtmf_input,
        menu_level,
    )

    if menu_level == 1:
        menu_actions = {
            "1": {
                "action": "check_availability",
                "message": "You selected room availability. Let me connect you to our booking system.",
                "next_level": 2,
            },
            "2": {
                "action": "existing_reservation",
                "message": "You selected existing reservations. Please provide your confirmation number.",
                "next_level": 3,
            },
            "3": {
                "action": "amenities_info",
                "message": "You selected hotel amenities and services information.",
                "next_level": 4,
            },
            "4": {
                "action": "transfer_to_human",
                "message": "Transferring you to a staff member. Please hold.",
                "next_level": 0,
            },
            "0": {
                "action": "operator",
                "message": "Connecting you to the front desk.",
                "next_level": 0,
            },
        }

        action = menu_actions.get(
            dtmf_input,
            {
                "action": "invalid",
                "message": "Invalid selection. Please press 1 for availability, 2 for reservations, 3 for amenities, or 0 for the front desk.",
                "next_level": 1,
            },
        )

        return {
            "success": True,
            "session_id": session_identifier,
            "action": action["action"],
            "message": action["message"],
            "next_level": action["next_level"],
            "dtmf_input": dtmf_input,
        }

    return {
        "success": False,
        "session_id": session_identifier,
        "action": "unknown",
        "message": "I didn't understand that selection. Let me connect you to a staff member.",
        "next_level": 0,
    }


async def get_caller_history(phone: str, limit: int = 5) -> Dict[str, Any]:
    """Return previous caller interactions (placeholder implementation)."""

    logger.info("Retrieving caller history for %s", phone)

    return {
        "success": True,
        "phone": phone,
        "call_count": 0,
        "last_call": None,
        "previous_reservations": [],
        "previous_leads": [],
        "notes": None,
        "message": "This appears to be your first time calling us. Welcome!",
    }


async def record_voice_note(
    session_id: Optional[str] = None,
    max_duration_seconds: int = 60,
) -> Dict[str, Any]:
    """Return instructions to record a voice note."""

    session_identifier = session_id or "unknown"
    logger.info(
        "Session %s: Starting voice recording (max %ss)",
        session_identifier,
        max_duration_seconds,
    )

    return {
        "success": True,
        "session_id": session_identifier,
        "max_duration": max_duration_seconds,
        "message": "Please leave your message after the beep. Press any key when you're done.",
        "twiml_action": "record",
        "twiml_max_length": max_duration_seconds,
        "twiml_finish_on_key": "#",
    }


async def announce_to_session(
    session_id: Optional[str] = None,
    message: Optional[str] = None,
    voice: str = "Polly.Joanna",
) -> Dict[str, Any]:
    """Return a TTS announcement payload."""

    if message is None:
        raise ValueError("message is required")

    session_identifier = session_id or "unknown"
    logger.info("Session %s: Announcing message %s", session_identifier, message[:50])

    return {
        "success": True,
        "session_id": session_identifier,
        "message": message,
        "voice": voice,
        "twiml_action": "say",
        "twiml_text": message,
        "twiml_voice": voice,
    }


async def format_for_voice(data: Dict[str, Any], data_type: str = "availability") -> str:
    """Format structured data into natural language for TTS."""

    if data_type == "availability":
        available = data.get("available", 0)
        check_in = data.get("check_in")
        check_out = data.get("check_out")

        if not available:
            return f"I'm sorry, we don't have any rooms available from {check_in} to {check_out}."
        if available == 1:
            return f"Great news! We have 1 room available from {check_in} to {check_out}."
        return f"Excellent! We have {available} rooms available from {check_in} to {check_out}."

    if data_type == "reservation":
        confirmation = data.get("confirmation_number")
        guest_name = data.get("guest_name")
        check_in = data.get("check_in")
        return (
            f"Your reservation is confirmed, {guest_name}. "
            f"Your confirmation number is {confirmation}. We look forward to welcoming you on {check_in}."
        )

    if data_type == "lead":
        lead_id = data.get("lead_id")
        return (
            f"Thank you for your interest. I've recorded your inquiry as reference number {lead_id}. "
            "A member of our team will follow up with you shortly."
        )

    return str(data)


VOICE_TOOLS = {
    "transfer_to_human": transfer_to_human,
    "play_hold_music": play_hold_music,
    "send_sms_confirmation": send_sms_confirmation,
    "schedule_callback": schedule_callback,
    "handle_ivr_menu": handle_ivr_menu,
    "get_caller_history": get_caller_history,
    "record_voice_note": record_voice_note,
    "announce_to_session": announce_to_session,
    "format_for_voice": format_for_voice,
}


async def execute_voice_tool(tool_name: str, **kwargs: Any) -> Dict[str, Any]:
    """Execute a voice tool by name."""

    tool = VOICE_TOOLS.get(tool_name)
    if not tool:
        logger.error("Unknown voice tool: %s", tool_name)
        return {
            "success": False,
            "error": f"Tool '{tool_name}' not found",
            "available_tools": list(VOICE_TOOLS.keys()),
        }

    try:
        return await tool(**kwargs)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error executing voice tool '%s': %s", tool_name, exc, exc_info=True)
        return {
            "success": False,
            "error": str(exc),
            "tool": tool_name,
        }
