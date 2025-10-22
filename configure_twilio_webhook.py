#!/usr/bin/env python3
"""
Twilio Webhook Configuration Script
Automatically updates the Twilio phone number webhook to point to the deployed Voice AI service
"""
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Twilio configuration from .env.local
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Voice AI service configuration
VOICE_AI_SERVICE_URL = os.getenv(
    "VOICE_AI_SERVICE_URL",
    "https://voice-ai-assistant-jvm6akkheq-uc.a.run.app"
)
WEBHOOK_URL = f"{VOICE_AI_SERVICE_URL}/incoming-call"

def main():
    print("🔧 Twilio Webhook Configuration Script")
    print("=" * 50)
    
    # Validate configuration
    if not TWILIO_ACCOUNT_SID:
        print("❌ Error: TWILIO_ACCOUNT_SID not found in .env.local")
        return False
        
    if not TWILIO_AUTH_TOKEN:
        print("❌ Error: TWILIO_AUTH_TOKEN not found in .env.local")
        return False
        
    if not TWILIO_PHONE_NUMBER:
        print("❌ Error: TWILIO_PHONE_NUMBER not found in .env.local")
        return False
    
    print(f"📱 Phone Number: {TWILIO_PHONE_NUMBER}")
    print(f"🔗 Webhook URL: {WEBHOOK_URL}")
    print(f"🏨 Service: West Bethel Motel Voice AI")
    print()
    
    try:
        # Initialize Twilio client
        print("🚀 Connecting to Twilio...")
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Get phone number SID
        print("🔍 Looking up phone number...")
        phone_numbers = client.incoming_phone_numbers.list(phone_number=TWILIO_PHONE_NUMBER)
        
        if not phone_numbers:
            print(f"❌ Error: Phone number {TWILIO_PHONE_NUMBER} not found in your Twilio account")
            return False
            
        phone_number_resource = phone_numbers[0]
        print(f"✅ Found phone number: {phone_number_resource.phone_number}")
        print(f"   - Friendly Name: {phone_number_resource.friendly_name}")
        print(f"   - Current Voice URL: {phone_number_resource.voice_url}")
        print()
        
        # Update webhook configuration
        print("🔧 Updating webhook configuration...")
        updated_number = client.incoming_phone_numbers(phone_number_resource.sid).update(
            voice_url=WEBHOOK_URL,
            voice_method='POST'
        )
        
        print("✅ Webhook configuration updated successfully!")
        print()
        print("📋 Configuration Summary:")
        print(f"   - Phone Number: {updated_number.phone_number}")
        print(f"   - Voice Webhook: {updated_number.voice_url}")
        print(f"   - Method: {updated_number.voice_method}")
        print()
        
        # Test the webhook endpoint
        print("🧪 Testing webhook endpoint...")
        import requests
        try:
            response = requests.get(f"{VOICE_AI_SERVICE_URL}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Voice AI service is healthy!")
                print(f"   - Hotel: {health_data.get('hotel', 'Unknown')}")
                print(f"   - OpenAI Configured: {health_data.get('openai_configured', False)}")
            else:
                print(f"⚠️  Warning: Health check returned status {response.status_code}")
        except Exception as e:
            print(f"⚠️  Warning: Could not test webhook endpoint: {e}")
        
        print()
        print("🎉 SUCCESS! Your Twilio phone number is now configured for Voice AI!")
        print()
        print("📞 READY TO TEST:")
        print(f"   Call {TWILIO_PHONE_NUMBER} to test your Voice AI assistant")
        print("   Expected experience:")
        print("   1. Greeting: 'Hello! Welcome to West Bethel Motel...'")
        print("   2. AI Assistant connects via OpenAI Realtime API")
        print("   3. Natural conversation about hotel services")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring Twilio webhook: {e}")
        print()
        print("🔍 Troubleshooting:")
        print("   1. Verify Twilio credentials in .env.local")
        print("   2. Check that the phone number belongs to your account")
        print("   3. Ensure you have permissions to modify phone number settings")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("🏁 Configuration complete!")
    else:
        print("❌ Configuration failed. Please check the errors above.")
        exit(1)
