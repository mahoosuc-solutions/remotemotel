"""
Voice-specific tools for hotel operations

These tools are designed to work with voice interactions and integrate
with the existing hotel tools (check_availability, create_lead, etc.)
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


async def transfer_to_human(
    session_id: str,
    department: str = "front_desk",
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transfer call to a human operator

    Args:
        session_id: Voice session identifier
        department: Department to transfer to ('front_desk', 'housekeeping', 'management')
        reason: Reason for transfer

    Returns:
        Transfer status and phone number
    """
    logger.info(f"Session {session_id}: Transferring to {department}")

    # Department phone mapping (these should come from configuration)
    department_phones = {
        "front_desk": os.getenv("FRONT_DESK_PHONE", "+15555551234"),
        "housekeeping": os.getenv("HOUSEKEEPING_PHONE", "+15555551235"),
        "management": os.getenv("MANAGEMENT_PHONE", "+15555551236"),
        "maintenance": os.getenv("MAINTENANCE_PHONE", "+15555551237"),
    }

    phone = department_phones.get(department)

    if not phone:
        logger.error(f"No phone configured for department: {department}")
        return {
            "success": False,
            "error": f"Department '{department}' not found",
            "message": "I apologize, but I'm unable to transfer you at this time. Please try calling back."
        }

    return {
        "success": True,
        "department": department,
        "phone_number": phone,
        "reason": reason,
        "message": f"Transferring you to our {department.replace('_', ' ')} team. Please hold.",
        "twiml_action": "dial",
        "twiml_number": phone
    }


