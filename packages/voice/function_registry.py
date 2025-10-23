"""
Voice Function Registry

Provides a single place to register all callable tools that the
OpenAI Realtime API can invoke during a conversation. This keeps the
Realtime configuration used by the standalone voice server, the voice
gateway, and tests perfectly aligned.
"""

from __future__ import annotations

import inspect
import logging
import os
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class FunctionSchema:
    """Metadata describing a registered function."""

    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable[..., Any]
    required_params: List[str]


class FunctionRegistry:
    """Holds callable tools that can be exposed to the Realtime API."""

    def __init__(self) -> None:
        self.functions: Dict[str, FunctionSchema] = {}
        self.logger = logging.getLogger(f"{__name__}.FunctionRegistry")

    def register(
        self,
        name: str,
        function: Callable[..., Any],
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a function with optional explicit JSON schema."""

        if parameters is None:
            parameters = self._generate_schema(function)

        schema = FunctionSchema(
            name=name,
            description=description,
            parameters=parameters,
            function=function,
            required_params=parameters.get("required", []),
        )

        self.functions[name] = schema
        self.logger.info("Registered function: %s", name)

    def _generate_schema(self, function: Callable[..., Any]) -> Dict[str, Any]:
        """Best-effort JSON schema generation from type hints."""

        signature = inspect.signature(function)
        properties: Dict[str, Any] = {}
        required: List[str] = []

        for param_name, param in signature.parameters.items():
            if param_name in {"self", "cls"}:
                continue

            json_type = "string"
            if param.annotation is int:
                json_type = "integer"
            elif param.annotation is float:
                json_type = "number"
            elif param.annotation is bool:
                json_type = "boolean"
            elif param.annotation is list:
                json_type = "array"
            elif param.annotation is dict:
                json_type = "object"

            properties[param_name] = {
                "type": json_type,
                "description": f"Parameter: {param_name}",
            }

            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        return {"type": "object", "properties": properties, "required": required}

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Return the registered functions in OpenAI tool format."""

        return [
            {
                "type": "function",
                "name": schema.name,
                "description": schema.description,
                "parameters": schema.parameters,
            }
            for schema in self.functions.values()
        ]

    async def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a function by name with the provided arguments."""

        schema = self.functions.get(name)
        if not schema:
            raise ValueError(f"Function not found: {name}")

        for param in schema.required_params:
            if param not in arguments:
                raise ValueError(f"Missing required parameter: {param}")

        if inspect.iscoroutinefunction(schema.function):
            return await schema.function(**arguments)

        result = schema.function(**arguments)
        if inspect.isawaitable(result):
            return await result

        return result

    def list_functions(self) -> List[str]:
        return list(self.functions.keys())


def create_hotel_function_registry() -> FunctionRegistry:
    """Create the canonical registry of voice tools for the hotel agent."""

    registry = FunctionRegistry()

    from packages.tools import (
        check_availability,
        create_booking,
        create_lead,
        generate_payment_link,
        search_kb,
    )
    from packages.voice.tools import (
        announce_to_session,
        format_for_voice,
        handle_ivr_menu,
        play_hold_music,
        record_voice_note,
        schedule_callback,
        send_sms_confirmation,
        transfer_to_human,
    )
    from packages.voice import workflows

    hotel_name = os.getenv("HOTEL_NAME", "StayHive Hotels")
    hotel_location = os.getenv("HOTEL_LOCATION", "West Bethel, ME")
    hotel_amenities = [
        amenity.strip()
        for amenity in os.getenv(
            "HOTEL_AMENITIES",
            "Free Wi-Fi, Complimentary Breakfast, Swimming Pool, Fitness Center",
        ).split(",")
        if amenity.strip()
    ]
    check_in_time = os.getenv("HOTEL_CHECKIN_TIME", "4:00 PM")
    check_out_time = os.getenv("HOTEL_CHECKOUT_TIME", "10:00 AM")
    pet_policy = os.getenv("HOTEL_PET_POLICY", "Pets welcome with $40 fee")

    async def check_room_availability(
        check_in: str,
        check_out: str,
        guests: int = 1,
        pets: bool = False,
    ) -> Dict[str, Any]:
        result = await check_availability.check_availability(
            check_in=check_in,
            check_out=check_out,
            adults=guests,
            pets=pets,
        )

        if isinstance(result, dict):
            if result.get("available") and result.get("rooms"):
                summaries = []
                for room in result["rooms"]:
                    room_name = room.get("type") or room.get("room_type", "room")
                    price = room.get("price_per_night") or room.get("rate", "N/A")
                    summaries.append(f"{room_name} (${price}/night)")
                if summaries:
                    result["voice_summary"] = "We have " + ", ".join(summaries) + " available."
            elif not result.get("available"):
                result["voice_summary"] = result.get(
                    "error", "We're fully booked for those dates."
                )

        return result

    def get_hotel_info(info_type: str) -> Dict[str, Any]:
        normalized = (info_type or "").strip().lower()
        response: Dict[str, Any] = {
            "requested": info_type,
            "hotel": hotel_name,
            "location": hotel_location,
        }

        if normalized in {"amenities", "amenity"}:
            response.update(
                {
                    "category": "amenities",
                    "details": hotel_amenities,
                    "voice_summary": "Our amenities include " + ", ".join(hotel_amenities),
                }
            )
        elif normalized in {"checkin", "check-in", "check in"}:
            response.update(
                {
                    "category": "check_in",
                    "check_in": check_in_time,
                    "voice_summary": f"Check-in time is {check_in_time}.",
                }
            )
        elif normalized in {"checkout", "check-out", "check out"}:
            response.update(
                {
                    "category": "check_out",
                    "check_out": check_out_time,
                    "voice_summary": f"Check-out time is {check_out_time}.",
                }
            )
        elif normalized in {"pets", "pet", "pet_policy", "pet policy"}:
            response.update(
                {
                    "category": "pet_policy",
                    "details": pet_policy,
                    "voice_summary": pet_policy,
                }
            )
        elif normalized in {"location", "directions"}:
            response.update(
                {
                    "category": "location",
                    "details": hotel_location,
                    "voice_summary": f"We're located in {hotel_location}.",
                }
            )
        else:
            response.update(
                {
                    "category": "general",
                    "details": "Ready to help with reservations, amenities, policies, and local recommendations.",
                    "voice_summary": "I'm here to help with reservations, amenities, policies, and local recommendations.",
                }
            )

        return response

    async def transfer_to_department(
        department: str,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await transfer_to_human(
            session_id=session_id,
            department=department,
            reason=reason,
        )

    registry.register(
        name="check_room_availability",
        function=check_room_availability,
        description=f"Check room availability at {hotel_name}",
        parameters={
            "type": "object",
            "properties": {
                "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                "guests": {
                    "type": "integer",
                    "description": "Number of guests staying",
                    "default": 1,
                    "minimum": 1,
                },
                "pets": {
                    "type": "boolean",
                    "description": "Whether guests are bringing pets",
                    "default": False,
                },
            },
            "required": ["check_in", "check_out"],
        },
    )

    registry.register(
        name="get_hotel_info",
        function=get_hotel_info,
        description=f"Retrieve information about {hotel_name}",
        parameters={
            "type": "object",
            "properties": {
                "info_type": {
                    "type": "string",
                    "description": "Topic to look up (amenities, checkin, checkout, pets, location, etc.)",
                }
            },
            "required": ["info_type"],
        },
    )

    registry.register(
        name="transfer_to_department",
        function=transfer_to_department,
        description="Provide contact details to transfer caller to a hotel department",
        parameters={
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "enum": ["front_desk", "housekeeping", "management", "maintenance"],
                    "description": "Department to connect",
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for transfer",
                },
                "session_id": {
                    "type": "string",
                    "description": "Session identifier (optional)",
                },
            },
            "required": ["department"],
        },
    )

    registry.register(
        name="check_availability",
        function=check_availability.check_availability,
        description="Check room availability for specific dates",
        parameters={
            "type": "object",
            "properties": {
                "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                "adults": {
                    "type": "integer",
                    "description": "Number of adult guests",
                    "default": 2,
                },
                "pets": {
                    "type": "boolean",
                    "description": "Whether the guest is bringing pets",
                    "default": False,
                },
            },
            "required": ["check_in", "check_out"],
        },
    )

    registry.register(
        name="create_lead",
        function=create_lead.create_lead,
        description="Capture guest information for follow-up",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Guest full name"},
                "phone": {"type": "string", "description": "Guest phone number"},
                "email": {"type": "string", "description": "Guest email address"},
                "check_in": {"type": "string", "description": "Desired check-in date"},
                "check_out": {"type": "string", "description": "Desired check-out date"},
                "guests": {"type": "integer", "description": "Number of guests"},
                "notes": {"type": "string", "description": "Optional notes or requests"},
            },
            "required": ["name", "phone", "check_in", "check_out"],
        },
    )

    registry.register(
        name="create_booking",
        function=create_booking.create_booking,
        description="Create a confirmed reservation for the guest",
        parameters={
            "type": "object",
            "properties": {
                "guest_name": {"type": "string", "description": "Guest full name"},
                "guest_email": {"type": "string", "description": "Guest email"},
                "guest_phone": {"type": "string", "description": "Guest phone"},
                "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                "room_type": {"type": "string", "description": "Requested room type"},
                "adults": {"type": "integer", "description": "Number of adults", "default": 2},
                "pets": {"type": "boolean", "description": "Whether pets are included", "default": False},
                "special_requests": {"type": "string", "description": "Additional requests"},
            },
            "required": [
                "guest_name",
                "guest_email",
                "guest_phone",
                "check_in",
                "check_out",
                "room_type",
            ],
        },
    )

    def _usd_to_cents(amount_usd: float) -> int:
        cents = int(
            (Decimal(str(amount_usd)) * Decimal("100")).to_integral_value(
                rounding=ROUND_HALF_UP
            )
        )
        return cents

    def generate_payment_link_from_usd(
        amount_usd: float,
        description: str,
        customer_email: Optional[str] = None,
        lead_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload_metadata = dict(metadata or {})
        if lead_id:
            payload_metadata.setdefault("lead_id", lead_id)
        amount_cents = _usd_to_cents(amount_usd)
        return generate_payment_link.generate_payment_link(
            amount_cents=amount_cents,
            description=description,
            customer_email=customer_email,
            metadata=payload_metadata or None,
        )

    registry.register(
        name="generate_payment_link",
        function=generate_payment_link_from_usd,
        description="Generate a secure payment link for a booking",
        parameters={
            "type": "object",
            "properties": {
                "lead_id": {"type": "string", "description": "Lead identifier"},
                "amount_usd": {
                    "type": "number",
                    "description": "Amount owed in USD (converted to cents internally)",
                },
                "description": {
                    "type": "string",
                    "description": "Reason for payment (e.g. deposit for reservation)",
                },
                "customer_email": {"type": "string", "description": "Customer email"},
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata passed to the payment provider",
                },
            },
            "required": ["amount_usd", "description"],
        },
    )

    registry.register(
        name="search_kb",
        function=search_kb.search_kb,
        description="Search the hotel knowledge base for policies or amenities",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5,
                    "minimum": 1,
                },
            },
            "required": ["query"],
        },
    )

    registry.register(
        name="send_sms",
        function=send_sms_confirmation,
        description="Send an SMS message to the guest",
        parameters={
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "Guest phone number"},
                "message": {"type": "string", "description": "Message to send"},
                "session_id": {
                    "type": "string",
                    "description": "Optional session identifier",
                },
            },
            "required": ["phone", "message"],
        },
    )

    registry.register(
        name="schedule_callback",
        function=schedule_callback,
        description="Schedule a callback to the guest",
        parameters={
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "Guest phone number"},
                "callback_time": {
                    "type": "string",
                    "description": "ISO timestamp for the callback",
                },
                "reason": {"type": "string", "description": "Reason for the callback"},
                "session_id": {
                    "type": "string",
                    "description": "Optional session identifier",
                },
            },
            "required": ["phone", "callback_time"],
        },
    )

    registry.register(
        name="play_hold_music",
        function=play_hold_music,
        description="Play hold music for the caller",
        parameters={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session identifier"},
                "duration_seconds": {
                    "type": "integer",
                    "description": "Duration to play music",
                    "default": 30,
                },
                "music_url": {
                    "type": "string",
                    "description": "Optional custom music URL",
                },
            },
            "required": [],
        },
    )

    registry.register(
        name="handle_ivr_menu",
        function=handle_ivr_menu,
        description="Handle IVR DTMF input",
        parameters={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session identifier"},
                "dtmf_input": {"type": "string", "description": "DTMF digit pressed"},
                "menu_level": {
                    "type": "integer",
                    "description": "Current menu level",
                    "default": 1,
                },
            },
            "required": ["dtmf_input"],
        },
    )

    registry.register(
        name="announce_to_session",
        function=announce_to_session,
        description="Speak a message to the caller via TTS",
        parameters={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session identifier"},
                "message": {"type": "string", "description": "Message to announce"},
                "voice": {
                    "type": "string",
                    "description": "Preferred TTS voice",
                    "default": "Polly.Joanna",
                },
            },
            "required": ["message"],
        },
    )

    registry.register(
        name="record_voice_note",
        function=record_voice_note,
        description="Record a voice note from the caller",
        parameters={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session identifier"},
                "max_duration_seconds": {
                    "type": "integer",
                    "description": "Maximum recording duration",
                    "default": 60,
                },
            },
            "required": [],
        },
    )

    registry.register(
        name="format_for_voice",
        function=format_for_voice,
        description="Format structured data for verbal presentation",
        parameters={
            "type": "object",
            "properties": {
                "data": {"type": "object", "description": "Payload to format"},
                "data_type": {
                    "type": "string",
                    "description": "The type of data (availability, reservation, lead, etc.)",
                    "default": "availability",
                },
            },
            "required": ["data"],
        },
    )

    registry.register(
        name="create_reservation_with_payment",
        function=workflows.create_reservation_with_payment,
        description="Create a reservation, generate a payment link, and notify the guest",
        parameters={
            "type": "object",
            "properties": {
                "guest_name": {"type": "string", "description": "Guest full name"},
                "guest_email": {"type": "string", "description": "Guest email"},
                "guest_phone": {"type": "string", "description": "Guest phone"},
                "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                "room_type": {"type": "string", "description": "Room type"},
                "adults": {"type": "integer", "description": "Number of adult guests", "default": 2},
                "pets": {"type": "boolean", "description": "Whether pets are included", "default": False},
                "special_requests": {"type": "string", "description": "Additional requests"},
                "deposit_amount_cents": {
                    "type": "integer",
                    "description": "Deposit amount in cents",
                },
                "send_sms": {"type": "boolean", "default": True, "description": "Send SMS confirmation"},
                "sms_message": {"type": "string", "description": "Custom SMS body"},
            },
            "required": [
                "guest_name",
                "guest_email",
                "guest_phone",
                "check_in",
                "check_out",
                "room_type",
            ],
        },
    )

    registry.register(
        name="schedule_guest_callback",
        function=workflows.schedule_guest_callback,
        description="Schedule a callback and optionally notify the guest via SMS",
        parameters={
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "Guest phone number"},
                "callback_time": {
                    "type": "string",
                    "description": "ISO-8601 timestamp for the callback",
                },
                "reason": {"type": "string", "description": "Reason for the callback"},
                "notify_sms": {"type": "boolean", "default": False, "description": "Send SMS notification"},
                "sms_message": {"type": "string", "description": "Custom SMS message"},
            },
            "required": ["phone", "callback_time"],
        },
    )

    registry.register(
        name="send_confirmation_notification",
        function=workflows.send_confirmation_notification,
        description="Send an SMS confirmation to the guest",
        parameters={
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "Guest phone number"},
                "message": {"type": "string", "description": "Message body"},
                "session_id": {"type": "string", "description": "Session identifier"},
            },
            "required": ["phone", "message"],
        },
    )

    logger.info("Hotel function registry created with %s functions", len(registry.functions))
    return registry
