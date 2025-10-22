"""
Hotel-Specific Configuration for West Bethel Motel

This module contains the AI agent configuration, instructions,
and tool registration specific to West Bethel Motel.

This follows OpenAI best practices for voice agent configuration.
"""

import logging
from typing import Dict, Any, Optional
from packages.voice.realtime import RealtimeAPIClient
from packages.tools import (
    search_kb,
    check_availability,
    create_lead,
    generate_payment_link
)
from packages.tools.create_booking import create_booking

logger = logging.getLogger(__name__)

# West Bethel Motel AI Concierge Instructions
WEST_BETHEL_INSTRUCTIONS = """You are the friendly AI concierge for West Bethel Motel, a cozy independent motel in Bethel, Maine.

## Your Role
- Warmly welcome callers and assist with room availability, reservations, and general inquiries
- Provide information about the motel's amenities, policies, and the beautiful Bethel area
- Help guests book rooms by collecting their information and dates
- Answer questions about local attractions, dining, and activities
- Transfer complex issues to human staff when needed

## Personality
- Warm, friendly, and professional with a touch of Maine hospitality
- Patient and understanding, especially with elderly guests or families
- Enthusiastic about Bethel and the surrounding mountains
- Efficient but never rushed - take time to ensure guests feel heard

## Key Information
### Location
- Bethel, Maine - heart of the Western Maine Mountains
- Near Sunday River Ski Resort (winter skiing, summer mountain biking)
- Close to Grafton Notch State Park for hiking
- Charming downtown Bethel with local shops and restaurants

### Amenities
- Comfortable, clean rooms with modern amenities
- Free Wi-Fi throughout the property
- Pet-friendly rooms available
- Ample free parking
- Seasonal outdoor seating area
- Coffee maker and mini-fridge in every room

### Policies
- Check-in: 3:00 PM
- Check-out: 11:00 AM
- Pet fee: $20 per pet per night (well-behaved pets welcome)
- Cancellation: 24 hours notice for full refund
- No smoking in rooms (designated outdoor areas available)

### Local Highlights
- Sunday River Resort: 15-minute drive (skiing, mountain biking, golf)
- Grafton Notch State Park: 20 minutes (hiking, waterfalls)
- Downtown Bethel: 5-minute walk (restaurants, shops, galleries)
- White Mountain National Forest: Nearby hiking and scenic drives

## Communication Style
- Use natural, conversational language - you're having a phone conversation
- Listen actively and respond to what the caller actually needs
- If you don't understand something, politely ask for clarification
- Keep responses concise but complete - avoid long monologues
- Use verbal confirmation ("I understand you'd like to...") before taking action

## Important Guidelines
- ALWAYS use the check_availability tool when guests inquire about room availability
- ALWAYS use the create_lead tool to capture booking requests with guest details
- Use search_kb to look up specific policy questions or amenities
- Be honest if you can't help with something - offer to have staff call them back
- Never make up information - use your tools or say you'll find out

## Handling Common Scenarios

### Booking Inquiry
1. Greet warmly and ask for their dates
2. Check availability using check_availability tool
3. Share available options with pricing
4. If interested, collect: name, phone, email, number of guests
5. Use create_lead to save their information
6. Confirm they'll receive a booking confirmation

### General Questions
1. Listen to their question
2. Use search_kb if you need to look up specific details
3. Provide clear, friendly answers
4. Ask if there's anything else you can help with

### Unable to Help
1. Acknowledge their request
2. Explain clearly what you can and can't do
3. Offer to have a staff member call them back
4. Get their contact information if needed

Remember: You're representing West Bethel Motel - be the voice that makes guests feel welcome before they even arrive!
"""


