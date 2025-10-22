#!/usr/bin/env python3
"""
Test the Voice AI Server endpoints
"""
import requests
import sys
import json

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: OK")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_incoming_call_endpoint():
    """Test the incoming call endpoint (should return TwiML)"""
    try:
        response = requests.post("http://localhost:8000/incoming-call", timeout=5)
        if response.status_code == 200:
            print("✅ Incoming call endpoint: OK")
            if "TwiML" in response.text or "VoiceResponse" in response.text or "Say" in response.text:
                print("   ✅ Returns valid TwiML response")
                return True
            else:
                print("   ⚠️ Response doesn't look like TwiML")
                print(f"   Response snippet: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Incoming call endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Incoming call endpoint error: {e}")
        return False

def main():
    print("🧪 Testing Voice AI Server...")
    print()
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        print("✅ Server is running")
    except Exception as e:
        print("❌ Server is not running or not accessible")
        print("   Make sure to start the server first:")
        print("   python3 voice_ai_server.py")
        sys.exit(1)
    
    print()
    
    # Test endpoints
    health_ok = test_health_endpoint()
    call_ok = test_incoming_call_endpoint()
    
    print()
    if health_ok and call_ok:
        print("🎉 All tests passed! Voice AI server is ready for Twilio.")
        print()
        print("Next steps:")
        print("1. Start ngrok: ngrok http 8000")
        print("2. Configure Twilio webhook to: https://your-ngrok-url.ngrok.app/incoming-call")
        print("3. Call your Twilio number to test!")
    else:
        print("❌ Some tests failed. Check the server logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()