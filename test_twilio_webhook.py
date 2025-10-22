#!/usr/bin/env python3
"""
Test script to verify Twilio signature validation is working correctly

This script simulates a Twilio webhook call to the deployed Cloud Run service
to ensure the signature validation is properly handling HTTPS URLs.
"""

import requests
from twilio.request_validator import RequestValidator
from urllib.parse import urlencode

# Load credentials from .env.local
env_vars = {}
with open('.env.local', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key] = value

AUTH_TOKEN = env_vars.get('TWILIO_AUTH_TOKEN')
SERVICE_URL = "https://westbethel-operator-1048462921095.us-central1.run.app"

print("=" * 70)
print("TWILIO WEBHOOK SIGNATURE VALIDATION TEST")
print("=" * 70)

# Create a validator instance
validator = RequestValidator(AUTH_TOKEN)

# The URL that Twilio will call
webhook_url = f"{SERVICE_URL}/voice/twilio/inbound"

# Parameters that Twilio sends
params = {
    "CallSid": "CA_test_signature_validation_12345",
    "From": "+15551234567",
    "To": "+12072203501",
    "CallStatus": "ringing",
    "Direction": "inbound",
    "ApiVersion": "2010-04-01",
}

print(f"\nWebhook URL: {webhook_url}")
print(f"\nParameters:")
for key, value in params.items():
    print(f"  {key}: {value}")

# Compute the signature that Twilio would send
signature = validator.compute_signature(webhook_url, params)

print(f"\nComputed Signature: {signature}")

# Make the request with the signature
headers = {
    "X-Twilio-Signature": signature,
}

print(f"\nSending POST request to {webhook_url}...")
print(f"Headers: {headers}")

try:
    response = requests.post(
        webhook_url,
        data=params,
        headers=headers,
        timeout=10
    )

    print(f"\n✅ Response Status: {response.status_code}")
    print(f"\nResponse Body:")
    print(response.text)

    if response.status_code == 200:
        if "technical difficulties" in response.text.lower() or "sorry" in response.text.lower():
            print("\n❌ ERROR: Signature validation may have failed (error TwiML returned)")
        else:
            print("\n✅ SUCCESS: Signature validation passed! The service accepted the request.")
    else:
        print(f"\n❌ ERROR: Unexpected status code {response.status_code}")

except Exception as e:
    print(f"\n❌ ERROR: Request failed: {e}")

print("\n" + "=" * 70)
print("Now checking Cloud Run logs for signature validation...")
print("=" * 70)
