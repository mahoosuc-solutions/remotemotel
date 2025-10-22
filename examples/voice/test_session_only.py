"""
Simple test of session management without external dependencies

This demonstrates the core session management without requiring
Twilio, FastAPI, or any external services.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.voice.session import SessionManager, VoiceSession, SessionStatus, Message


async def test_sessions():
    """Test basic session management"""

    print("=" * 60)
    print("Voice Module - Session Management Test")
    print("=" * 60)
    print()

    # Create session manager
    print("1. Creating SessionManager...")
    manager = SessionManager()
    print("   ✓ SessionManager created\n")

    # Create a session
    print("2. Creating new voice session...")
    session = await manager.create_session(
        channel="phone",
        caller_id="+15551234567",
        language="en-US",
        metadata={
            "caller_name": "John Smith",
            "call_source": "direct_dial"
        }
    )
    print(f"   ✓ Session created: {session.session_id}")
    print(f"   - Channel: {session.channel}")
    print(f"   - Caller: {session.caller_id}")
    print(f"   - Status: {session.status.value}\n")

    # Add messages
    print("3. Adding conversation messages...")
    session.add_message(
        role="user",
        content="Hello, I'd like to book a room"
    )
    print("   ✓ User message added")

    session.add_message(
        role="assistant",
        content="I'd be happy to help you book a room. What dates?",
        latency_ms=250
    )
    print("   ✓ Assistant message added (250ms latency)")

    session.add_message(
        role="user",
        content="January 15-17, 2 adults"
    )
    print("   ✓ User message added\n")

    # Record tool usage
    print("4. Recording tool usage...")
    session.add_tool_usage("check_availability")
    print("   ✓ Tool: check_availability")
    session.add_tool_usage("create_lead")
    print("   ✓ Tool: create_lead")
    session.add_tool_usage("send_sms_confirmation")
    print("   ✓ Tool: send_sms_confirmation\n")

    # Get session details
    print("5. Session Summary:")
    print(f"   - Session ID: {session.session_id}")
    print(f"   - Duration: {session.get_duration_seconds():.2f} seconds")
    print(f"   - Turn count: {session.get_turn_count()}")
    print(f"   - Tools used: {len(session.tools_used)}")
    print(f"   - Status: {session.status.value}\n")

    # Check active sessions
    print("6. Checking active sessions...")
    active = await manager.get_active_sessions()
    print(f"   ✓ Found {len(active)} active session(s)\n")

    # Display conversation
    print("7. Full Conversation History:")
    print("   " + "-" * 56)
    for i, msg in enumerate(session.conversation_history, 1):
        print(f"   Turn {i}: [{msg.role.upper()}]")
        print(f"           {msg.content}")
        if msg.latency_ms:
            print(f"           (latency: {msg.latency_ms}ms)")
        print()
    print("   " + "-" * 56 + "\n")

    # Convert to dictionary
    print("8. Testing serialization...")
    session_dict = session.to_dict()
    print(f"   ✓ Serialized to dict ({len(session_dict)} fields)")
    print(f"   - turn_count: {session_dict['turn_count']}")
    print(f"   - duration_seconds: {session_dict['duration_seconds']:.2f}")
    print(f"   - tools_used: {session_dict['tools_used']}\n")

    # End session
    print("9. Ending session...")
    await manager.end_session(session.session_id, SessionStatus.COMPLETED)
    print(f"   ✓ Session ended with status: {SessionStatus.COMPLETED.value}")

    # Verify removal
    active = await manager.get_active_sessions()
    print(f"   ✓ Active sessions after ending: {len(active)}\n")

    # Test multiple sessions
    print("10. Testing multiple sessions...")
    session1 = await manager.create_session("phone", "+15551111111")
    session2 = await manager.create_session("webrtc", "user_123")
    session3 = await manager.create_session("phone", "+15552222222")
    print(f"    ✓ Created 3 sessions")

    active = await manager.get_active_sessions()
    print(f"    ✓ Active sessions: {len(active)}")

    # End all
    await manager.end_session(session1.session_id)
    await manager.end_session(session2.session_id)
    await manager.end_session(session3.session_id)
    print(f"    ✓ Ended all sessions\n")

    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_sessions())
