#!/usr/bin/env python3
"""
Twilio Setup Verification Script

This script verifies your Twilio configuration and tests the connection.
It checks:
1. Environment variables are set
2. Twilio credentials are valid
3. Phone number is verified
4. Webhook URLs are accessible (if ngrok is running)
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
env_file = project_root / ".env.local"
load_dotenv(env_file)

def check_env_vars():
    """Check if required environment variables are set"""
    print("🔍 Checking environment variables...")

    required_vars = {
        "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID"),
        "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN"),
        "TWILIO_PHONE_NUMBER": os.getenv("TWILIO_PHONE_NUMBER"),
    }

    optional_vars = {
        "TWILIO_WEBHOOK_URL": os.getenv("TWILIO_WEBHOOK_URL"),
        "VOICE_WEBSOCKET_URL": os.getenv("VOICE_WEBSOCKET_URL"),
    }

    all_set = True
    for var_name, value in required_vars.items():
        if value:
            # Mask sensitive values
            if "TOKEN" in var_name or "KEY" in var_name:
                display = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            elif "SID" in var_name:
                display = value[:8] + "..." if len(value) > 8 else value
            else:
                display = value
            print(f"  ✅ {var_name}: {display}")
        else:
            print(f"  ❌ {var_name}: NOT SET")
            all_set = False

    print("\n📝 Optional variables:")
    for var_name, value in optional_vars.items():
        if value:
            print(f"  ✅ {var_name}: {value}")
        else:
            print(f"  ⚠️  {var_name}: NOT SET")

    return all_set

def verify_twilio_credentials():
    """Verify Twilio credentials by making an API call"""
    print("\n🔐 Verifying Twilio credentials...")

    try:
        from twilio.rest import Client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        # Note: If using API Key, account_sid should be the actual Account SID
        # and auth_token should be the API Key Secret
        client = Client(account_sid, auth_token)

        # Try to fetch account details
        account = client.api.accounts(account_sid).fetch()

        print(f"  ✅ Connected to Twilio account: {account.friendly_name}")
        print(f"  📊 Account Status: {account.status}")
        print(f"  🆔 Account SID: {account.sid[:8]}...")

        return True

    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ Failed to connect to Twilio: {error_msg}")

        # Provide helpful error messages
        if "Unable to create record" in error_msg or "authenticate" in error_msg.lower():
            print("\n💡 Tips:")
            print("  - TWILIO_ACCOUNT_SID should be your main Account SID (starts with 'AC')")
            print("  - TWILIO_AUTH_TOKEN should be your Auth Token")
            print("  - If using API Keys:")
            print("    • TWILIO_ACCOUNT_SID = Your Account SID (AC...)")
            print("    • TWILIO_AUTH_TOKEN = API Key Secret (NOT the API Key SID)")
            print("\n  You can find these at: https://console.twilio.com/")

        return False

def verify_phone_number():
    """Verify the configured phone number"""
    print("\n📞 Verifying phone number...")

    try:
        from twilio.rest import Client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        phone_number = os.getenv("TWILIO_PHONE_NUMBER")

        client = Client(account_sid, auth_token)

        # Fetch phone number details
        number = client.incoming_phone_numbers.list(phone_number=phone_number)

        if number:
            num = number[0]
            print(f"  ✅ Phone number verified: {num.phone_number}")
            print(f"  📝 Friendly name: {num.friendly_name}")
            print(f"  🌐 Voice URL: {num.voice_url or 'Not configured'}")
            print(f"  📲 SMS URL: {num.sms_url or 'Not configured'}")

            # Check if webhooks are configured
            if not num.voice_url:
                print("\n  ⚠️  Voice webhook not configured in Twilio console")
                print("     You'll need to set this up for inbound calls")

            return True
        else:
            print(f"  ❌ Phone number {phone_number} not found in your account")
            print("     Available numbers:")

            all_numbers = client.incoming_phone_numbers.list(limit=10)
            for num in all_numbers:
                print(f"     - {num.phone_number} ({num.friendly_name})")

            return False

    except Exception as e:
        print(f"  ❌ Error verifying phone number: {e}")
        return False

def test_webhook_accessibility():
    """Test if webhook URLs are accessible"""
    print("\n🌐 Testing webhook accessibility...")

    webhook_url = os.getenv("TWILIO_WEBHOOK_URL", "http://localhost:8000")

    try:
        import requests

        # Test health endpoint
        health_url = f"{webhook_url}/health"
        print(f"  Testing: {health_url}")

        response = requests.get(health_url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Server is running")
            print(f"     Voice enabled: {data.get('voice_enabled', False)}")
            print(f"     Active sessions: {data.get('voice_sessions', 0)}")
            return True
        else:
            print(f"  ❌ Server returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"  ⚠️  Cannot reach webhook URL: {e}")
        print("     This is normal for localhost - you'll need ngrok for external access")
        return False

def print_next_steps():
    """Print next steps for setup"""
    print("\n" + "="*70)
    print("📋 NEXT STEPS")
    print("="*70)

    print("\n1️⃣  Start the voice server:")
    print("   cd /home/webemo-aaron/projects/front-desk")
    print("   . venv/bin/activate")
    print("   export PYTHONPATH=/home/webemo-aaron/projects/front-desk:$PYTHONPATH")
    print("   python apps/operator-runtime/main.py")

    print("\n2️⃣  For local testing, install and run ngrok:")
    print("   # Install ngrok from https://ngrok.com/download")
    print("   ngrok http 8000")
    print("   # Copy the https URL (e.g., https://abc123.ngrok.io)")

    print("\n3️⃣  Configure Twilio webhooks:")
    print("   Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
    print("   Click on your phone number")
    print("   Under 'Voice Configuration':")
    print("     - A CALL COMES IN: Webhook")
    print("     - URL: https://your-ngrok-url.ngrok.io/voice/twilio/inbound")
    print("     - HTTP: POST")
    print("   Under 'Call Status Changes':")
    print("     - URL: https://your-ngrok-url.ngrok.io/voice/twilio/status")
    print("     - HTTP: POST")
    print("   Click 'Save'")

    print("\n4️⃣  Test your setup:")
    print("   Call your Twilio number: " + os.getenv("TWILIO_PHONE_NUMBER", "YOUR_PHONE_NUMBER"))
    print("   You should hear the AI concierge greeting!")

    print("\n5️⃣  Monitor calls:")
    print("   # In a new terminal:")
    print("   curl http://localhost:8000/voice/sessions")
    print("   # Or check Twilio logs:")
    print("   https://console.twilio.com/us1/monitor/logs/calls")

    print("\n" + "="*70)

def main():
    """Main verification function"""
    print("="*70)
    print("🎙️  TWILIO SETUP VERIFICATION")
    print("="*70)

    results = {
        "env_vars": check_env_vars(),
        "credentials": False,
        "phone_number": False,
        "webhook": False,
    }

    if results["env_vars"]:
        results["credentials"] = verify_twilio_credentials()

        if results["credentials"]:
            results["phone_number"] = verify_phone_number()

    results["webhook"] = test_webhook_accessibility()

    # Summary
    print("\n" + "="*70)
    print("📊 VERIFICATION SUMMARY")
    print("="*70)

    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check.replace('_', ' ').title()}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All checks passed! Your Twilio setup is ready.")
    else:
        print("\n⚠️  Some checks failed. Please review the errors above.")

    print_next_steps()

if __name__ == "__main__":
    main()
