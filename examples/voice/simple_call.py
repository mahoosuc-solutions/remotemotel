"""
Simple example of creating and managing a voice session

This demonstrates the basic voice module API without requiring
Twilio or external services.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.voice import SessionManager, SessionStatus
from packages.voice.tools import format_for_voice, execute_voice_tool

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def simulate_call():
    """Simulate a simple phone call interaction"""

    # Create session manager
    manager = SessionManager()

    # Create a new call session
    logger.info("Creating new call session...")
    session = await manager.create_session(
        channel="phone",
        caller_id="+15551234567",
        language="en-US",
        metadata={
            "caller_name": "John Smith",
            "call_source": "direct"
        }
    )

    logger.info(f"Session created: {session.session_id}")

    # Simulate conversation
    logger.info("\n--- Conversation Start ---")

    # Guest: Initial greeting
    session.add_message(
        role="user",
        content="Hello, I'd like to check room availability"
    )
    logger.info("Guest: Hello, I'd like to check room availability")

    # Assistant: Response
    session.add_message(
        role="assistant",
        content="I'd be happy to help you check availability. What dates are you looking for?",
        latency_ms=250
    )
    logger.info("AI: I'd be happy to help you check availability. What dates are you looking for?")

    # Guest: Provide dates
    session.add_message(
        role="user",
        content="January 15th to January 17th, for 2 adults"
    )
    logger.info("Guest: January 15th to January 17th, for 2 adults")

    # Simulate checking availability
    logger.info("\n--- Tool Execution ---")
    session.add_tool_usage("check_availability")

    # Mock availability result
    availability_data = {
        "available": 5,
        "check_in": "January 15th",
        "check_out": "January 17th"
    }

    # Format for voice
    voice_response = format_for_voice(availability_data, "availability")
    logger.info(f"AI (formatted for voice): {voice_response}")

    session.add_message(
        role="assistant",
        content=voice_response,
        latency_ms=450
    )

    # Guest: Wants to book
    session.add_message(
        role="user",
        content="Great! I'd like to book one room"
    )
    logger.info("Guest: Great! I'd like to book one room")

    # Create lead
    session.add_tool_usage("create_lead")
    logger.info("Tool executed: create_lead")

    # Send SMS confirmation
    logger.info("\n--- Sending SMS Confirmation ---")
    sms_result = await execute_voice_tool(
        "send_sms_confirmation",
        phone=session.caller_id,
        message="Thank you for your interest! Confirmation: LEAD-123",
        session_id=session.session_id
    )
    logger.info(f"SMS result: {sms_result.get('message', 'Error')}")

    session.add_tool_usage("send_sms_confirmation")

    # Assistant: Confirmation
    session.add_message(
        role="assistant",
        content="Perfect! I've created a reservation inquiry for you. Confirmation number LEAD-123. You should receive an SMS shortly.",
        latency_ms=300
    )
    logger.info("AI: Perfect! I've created a reservation inquiry...")

    # Display session summary
    logger.info("\n--- Session Summary ---")
    logger.info(f"Session ID: {session.session_id}")
    logger.info(f"Caller: {session.caller_id}")
    logger.info(f"Duration: {session.get_duration_seconds():.2f} seconds")
    logger.info(f"Conversation turns: {session.get_turn_count()}")
    logger.info(f"Tools used: {', '.join(session.tools_used)}")

    # Get all active sessions
    active_sessions = await manager.get_active_sessions()
    logger.info(f"\nActive sessions: {len(active_sessions)}")

    # End session
    logger.info("\n--- Ending Session ---")
    await manager.end_session(session.session_id, SessionStatus.COMPLETED)
    logger.info("Session ended successfully")

    # Verify session was removed
    active_sessions = await manager.get_active_sessions()
    logger.info(f"Active sessions after ending: {len(active_sessions)}")

    # Display conversation history
    logger.info("\n--- Full Conversation History ---")
    for turn in session.conversation_history:
        logger.info(f"[{turn.role.upper()}]: {turn.content}")


if __name__ == "__main__":
    print("=== Voice Module - Simple Call Example ===\n")
    asyncio.run(simulate_call())
    print("\n=== Example Complete ===")
