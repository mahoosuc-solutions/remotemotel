"""
Conversation Manager for Realtime API

Manages natural conversation flow, context injection, and turn coordination.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for a conversation"""
    hotel_name: str = "Our Hotel"
    hotel_location: str = "Downtown"
    check_in_time: str = "3:00 PM"
    check_out_time: str = "11:00 AM"
    pet_policy: str = "Pets welcome with $50 fee"
    amenities: List[str] = field(default_factory=lambda: [
        "Free WiFi",
        "Complimentary breakfast",
        "Fitness center",
        "Swimming pool"
    ])
    room_types: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"name": "Standard Queen", "price": 129, "occupancy": 2},
        {"name": "Deluxe King", "price": 159, "occupancy": 2},
        {"name": "Suite", "price": 249, "occupancy": 4}
    ])
    policies: Dict[str, str] = field(default_factory=lambda: {
        "cancellation": "Free cancellation up to 24 hours before check-in",
        "payment": "Credit card required at booking, charged at check-in",
        "children": "Children under 12 stay free with parents"
    })


class ConversationManager:
    """
    Manages conversation flow and context

    Handles:
    - System instructions generation
    - Context injection
    - Conversation state tracking
    - Response formatting
    """

    def __init__(self, context: Optional[ConversationContext] = None):
        """
        Initialize conversation manager

        Args:
            context: Hotel context for conversations
        """
        self.context = context or ConversationContext()
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_topic: Optional[str] = None
        self.guest_info: Dict[str, Any] = {}

        self.logger = logging.getLogger(f"{__name__}.ConversationManager")

    def generate_system_instructions(self) -> str:
        """
        Generate system instructions for Realtime API

        Returns:
            System instructions string
        """
        instructions = f"""You are a friendly and professional AI concierge for {self.context.hotel_name}, located in {self.context.hotel_location}.

Your role is to assist guests with:
- Checking room availability
- Making reservations
- Answering questions about the hotel
- Providing local recommendations
- Handling special requests

Key Information:
- Check-in time: {self.context.check_in_time}
- Check-out time: {self.context.check_out_time}
- Pet policy: {self.context.pet_policy}

Amenities:
{self._format_amenities()}

Room Types:
{self._format_room_types()}

Policies:
{self._format_policies()}

Guidelines:
1. Be warm, welcoming, and conversational
2. Use natural language, not robotic responses
3. Ask clarifying questions when needed
4. Offer suggestions and alternatives
5. Use available functions to check availability, create leads, etc.
6. Transfer to human staff for complex issues
7. Confirm important details (dates, names, phone numbers)
8. End calls professionally and invite guests to call back

Remember: You're representing {self.context.hotel_name}. Provide excellent service and make guests feel valued!
"""

        return instructions

    def _format_amenities(self) -> str:
        """Format amenities list"""
        return "\n".join(f"- {amenity}" for amenity in self.context.amenities)

    def _format_room_types(self) -> str:
        """Format room types"""
        lines = []
        for room in self.context.room_types:
            lines.append(f"- {room['name']}: ${room['price']}/night (sleeps {room['occupancy']})")
        return "\n".join(lines)

    def _format_policies(self) -> str:
        """Format policies"""
        lines = []
        for key, value in self.context.policies.items():
            lines.append(f"- {key.title()}: {value}")
        return "\n".join(lines)

    def add_turn(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a conversation turn

        Args:
            role: Speaker role ('user', 'assistant', 'system')
            content: Turn content
            metadata: Additional metadata
        """
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        self.conversation_history.append(turn)
        self.logger.debug(f"Added turn: {role} - {content[:50]}...")

    def update_guest_info(self, info: Dict[str, Any]) -> None:
        """
        Update guest information

        Args:
            info: Guest information to add/update
        """
        self.guest_info.update(info)
        self.logger.info(f"Updated guest info: {list(info.keys())}")

    def get_conversation_summary(self) -> str:
        """
        Get a summary of the conversation

        Returns:
            Conversation summary
        """
        if not self.conversation_history:
            return "No conversation yet"

        summary_parts = []

        # Count turns
        user_turns = sum(1 for turn in self.conversation_history if turn["role"] == "user")
        assistant_turns = sum(1 for turn in self.conversation_history if turn["role"] == "assistant")

        summary_parts.append(f"Conversation turns: {user_turns} from guest, {assistant_turns} from assistant")

        # Current topic
        if self.current_topic:
            summary_parts.append(f"Current topic: {self.current_topic}")

        # Guest info
        if self.guest_info:
            info_str = ", ".join(f"{k}: {v}" for k, v in self.guest_info.items())
            summary_parts.append(f"Guest info: {info_str}")

        return "\n".join(summary_parts)

    def extract_dates_from_text(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract dates from user text (basic implementation)

        Args:
            text: User text

        Returns:
            Dict with check_in and check_out dates
        """
        # This is a simplified implementation
        # Production would use NLP/date parsing libraries

        dates = {"check_in": None, "check_out": None}

        # Look for date patterns (very basic)
        import re

        # Pattern: "January 15" or "Jan 15" or "1/15"
        date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}\b'
        matches = re.findall(date_pattern, text, re.IGNORECASE)

        if len(matches) >= 1:
            dates["check_in"] = matches[0]
        if len(matches) >= 2:
            dates["check_out"] = matches[1]

        return dates

    def extract_guest_count(self, text: str) -> Optional[int]:
        """
        Extract guest count from text

        Args:
            text: User text

        Returns:
            Number of guests or None
        """
        import re

        # Look for patterns like "2 people", "for 3", "3 adults"
        patterns = [
            r'(\d+)\s+(?:people|guests|adults)',
            r'for\s+(\d+)',
            r'(\d+)\s+of us'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def should_transfer_to_human(self, text: str) -> bool:
        """
        Determine if conversation should be transferred to human

        Args:
            text: User text or conversation state

        Returns:
            True if should transfer
        """
        # Transfer keywords
        transfer_keywords = [
            "speak to a person",
            "talk to someone",
            "human agent",
            "manager",
            "complaint",
            "problem",
            "not happy",
            "dissatisfied"
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in transfer_keywords)

    def get_suggested_response(self, user_text: str) -> Optional[str]:
        """
        Get suggested response based on user text

        This provides fallback responses if Realtime API is unavailable

        Args:
            user_text: User's text

        Returns:
            Suggested response or None
        """
        text_lower = user_text.lower()

        # Greetings
        if any(word in text_lower for word in ["hello", "hi", "hey", "good morning", "good evening"]):
            return f"Hello! Welcome to {self.context.hotel_name}. How may I assist you today?"

        # Availability inquiry
        if "available" in text_lower or "vacancy" in text_lower:
            return "I'd be happy to check availability for you. What dates are you interested in?"

        # Pricing
        if "price" in text_lower or "cost" in text_lower or "rate" in text_lower:
            return f"Our rooms start at ${self.context.room_types[0]['price']} per night. Would you like to hear about our different room types?"

        # Amenities
        if "amenities" in text_lower or "facilities" in text_lower:
            return f"We offer {', '.join(self.context.amenities[:3])}, and more! Would you like the full list?"

        # Pet policy
        if "pet" in text_lower or "dog" in text_lower or "cat" in text_lower:
            return f"{self.context.pet_policy}. We love our furry guests!"

        # Check-in/out times
        if "check in" in text_lower or "check out" in text_lower:
            return f"Check-in is at {self.context.check_in_time} and check-out is at {self.context.check_out_time}."

        return None


def create_hotel_conversation_manager(
    hotel_name: str = "Our Hotel",
    location: str = "Downtown"
) -> ConversationManager:
    """
    Create a conversation manager with hotel context

    Args:
        hotel_name: Hotel name
        location: Hotel location

    Returns:
        ConversationManager instance
    """
    context = ConversationContext(
        hotel_name=hotel_name,
        hotel_location=location
    )

    return ConversationManager(context)
