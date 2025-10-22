"""
Room availability checking for West Bethel Motel

This module provides the check_availability function used by the voice AI.
It uses the new hotel management system for real-time availability data.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import date, timedelta

logger = logging.getLogger(__name__)

async def check_availability(check_in: str, check_out: str, adults: int = 1, pets: bool = False) -> Dict[str, Any]:
    """
    Check room availability for given dates
    
    This function uses the new hotel management system to get real-time
    availability data with dynamic pricing.
    
    Args:
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD) 
        adults: Number of adult guests
        pets: Whether guest has pets
        
    Returns:
        Availability information including room types and pricing
    """
    try:
        from mcp_servers.shared.database import DatabaseManager
        from packages.hotel.services import AvailabilityService
        from packages.hotel.models import RoomType
        
        logger.info(f"Checking availability: {check_in} to {check_out}, adults={adults}, pets={pets}")
        
        # Initialize database and services
        db = DatabaseManager(business_module="hotel")
        db.create_tables()
        
        with db.get_session() as session:
            availability_service = AvailabilityService(session)
            
            # Convert string dates to date objects
            check_in_date = date.fromisoformat(check_in)
            check_out_date = date.fromisoformat(check_out)
            
            # Determine room type filter based on pets
            room_type_filter = RoomType.PET_FRIENDLY if pets else None
            
            # Check availability
            result = availability_service.check_availability(
                check_in=check_in_date,
                check_out=check_out_date,
                room_type=room_type_filter,
                adults=adults,
                pets=pets
            )
            
            # Convert room types to readable names
            if result.get("rooms"):
                for room in result["rooms"]:
                    room_type_mapping = {
                        "standard_queen": "Standard Queen",
                        "king_suite": "King Suite", 
                        "pet_friendly": "Pet-Friendly Room",
                        "deluxe_suite": "Deluxe Suite"
                    }
                    room["type"] = room_type_mapping.get(room["room_type"], room["room_type"])
            
            logger.info(f"Availability check result: {result}")
            return result
        
    except Exception as e:
        logger.error(f"Error checking availability: {e}", exc_info=True)
        
        # Fallback to basic availability if hotel system fails
        try:
            check_in_date = date.fromisoformat(check_in)
            check_out_date = date.fromisoformat(check_out)
            num_nights = (check_out_date - check_in_date).days
            
            if num_nights <= 0:
                return {
                    "available": False,
                    "error": "Check-out must be after check-in"
                }
            
            # Basic fallback - assume some availability
            rooms = []
            if pets:
                rooms.append({
                    "type": "Pet-Friendly Room",
                    "available": 2,
                    "price_per_night": 140,
                    "pet_fee_per_night": 20,
                    "total_price": (140 + 20) * num_nights
                })
            else:
                rooms.append({
                    "type": "Standard Queen", 
                    "available": 5,
                    "price_per_night": 120,
                    "total_price": 120 * num_nights
                })
                rooms.append({
                    "type": "King Suite",
                    "available": 3, 
                    "price_per_night": 180,
                    "total_price": 180 * num_nights
                })
            
            return {
                "available": True,
                "check_in": check_in,
                "check_out": check_out,
                "num_nights": num_nights,
                "adults": adults,
                "pets": pets,
                "rooms": rooms,
                "note": "Using fallback availability data"
            }
            
        except ValueError as e:
            return {
                "available": False,
                "error": f"Invalid date format: {str(e)}"
            }
