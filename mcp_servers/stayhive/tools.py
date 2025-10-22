"""MCP Tools for StayHive Hospitality Module"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from mcp_servers.shared.database import DatabaseManager, Base
from mcp_servers.shared.cloud_sync import CloudSyncManager
from sqlalchemy import Column, Integer, String, Date, Boolean, Float, DateTime, Text
import uuid


# Database Models
class RoomInventory(Base):
    """Track room availability by date"""
    __tablename__ = "room_inventory"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    standard_queen_available = Column(Integer, default=10)
    king_suite_available = Column(Integer, default=5)
    pet_friendly_available = Column(Integer, default=3)


class Reservation(Base):
    """Guest reservations"""
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(String, unique=True, index=True)
    guest_name = Column(String)
    guest_email = Column(String, index=True)
    guest_phone = Column(String)
    check_in = Column(Date, index=True)
    check_out = Column(Date, index=True)
    room_type = Column(String)
    adults = Column(Integer)
    pets = Column(Boolean, default=False)
    status = Column(String, default="pending")  # pending, confirmed, cancelled, completed
    total_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Lead(Base):
    """Guest leads and inquiries"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(String, unique=True, index=True)
    full_name = Column(String)
    channel = Column(String)  # web, phone, email, chat
    email = Column(String, index=True)
    phone = Column(String)
    interest = Column(Text)
    status = Column(String, default="new")  # new, contacted, qualified, converted, lost
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# MCP Tool Functions
def _compute_availability(
    check_in: str,
    check_out: str,
    adults: int = 2,
    pets: bool = False
) -> Dict[str, Any]:
    """
    Check room availability for given dates

    Args:
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        adults: Number of adult guests
        pets: Whether guest has pets

    Returns:
        Availability information including room types and pricing
    """
    db = DatabaseManager(business_module="stayhive")
    db.create_tables()

    try:
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)
        num_nights = (check_out_date - check_in_date).days

        if num_nights <= 0:
            return {
                "available": False,
                "error": "Check-out must be after check-in"
            }

        # Query inventory for date range
        with db.get_session() as session:
            current_date = check_in_date
            min_standard = float('inf')
            min_king = float('inf')
            min_pet = float('inf')

            while current_date < check_out_date:
                inventory = session.query(RoomInventory).filter(
                    RoomInventory.date == current_date
                ).first()

                if inventory:
                    min_standard = min(min_standard, inventory.standard_queen_available)
                    min_king = min(min_king, inventory.king_suite_available)
                    min_pet = min(min_pet, inventory.pet_friendly_available)
                else:
                    # No inventory record = assume default availability
                    min_standard = min(min_standard, 10)
                    min_king = min(min_king, 5)
                    min_pet = min(min_pet, 3)

                current_date += timedelta(days=1)

        # Build response
        available_rooms = []

        if pets:
            if min_pet > 0:
                available_rooms.append({
                    "type": "Pet-Friendly Room",
                    "available": int(min_pet),
                    "price_per_night": 140,
                    "pet_fee_per_night": 20,
                    "total_price": (140 + 20) * num_nights
                })
        else:
            if min_standard > 0:
                available_rooms.append({
                    "type": "Standard Queen",
                    "available": int(min_standard),
                    "price_per_night": 120,
                    "total_price": 120 * num_nights
                })
            if min_king > 0:
                available_rooms.append({
                    "type": "King Suite",
                    "available": int(min_king),
                    "price_per_night": 180,
                    "total_price": 180 * num_nights
                })

        return {
            "available": len(available_rooms) > 0,
            "check_in": check_in,
            "check_out": check_out,
            "num_nights": num_nights,
            "adults": adults,
            "pets": pets,
            "rooms": available_rooms
        }

    except ValueError as e:
        return {
            "available": False,
            "error": f"Invalid date format: {str(e)}"
        }


async def check_availability(
    check_in: str,
    check_out: str,
    adults: int = 2,
    pets: bool = False
) -> Dict[str, Any]:
    """Async façade maintained for MCP tool compatibility."""
    return _compute_availability(check_in, check_out, adults, pets)


def check_availability_sync(
    check_in: str,
    check_out: str,
    adults: int = 2,
    pets: bool = False
) -> Dict[str, Any]:
    """Synchronous variant for REST API threads."""
    return _compute_availability(check_in, check_out, adults, pets)


