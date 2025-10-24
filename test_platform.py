#!/usr/bin/env python3
"""
Simple platform test script - validates core functionality without needing database
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all core modules can be imported"""
    print("Testing imports...")
    try:
        from packages.tools import search_kb, check_availability, create_lead, generate_payment_link
        from packages.hotel.api import router as hotel_router
        from packages.hotel.models import Base as HotelBase
        from packages.voice.models import Base as VoiceBase
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_mock_tools():
    """Test mock tool implementations"""
    print("\nTesting mock tools...")
    try:
        from packages.tools import search_kb, check_availability, create_lead, generate_payment_link

        # Test search_kb
        result = search_kb("pet policy")
        print(f"✓ search_kb: {len(result)} results")

        # Test check_availability
        result = check_availability("2025-10-25", "2025-10-27", 2, True)
        print(f"✓ check_availability: {result['available_rooms']} rooms")

        # Test create_lead
        result = create_lead("John Doe", "john@example.com", "+15551234567", "2025-10-25", "2025-10-27", 2)
        print(f"✓ create_lead: Lead ID {result['lead_id']}")

        # Test generate_payment_link
        result = generate_payment_link(250.00, "Test Booking", "john@example.com")
        print(f"✓ generate_payment_link: {result['payment_url']}")

        return True
    except Exception as e:
        print(f"✗ Tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_models():
    """Test that database models are defined correctly"""
    print("\nTesting database models...")
    try:
        from packages.hotel.models import Base as HotelBase, RoomInventory, Lead
        from packages.voice.models import Base as VoiceBase, VoiceCall, VoiceConversation

        print(f"✓ Hotel models: {len(HotelBase.metadata.tables)} tables")
        print(f"  - {', '.join(HotelBase.metadata.tables.keys())}")

        print(f"✓ Voice models: {len(VoiceBase.metadata.tables)} tables")
        print(f"  - {', '.join(VoiceBase.metadata.tables.keys())}")

        return True
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("FRONT DESK PLATFORM TEST")
    print("=" * 60)

    tests = [
        test_imports(),
        test_mock_tools(),
        test_database_models(),
    ]

    print("\n" + "=" * 60)
    passed = sum(tests)
    total = len(tests)
    print(f"RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("✓ Platform is ready for development!")
        return 0
    else:
        print("✗ Some tests failed - review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
