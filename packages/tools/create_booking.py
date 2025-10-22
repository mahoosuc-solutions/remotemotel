"""
Booking creation for West Bethel Motel

This module provides the create_booking function used by the voice AI.
It uses the new hotel management system for booking creation.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import date

logger = logging.getLogger(__name__)

async def create_booking(
    guest_name: str,
    guest_email: str,
    guest_phone: str,
    check_in: str,
    check_out: str,
    room_type: str,
    adults: int = 2,
    pets: bool = False,
    special_requests: str = None
) -> Dict[str, Any]:
    """
    Create a new hotel booking
    
    This function uses the new hotel management system to create bookings
    with real-time availability checking and pricing.
    
    Args:
        guest_name: Guest's full name
        guest_email: Guest's email address
        guest_phone: Guest's phone number
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        room_type: Type of room to book
        adults: Number of adult guests
        pets: Whether guest has pets
        special_requests: Special requests or notes
        
    Returns:
        Booking confirmation information
    """
    try:
        from mcp_servers.shared.database import DatabaseManager
        from packages.hotel.services import BookingService
        from packages.hotel.models import RoomType
        
        logger.info(f"Creating booking for {guest_name}: {check_in} to {check_out}, {room_type}")
        
        # Initialize database and services
        db = DatabaseManager(business_module="hotel")
        db.create_tables()
        
        with db.get_session() as session:
            booking_service = BookingService(session)
            
            # Parse guest name
            name_parts = guest_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # Convert room type string to enum
            room_type_mapping = {
                "standard queen": RoomType.STANDARD_QUEEN,
                "standard_queen": RoomType.STANDARD_QUEEN,
                "queen": RoomType.STANDARD_QUEEN,
                "king suite": RoomType.KING_SUITE,
                "king_suite": RoomType.KING_SUITE,
                "king": RoomType.KING_SUITE,
                "pet friendly": RoomType.PET_FRIENDLY,
                "pet_friendly": RoomType.PET_FRIENDLY,
                "pet": RoomType.PET_FRIENDLY,
                "deluxe suite": RoomType.DELUXE_SUITE,
                "deluxe_suite": RoomType.DELUXE_SUITE,
                "deluxe": RoomType.DELUXE_SUITE
            }
            
            room_type_enum = room_type_mapping.get(room_type.lower())
            if not room_type_enum:
                return {
                    "success": False,
                    "error": f"Invalid room type: {room_type}. Available types: Standard Queen, King Suite, Pet-Friendly, Deluxe Suite"
                }
            
            # Convert string dates to date objects
            check_in_date = date.fromisoformat(check_in)
            check_out_date = date.fromisoformat(check_out)
            
            # Prepare guest data
            guest_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": guest_email,
                "phone": guest_phone
            }
            
            # Create booking
            booking = booking_service.create_booking(
                guest_data=guest_data,
                room_type=room_type_enum,
                check_in=check_in_date,
                check_out=check_out_date,
                adults=adults,
                children=0,  # Default to 0 children
                pets=pets,
                special_requests=special_requests,
                source="voice_ai"
            )
            
            # Prepare response
            result = {
                "success": True,
                "confirmation_number": booking.confirmation_number,
                "guest_name": f"{booking.guest.first_name} {booking.guest.last_name}",
                "room_type": booking.room.room_type.value.replace('_', ' ').title(),
                "check_in": booking.check_in_date.isoformat(),
                "check_out": booking.check_out_date.isoformat(),
                "adults": booking.adults,
                "pets": booking.pets,
                "total_amount": float(booking.total_amount),
                "status": booking.status.value,
                "special_requests": booking.special_requests,
                "created_at": booking.created_at.isoformat()
            }
            
            logger.info(f"Booking created successfully: {booking.confirmation_number}")
            return result
        
    except Exception as e:
        logger.error(f"Error creating booking: {e}", exc_info=True)
        
        # Return error response
        return {
            "success": False,
            "error": f"Failed to create booking: {str(e)}"
        }