async def create_reservation(
    guest_name: str,
    guest_email: str,
    guest_phone: str,
    check_in: str,
    check_out: str,
    room_type: str,
    adults: int = 2,
    pets: bool = False
) -> Dict[str, Any]:
    """
    Create a new reservation

    Args:
        guest_name: Full name of guest
        guest_email: Guest email
        guest_phone: Guest phone number
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        room_type: Type of room (Standard Queen, King Suite, Pet-Friendly Room)
        adults: Number of adults
        pets: Whether guest has pets

    Returns:
        Reservation confirmation with reservation ID
    """
    db = DatabaseManager(business_module="stayhive")
    cloud_sync = CloudSyncManager(business_module="stayhive")

    try:
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)
        num_nights = (check_out_date - check_in_date).days

        # Calculate pricing
        pricing = {
            "Standard Queen": 120,
            "King Suite": 180,
            "Pet-Friendly Room": 140
        }
        price_per_night = pricing.get(room_type, 120)
        total_price = price_per_night * num_nights

        if pets and room_type == "Pet-Friendly Room":
            total_price += 20 * num_nights

        # Generate reservation ID
        reservation_id = f"RSV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        with db.get_session() as session:
            reservation = Reservation(
                reservation_id=reservation_id,
                guest_name=guest_name,
                guest_email=guest_email,
                guest_phone=guest_phone,
                check_in=check_in_date,
                check_out=check_out_date,
                room_type=room_type,
                adults=adults,
                pets=pets,
                status="pending",
                total_price=total_price
            )

            session.add(reservation)

        # Sync to cloud if enabled
        await cloud_sync.sync_reservation({
            "reservation_id": reservation_id,
            "guest_name": guest_name,
            "guest_email": guest_email,
            "check_in": check_in,
            "check_out": check_out,
            "room_type": room_type,
            "total_price": total_price
        })

        await cloud_sync.close()

        return {
            "success": True,
            "reservation_id": reservation_id,
            "guest_name": guest_name,
            "check_in": check_in,
            "check_out": check_out,
            "room_type": room_type,
            "num_nights": num_nights,
            "total_price": total_price,
            "status": "pending",
            "message": "Reservation created successfully. You will receive a confirmation email shortly."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create reservation. Please try again."
        }


async def create_lead(
    full_name: str,
    email: str,
    phone: str,
    channel: str = "chat",
    interest: str = ""
) -> Dict[str, Any]:
    """
    Create a guest lead for follow-up

    Args:
        full_name: Guest's full name
        email: Guest email
        phone: Guest phone number
        channel: How they contacted us (chat, phone, email, web)
        interest: What they're interested in (booking dates, questions, etc.)

    Returns:
        Lead confirmation with lead ID
    """
    db = DatabaseManager(business_module="stayhive")
    cloud_sync = CloudSyncManager(business_module="stayhive")

    try:
        # Generate lead ID
        lead_id = f"LD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        with db.get_session() as session:
            lead = Lead(
                lead_id=lead_id,
                full_name=full_name,
                channel=channel,
                email=email,
                phone=phone,
                interest=interest,
                status="new"
            )

            session.add(lead)

        # Sync to cloud if enabled
        await cloud_sync.sync_lead({
            "lead_id": lead_id,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "channel": channel,
            "interest": interest
        })

        await cloud_sync.close()

        return {
            "success": True,
            "lead_id": lead_id,
            "message": f"Thank you, {full_name}! We've saved your information and will follow up shortly."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to save your information. Please try again."
        }


async def generate_payment_link(
    amount_cents: int,
    description: str,
    reservation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a payment link (Stripe integration placeholder)

    Args:
        amount_cents: Amount in cents (e.g., 20000 = $200.00)
        description: Payment description
        reservation_id: Optional reservation ID

    Returns:
        Payment link information
    """
    # TODO: Integrate with actual Stripe API
    # For now, return a mock response

    payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"

    return {
        "success": True,
        "payment_id": payment_id,
        "url": f"https://pay.stayhive.ai/{payment_id}",
        "amount_cents": amount_cents,
        "amount_dollars": amount_cents / 100,
        "description": description,
        "reservation_id": reservation_id,
        "expires_in_hours": 24,
        "message": "Payment link generated successfully. Link expires in 24 hours."
    }
