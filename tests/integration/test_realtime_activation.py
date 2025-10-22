"""
Realtime API Activation Test

This test verifies that the Realtime API integration is properly activated
and can connect to OpenAI's Realtime API.

Usage:
    python tests/integration/test_realtime_activation.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env.local")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_realtime_client_connection():
    """Test 1: RealtimeAPIClient Connection"""
    print("\n" + "="*60)
    print("TEST 1: RealtimeAPIClient Connection")
    print("="*60)

    try:
        from packages.voice.realtime import create_realtime_client

        # Check configuration
        api_key = os.getenv("OPENAI_API_KEY")
        realtime_enabled = os.getenv("OPENAI_REALTIME_ENABLED", "false").lower() == "true"
        voice = os.getenv("OPENAI_REALTIME_VOICE", "alloy")

        print(f"✓ Realtime enabled: {realtime_enabled}")
        print(f"✓ Voice: {voice}")
        print(f"✓ API key configured: {'Yes' if api_key and api_key != 'your_openai_api_key_here' else 'No'}")

        if not realtime_enabled:
            print("⚠️  OPENAI_REALTIME_ENABLED is not set to true")
            return False

        if not api_key or api_key == "your_openai_api_key_here":
            print("⚠️  OPENAI_API_KEY is not configured")
            print("   Please set your OpenAI API key in .env.local")
            return False

        # Create client
        print("\nCreating RealtimeAPIClient...")
        client = create_realtime_client(
            voice=voice,
            instructions="You are a friendly hotel concierge."
        )

        # Connect
        print("Connecting to OpenAI Realtime API...")
        await client.connect()

        print("✅ Connected successfully!")

        # Get statistics
        await asyncio.sleep(1)
        stats = client.get_statistics()
        print(f"\nClient Statistics:")
        print(f"  - Connected: {stats['is_connected']}")
        print(f"  - Registered functions: {stats['registered_functions']}")
        print(f"  - Events received: {stats['events_received']}")

        # Disconnect
        await client.disconnect()
        print("✅ Disconnected successfully")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure websockets is installed: pip install websockets")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        logger.exception("Connection error")
        return False


async def test_function_registry():
    """Test 2: Function Registry"""
    print("\n" + "="*60)
    print("TEST 2: Function Registry")
    print("="*60)

    try:
        from packages.voice.function_registry import create_hotel_function_registry

        # Create registry
        registry = create_hotel_function_registry()

        # List functions
        functions = registry.list_functions()
        print(f"✓ Registered {len(functions)} functions:")
        for func_name in functions:
            schema = registry.get_function(func_name)
            print(f"  - {func_name}: {schema.description}")

        # Get OpenAI tools format
        tools = registry.get_openai_tools()
        print(f"\n✓ Generated {len(tools)} OpenAI tool schemas")

        # Test function execution
        print("\n✓ Testing function execution...")
        result = await registry.execute(
            name="check_availability",
            arguments={
                "check_in": "2025-10-20",
                "check_out": "2025-10-22",
                "adults": 2,
                "pets": False
            }
        )
        print(f"  check_availability result: {result}")

        print("✅ Function registry working correctly")
        return True

    except Exception as e:
        print(f"❌ Function registry error: {e}")
        logger.exception("Function registry error")
        return False


async def test_conversation_manager():
    """Test 3: Conversation Manager"""
    print("\n" + "="*60)
    print("TEST 3: Conversation Manager")
    print("="*60)

    try:
        from packages.voice.conversation import create_hotel_conversation_manager

        # Create manager
        hotel_name = os.getenv("HOTEL_NAME", "Our Hotel")
        hotel_location = os.getenv("HOTEL_LOCATION", "Downtown")

        manager = create_hotel_conversation_manager(
            hotel_name=hotel_name,
            location=hotel_location
        )

        print(f"✓ Created conversation manager for {hotel_name}")

        # Generate system instructions
        instructions = manager.generate_system_instructions()
        print(f"✓ Generated system instructions ({len(instructions)} chars)")
        print("\nFirst 200 characters:")
        print(instructions[:200] + "...")

        # Test conversation tracking
        manager.add_turn(
            role="user",
            content="I'd like to book a room",
            metadata={"source": "test"}
        )
        manager.add_turn(
            role="assistant",
            content="I'd be happy to help! What dates?",
            metadata={"source": "test"}
        )

        summary = manager.get_conversation_summary()
        print(f"\n✓ Conversation summary:\n{summary}")

        print("✅ Conversation manager working correctly")
        return True

    except Exception as e:
        print(f"❌ Conversation manager error: {e}")
        logger.exception("Conversation manager error")
        return False


async def test_realtime_bridge():
    """Test 4: Realtime Bridge Creation"""
    print("\n" + "="*60)
    print("TEST 4: Realtime Bridge Creation")
    print("="*60)

    try:
        from packages.voice.bridges.realtime_bridge import create_realtime_bridge

        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            print("⚠️  Skipping bridge test - API key not configured")
            return True

        # Create bridge
        print("Creating Realtime bridge...")
        hotel_name = os.getenv("HOTEL_NAME", "Our Hotel")
        hotel_location = os.getenv("HOTEL_LOCATION", "Downtown")

        bridge = await create_realtime_bridge(
            session_id="test_activation",
            hotel_name=hotel_name,
            hotel_location=hotel_location
        )

        print("✅ Bridge created successfully")

        # Get statistics
        stats = bridge.get_statistics()
        print(f"\nBridge Statistics:")
        print(f"  - Session ID: {stats['session_id']}")
        print(f"  - Active: {stats['is_active']}")
        print(f"  - Duration: {stats['duration_seconds']}s")
        print(f"  - Function calls: {stats['function_calls_executed']}")

        # Test text input (simulates conversation)
        print("\n✓ Testing text input...")
        await bridge.realtime_client.send_text(
            "Hello! Do you have any rooms available?"
        )

        # Wait for response
        print("✓ Waiting for response...")
        await asyncio.sleep(3)

        # Check updated statistics
        stats = bridge.get_statistics()
        print(f"\nUpdated Statistics:")
        print(f"  - Realtime messages sent: {stats['realtime_messages_sent']}")
        print(f"  - Realtime messages received: {stats['realtime_messages_received']}")

        # Stop bridge
        await bridge.stop()
        print("✅ Bridge stopped successfully")

        return True

    except Exception as e:
        print(f"❌ Realtime bridge error: {e}")
        logger.exception("Realtime bridge error")
        return False


async def run_all_tests():
    """Run all activation tests"""
    print("\n" + "="*60)
    print("REALTIME API ACTIVATION TESTS")
    print("="*60)

    results = {}

    # Test 1: Client connection
    results['client'] = await test_realtime_client_connection()

    # Test 2: Function registry
    results['registry'] = await test_function_registry()

    # Test 3: Conversation manager
    results['conversation'] = await test_conversation_manager()

    # Test 4: Realtime bridge
    results['bridge'] = await test_realtime_bridge()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Realtime API is activated and ready to use.")
        print("\nNext steps:")
        print("1. Configure your actual OpenAI API key in .env.local")
        print("2. Configure Twilio credentials for phone integration")
        print("3. Test with a real phone call")
        print("4. Monitor logs and statistics")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.exception("Unexpected error")
        sys.exit(1)
