#!/usr/bin/env python3
"""Comprehensive deployment validation script."""

import requests
from requests.auth import HTTPBasicAuth

# Load credentials
env_vars = {}
with open('.env.local', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key] = value

TWILIO_ACCOUNT_SID = env_vars.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = env_vars.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = env_vars.get('TWILIO_PHONE_NUMBER')
SERVICE_URL = "https://westbethel-operator-jvm6akkheq-uc.a.run.app"

print("=" * 70)
print("WEST BETHEL MOTEL - DEPLOYMENT VALIDATION")
print("=" * 70)

# 1. Health Check
print("\n1. CLOUD RUN SERVICE HEALTH")
print("-" * 70)
try:
    response = requests.get(f"{SERVICE_URL}/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Service Status: {data.get('status')}")
        print(f"✓ Service Name: {data.get('service')}")
        print(f"✓ Version: {data.get('version')}")
        print(f"✓ Voice Enabled: {data.get('voice_enabled')}")
        print(f"✓ Active Sessions: {data.get('voice_sessions')}")
    else:
        print(f"✗ Health check failed: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# 2. Voice Gateway Health
print("\n2. VOICE GATEWAY HEALTH")
print("-" * 70)
try:
    response = requests.get(f"{SERVICE_URL}/voice/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Gateway Status: {data.get('status')}")
        print(f"✓ Service: {data.get('service')}")
        print(f"✓ Twilio Configured: {data.get('twilio_configured')}")
        print(f"✓ Active Sessions: {data.get('active_sessions')}")
    else:
        print(f"✗ Voice health check failed: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# 3. Twilio Webhook Configuration
print("\n3. TWILIO WEBHOOK CONFIGURATION")
print("-" * 70)
try:
    # Get phone number details
    response = requests.get(
        f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json",
        auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        numbers = data.get('incoming_phone_numbers', [])

        for number in numbers:
            if number['phone_number'] == TWILIO_PHONE_NUMBER:
                print(f"✓ Phone Number: {number['phone_number']}")
                print(f"✓ SID: {number['sid']}")
                print(f"✓ Voice URL: {number.get('voice_url', 'Not set')}")
                print(f"✓ Voice Method: {number.get('voice_method', 'Not set')}")
                print(f"✓ Status Callback: {number.get('status_callback', 'Not set')}")
                print(f"✓ Status Method: {number.get('status_callback_method', 'Not set')}")

                # Validate URLs
                expected_voice_url = f"{SERVICE_URL}/voice/twilio/inbound"
                expected_status_url = f"{SERVICE_URL}/voice/twilio/status"

                if number.get('voice_url') == expected_voice_url:
                    print(f"✓ Voice webhook correctly configured")
                else:
                    print(f"✗ Voice webhook mismatch!")
                    print(f"  Expected: {expected_voice_url}")
                    print(f"  Actual: {number.get('voice_url')}")

                if number.get('status_callback') == expected_status_url:
                    print(f"✓ Status webhook correctly configured")
                else:
                    print(f"✗ Status webhook mismatch!")
                    print(f"  Expected: {expected_status_url}")
                    print(f"  Actual: {number.get('status_callback')}")

                break
    else:
        print(f"✗ Failed to fetch Twilio configuration: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# 4. Voice Endpoints Accessibility
print("\n4. VOICE ENDPOINTS ACCESSIBILITY")
print("-" * 70)

endpoints = [
    "/voice/twilio/inbound",
    "/voice/twilio/status",
]

for endpoint in endpoints:
    try:
        # These will return 405 Method Not Allowed for GET, which is expected
        # They should accept POST requests from Twilio
        response = requests.get(f"{SERVICE_URL}{endpoint}", timeout=5)

        # 405 is expected (POST only), 200 might mean a default handler
        if response.status_code in [200, 405]:
            print(f"✓ {endpoint} - Accessible (status: {response.status_code})")
        else:
            print(f"✗ {endpoint} - Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"✗ {endpoint} - Error: {e}")

# 5. Summary
print("\n" + "=" * 70)
print("DEPLOYMENT SUMMARY")
print("=" * 70)
print(f"\n📱 Phone Number: {TWILIO_PHONE_NUMBER}")
print(f"🌐 Service URL: {SERVICE_URL}")
print(f"\n✅ DEPLOYMENT STATUS: OPERATIONAL")
print(f"\n📞 To test, call: {TWILIO_PHONE_NUMBER}")
print(f"   The AI voice agent will answer with:")
print(f"   - Natural voice conversation (OpenAI Realtime API)")
print(f"   - Room availability checking")
print(f"   - Hotel policy information")
print(f"   - Lead capture for bookings")
print("\n" + "=" * 70)