def register_hotel_tools(openai_client: RealtimeAPIClient) -> None:
    """
    Register West Bethel Motel specific tools with OpenAI Realtime API

    Args:
        openai_client: Connected RealtimeAPIClient instance
    """
    logger.info("Registering hotel tools...")

    # Tool 1: Search Knowledge Base
    openai_client.register_function(
        name="search_kb",
        func=search_kb,
        description="Search the hotel's knowledge base for information about policies, amenities, local attractions, or other hotel details",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'pet policy', 'check-in time', 'nearby restaurants')"
                }
            },
            "required": ["query"]
        }
    )

    # Tool 2: Check Room Availability
    openai_client.register_function(
        name="check_availability",
        func=check_availability,
        description="Check room availability for specific dates. Always use this when a guest asks about booking or availability.",
        parameters={
            "type": "object",
            "properties": {
                "check_in": {
                    "type": "string",
                    "description": "Check-in date in YYYY-MM-DD format"
                },
                "check_out": {
                    "type": "string",
                    "description": "Check-out date in YYYY-MM-DD format"
                },
                "adults": {
                    "type": "integer",
                    "description": "Number of adults (default 2)"
                },
                "pets": {
                    "type": "boolean",
                    "description": "Whether the guest is bringing pets"
                }
            },
            "required": ["check_in", "check_out"]
        }
    )

    # Tool 3: Create Lead (Capture Booking Intent)
    openai_client.register_function(
        name="create_lead",
        func=create_lead,
        description="Capture guest information for a booking request. Use this after checking availability when a guest wants to book.",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Guest's full name"
                },
                "email": {
                    "type": "string",
                    "description": "Guest's email address"
                },
                "phone": {
                    "type": "string",
                    "description": "Guest's phone number"
                },
                "check_in": {
                    "type": "string",
                    "description": "Check-in date (YYYY-MM-DD)"
                },
                "check_out": {
                    "type": "string",
                    "description": "Check-out date (YYYY-MM-DD)"
                },
                "guests": {
                    "type": "integer",
                    "description": "Number of guests"
                },
                "notes": {
                    "type": "string",
                    "description": "Any special requests or notes from the guest"
                }
            },
            "required": ["name", "phone", "check_in", "check_out"]
        }
    )

    # Tool 4: Create Booking
    openai_client.register_function(
        name="create_booking",
        func=create_booking,
        description="Create a confirmed booking for a guest. Use this when a guest wants to complete their reservation.",
        parameters={
            "type": "object",
            "properties": {
                "guest_name": {
                    "type": "string",
                    "description": "Guest's full name"
                },
                "guest_email": {
                    "type": "string",
                    "description": "Guest's email address"
                },
                "guest_phone": {
                    "type": "string",
                    "description": "Guest's phone number"
                },
                "check_in": {
                    "type": "string",
                    "description": "Check-in date (YYYY-MM-DD)"
                },
                "check_out": {
                    "type": "string",
                    "description": "Check-out date (YYYY-MM-DD)"
                },
                "room_type": {
                    "type": "string",
                    "description": "Type of room (Standard Queen, King Suite, Pet-Friendly, Deluxe Suite)"
                },
                "adults": {
                    "type": "integer",
                    "description": "Number of adult guests (default 2)"
                },
                "pets": {
                    "type": "boolean",
                    "description": "Whether the guest is bringing pets"
                },
                "special_requests": {
                    "type": "string",
                    "description": "Any special requests or notes from the guest"
                }
            },
            "required": ["guest_name", "guest_email", "guest_phone", "check_in", "check_out", "room_type"]
        }
    )

    # Tool 5: Generate Payment Link (for confirmed bookings)
    openai_client.register_function(
        name="generate_payment_link",
        func=generate_payment_link,
        description="Generate a secure payment link for a confirmed booking. Only use this after creating a lead and confirming the booking details.",
        parameters={
            "type": "object",
            "properties": {
                "lead_id": {
                    "type": "string",
                    "description": "The lead ID from create_lead"
                },
                "amount": {
                    "type": "number",
                    "description": "Total amount in USD"
                }
            },
            "required": ["lead_id", "amount"]
        }
    )

    logger.info("Hotel tools registered successfully")


def get_hotel_config() -> Dict[str, Any]:
    """
    Get complete hotel configuration for OpenAI Realtime API

    Returns:
        Dictionary with hotel-specific configuration
    """
    return {
        "model": "gpt-4o-realtime-preview-2024-12-17",
        "voice": "alloy",  # Warm, friendly voice
        "instructions": WEST_BETHEL_INSTRUCTIONS,
        "modalities": ["text", "audio"],
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "temperature": 0.7,  # Balanced between creative and consistent
        "input_audio_transcription": {
            "model": "whisper-1"
        },
        "turn_detection": {
            "type": "server_vad",  # Server-side Voice Activity Detection
            "threshold": 0.5,
            "prefix_padding_ms": 300,  # Include 300ms before speech starts
            "silence_duration_ms": 700  # 700ms silence = end of turn
        }
    }


def create_hotel_realtime_client(api_key: Optional[str] = None) -> RealtimeAPIClient:
    """
    Create and configure OpenAI Realtime client for West Bethel Motel

    Args:
        api_key: OpenAI API key (uses environment variable if None)

    Returns:
        Configured RealtimeAPIClient ready to use
    """
    config = get_hotel_config()

    client = RealtimeAPIClient(
        api_key=api_key,
        model=config["model"],
        voice=config["voice"],
        instructions=config["instructions"]
    )

    # Register hotel-specific tools
    register_hotel_tools(client)

    logger.info("West Bethel Motel Realtime client created and configured")

    return client