async def play_hold_music(
    session_id: str,
    duration_seconds: int = 30,
    music_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Play hold music while processing request

    Args:
        session_id: Voice session identifier
        duration_seconds: How long to play music
        music_url: URL of music file (uses default if None)

    Returns:
        Music playback information
    """
    logger.info(f"Session {session_id}: Playing hold music for {duration_seconds}s")

    default_music = os.getenv(
        "HOLD_MUSIC_URL",
        "https://assets.stayhive.ai/hold-music/gentle-piano.mp3"
    )

    music_url = music_url or default_music

    return {
        "success": True,
        "music_url": music_url,
        "duration_seconds": duration_seconds,
        "message": "Please hold while I look that up for you.",
        "twiml_action": "play",
        "twiml_url": music_url
    }


async def send_sms_confirmation(
    phone: str,
    message: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send SMS confirmation to guest

    Args:
        phone: Guest's phone number
        message: Message to send
        session_id: Voice session identifier (for tracking)

    Returns:
        SMS send status
    """
    logger.info(f"Sending SMS to {phone}: {message[:50]}...")

    try:
        from twilio.rest import Client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not all([account_sid, auth_token, from_number]):
            logger.error("Twilio not configured for SMS")
            return {
                "success": False,
                "error": "SMS not configured",
                "message": "I'm unable to send an SMS at this time. Would you like me to email you instead?"
            }

        client = Client(account_sid, auth_token)

        sms = client.messages.create(
            body=message,
            from_=from_number,
            to=phone
        )

        logger.info(f"SMS sent successfully: {sms.sid}")

        return {
            "success": True,
            "message_sid": sms.sid,
            "to": phone,
            "message": "I've sent you a confirmation via SMS.",
            "status": sms.status
        }

    except Exception as e:
        logger.error(f"Failed to send SMS: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "I encountered an error sending the SMS. Would you like to try a different contact method?"
        }


async def schedule_callback(
    phone: str,
    callback_time: datetime,
    reason: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Schedule a callback to the guest

    Args:
        phone: Guest's phone number
        callback_time: When to call back
        reason: Reason for callback
        session_id: Voice session identifier

    Returns:
        Callback scheduling status
    """
    logger.info(f"Scheduling callback to {phone} at {callback_time}")

    # TODO: Integrate with actual scheduling system
    # For now, return mock response

    return {
        "success": True,
        "phone": phone,
        "callback_time": callback_time.isoformat(),
        "reason": reason,
        "message": f"I've scheduled a callback to {phone} at {callback_time.strftime('%I:%M %p')}.",
        "callback_id": f"CB-{datetime.utcnow().timestamp()}"
    }


async def handle_ivr_menu(
    session_id: str,
    dtmf_input: str,
    menu_level: int = 1
) -> Dict[str, Any]:
    """
    Handle IVR menu DTMF input

    Args:
        session_id: Voice session identifier
        dtmf_input: DTMF digit pressed (0-9, *, #)
        menu_level: Current menu level

    Returns:
        Menu action and response
    """
    logger.info(f"Session {session_id}: IVR input '{dtmf_input}' at level {menu_level}")

    # Main menu (level 1)
    if menu_level == 1:
        menu_actions = {
            "1": {
                "action": "check_availability",
                "message": "You selected room availability. Let me connect you to our booking system.",
                "next_level": 2
            },
            "2": {
                "action": "existing_reservation",
                "message": "You selected existing reservations. Please provide your confirmation number.",
                "next_level": 3
            },
            "3": {
                "action": "amenities_info",
                "message": "You selected hotel amenities and services information.",
                "next_level": 4
            },
            "4": {
                "action": "transfer_to_human",
                "message": "Transferring you to a staff member. Please hold.",
                "next_level": 0
            },
            "0": {
                "action": "operator",
                "message": "Connecting you to the front desk.",
                "next_level": 0
            }
        }

        action = menu_actions.get(dtmf_input, {
            "action": "invalid",
            "message": "Invalid selection. Please press 1 for availability, 2 for existing reservations, 3 for amenities, or 0 for the front desk.",
            "next_level": 1
        })

        return {
            "success": True,
            "action": action["action"],
            "message": action["message"],
            "next_level": action["next_level"],
            "dtmf_input": dtmf_input
        }

    # Additional menu levels can be added here
    return {
        "success": False,
        "action": "unknown",
        "message": "I didn't understand that selection. Let me connect you to a staff member.",
        "next_level": 0
    }


async def get_caller_history(
    phone: str,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Retrieve previous interactions with this caller

    Args:
        phone: Caller's phone number
        limit: Maximum number of calls to retrieve

    Returns:
        Caller history
    """
    logger.info(f"Retrieving caller history for {phone}")

    # TODO: Query database for actual call history
    # For now, return mock response

    return {
        "success": True,
        "phone": phone,
        "call_count": 0,
        "last_call": None,
        "previous_reservations": [],
        "previous_leads": [],
        "notes": None,
        "message": "This appears to be your first time calling us. Welcome!"
    }


async def record_voice_note(
    session_id: str,
    max_duration_seconds: int = 60
) -> Dict[str, Any]:
    """
    Record a voice note from the caller

    Args:
        session_id: Voice session identifier
        max_duration_seconds: Maximum recording duration

    Returns:
        Recording information
    """
    logger.info(f"Session {session_id}: Starting voice recording (max {max_duration_seconds}s)")

    return {
        "success": True,
        "session_id": session_id,
        "max_duration": max_duration_seconds,
        "message": "Please leave your message after the beep. Press any key when you're done.",
        "twiml_action": "record",
        "twiml_max_length": max_duration_seconds,
        "twiml_finish_on_key": "#"
    }


async def announce_to_session(
    session_id: str,
    message: str,
    voice: str = "Polly.Joanna"
) -> Dict[str, Any]:
    """
    Announce a message to the caller via TTS

    Args:
        session_id: Voice session identifier
        message: Text to speak
        voice: TTS voice to use

    Returns:
        Announcement status
    """
    logger.info(f"Session {session_id}: Announcing message: {message[:50]}...")

    return {
        "success": True,
        "session_id": session_id,
        "message": message,
        "voice": voice,
        "twiml_action": "say",
        "twiml_text": message,
        "twiml_voice": voice
    }


async def format_for_voice(data: Dict[str, Any], data_type: str = "availability") -> str:
    """
    Format data for voice output

    Converts structured data into natural language suitable for TTS.

    Args:
        data: Data to format
        data_type: Type of data ('availability', 'reservation', 'lead', etc.)

    Returns:
        Natural language description
    """
    if data_type == "availability":
        # Format room availability for voice
        available = data.get("available", 0)
        check_in = data.get("check_in")
        check_out = data.get("check_out")

        if available == 0:
            return f"I'm sorry, we don't have any rooms available from {check_in} to {check_out}."
        elif available == 1:
            return f"Great news! We have 1 room available from {check_in} to {check_out}."
        else:
            return f"Excellent! We have {available} rooms available from {check_in} to {check_out}."

    elif data_type == "reservation":
        # Format reservation confirmation for voice
        confirmation = data.get("confirmation_number")
        guest_name = data.get("guest_name")
        check_in = data.get("check_in")

        return f"Your reservation is confirmed, {guest_name}. Your confirmation number is {confirmation}. We look forward to welcoming you on {check_in}."

    elif data_type == "lead":
        # Format lead creation for voice
        lead_id = data.get("lead_id")

        return f"Thank you for your interest. I've recorded your inquiry as reference number {lead_id}. A member of our team will follow up with you shortly."

    else:
        # Generic formatting
        return str(data)


# Tool registry for easy access
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


async def execute_voice_tool(
    tool_name: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute a voice tool by name

    Args:
        tool_name: Name of the tool to execute
        **kwargs: Tool parameters

    Returns:
        Tool execution result
    """
    tool = VOICE_TOOLS.get(tool_name)

    if not tool:
        logger.error(f"Unknown voice tool: {tool_name}")
        return {
            "success": False,
            "error": f"Tool '{tool_name}' not found",
            "available_tools": list(VOICE_TOOLS.keys())
        }

    try:
        result = await tool(**kwargs)
        logger.info(f"Voice tool '{tool_name}' executed successfully")
        return result

    except Exception as e:
        logger.error(f"Error executing voice tool '{tool_name}': {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "tool": tool_name
        }
