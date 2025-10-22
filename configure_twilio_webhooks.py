#!/usr/bin/env python3
"""Configure Twilio webhooks for the deployed Cloud Run service."""

import os
import requests
from requests.auth import HTTPBasicAuth

# Load credentials from .env.local
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

# Cloud Run service URL
SERVICE_URL = "https://westbethel-operator-jvm6akkheq-uc.a.run.app"

print(f"Twilio Account SID: {TWILIO_ACCOUNT_SID}")
print(f"Phone Number: {TWILIO_PHONE_NUMBER}")
print(f"Service URL: {SERVICE_URL}")

# Get phone number SID
print("\nFetching phone numbers...")
response = requests.get(
    f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json",
    auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
)

if response.status_code != 200:
    print(f"Error fetching phone numbers: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
phone_numbers = data.get('incoming_phone_numbers', [])

print(f"\nFound {len(phone_numbers)} phone number(s):")
for number in phone_numbers:
    print(f"  {number['phone_number']}: {number['sid']}")

# Find the SID for our phone number
phone_sid = None
for number in phone_numbers:
    if number['phone_number'] == TWILIO_PHONE_NUMBER:
        phone_sid = number['sid']
        break

if not phone_sid:
    print(f"\nError: Phone number {TWILIO_PHONE_NUMBER} not found!")
    exit(1)

print(f"\nFound SID for {TWILIO_PHONE_NUMBER}: {phone_sid}")

# Update webhooks
print("\nUpdating webhooks...")
update_data = {
    'VoiceUrl': f"{SERVICE_URL}/voice/twilio/inbound",
    'VoiceMethod': 'POST',
    'StatusCallback': f"{SERVICE_URL}/voice/twilio/status",
    'StatusCallbackMethod': 'POST'
}

response = requests.post(
    f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers/{phone_sid}.json",
    data=update_data,
    auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
)

if response.status_code == 200:
    print("\n✓ Webhooks updated successfully!")
    result = response.json()
    print(f"\nVoice URL: {result.get('voice_url')}")
    print(f"Status Callback: {result.get('status_callback')}")
else:
    print(f"\nError updating webhooks: {response.status_code}")
    print(response.text)
    exit(1)
