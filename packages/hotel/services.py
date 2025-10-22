"""
Hotel Management Services

Business logic for rates, availability, and booking management.
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from packages.hotel.models import (
    Room, RoomRate, RoomAvailability, Guest, Booking, Payment, 
    RateRule, InventoryBlock, HotelSettings,
    RoomType, BookingStatus, PaymentStatus, RateType
)

logger = logging.getLogger(__name__)


class RateService:
    """Service for managing room rates and pricing"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_rate_for_date(
        self, 
        room_type: RoomType, 
        check_date: date, 
        rate_type: RateType = RateType.STANDARD
    ) -> Decimal:
        """
        Get the rate for a specific room type and date
        
        Args:
            room_type: Type of room
            check_date: Date to check rate for
            rate_type: Type of rate to apply
            
        Returns:
            Rate per night for the room type and date
        """
        try:
            # Get base rate for the room type and date
            base_rate = self.db.query(RoomRate).filter(
                and_(
                    Room.room_type == room_type,
                    Room.id == RoomRate.room_id,
                    RoomRate.rate_type == rate_type,
                    RoomRate.effective_date <= check_date,
                    RoomRate.end_date >= check_date,
                    RoomRate.active == True
                )
            ).join(Room).first()
            
            if not base_rate:
                # Fallback to standard rate
                base_rate = self.db.query(RoomRate).filter(
                    and_(
                        Room.room_type == room_type,
                        Room.id == RoomRate.room_id,
                        RoomRate.rate_type == RateType.STANDARD,
                        RoomRate.effective_date <= check_date,
                        RoomRate.end_date >= check_date,
                        RoomRate.active == True
                    )
                ).join(Room).first()
            
            if not base_rate:
                # Default rates if no rate found
                default_rates = {
                    RoomType.STANDARD_QUEEN: Decimal('120.00'),
                    RoomType.KING_SUITE: Decimal('180.00'),
                    RoomType.PET_FRIENDLY: Decimal('140.00'),
                    RoomType.DELUXE_SUITE: Decimal('220.00')
                }
                return default_rates.get(room_type, Decimal('120.00'))
            
            # Apply rate rules
            final_rate = self._apply_rate_rules(base_rate.base_rate, room_type, check_date)
            
            logger.info(f"Rate for {room_type} on {check_date}: ${final_rate}")
            return final_rate
            
        except Exception as e:
            logger.error(f"Error getting rate for {room_type} on {check_date}: {e}")
            # Return default rate
            default_rates = {
                RoomType.STANDARD_QUEEN: Decimal('120.00'),
                RoomType.KING_SUITE: Decimal('180.00'),
                RoomType.PET_FRIENDLY: Decimal('140.00'),
                RoomType.DELUXE_SUITE: Decimal('220.00')
            }
            return default_rates.get(room_type, Decimal('120.00'))
    
    def _apply_rate_rules(self, base_rate: Decimal, room_type: RoomType, check_date: date) -> Decimal:
        """Apply rate rules to base rate"""
        try:
            # Get applicable rate rules
            rules = self.db.query(RateRule).filter(
                and_(
                    RateRule.room_type == room_type,
                    RateRule.effective_date <= check_date,
                    RateRule.end_date >= check_date,
                    RateRule.active == True
                )
            ).order_by(desc(RateRule.priority)).all()
            
            final_rate = base_rate
            
            for rule in rules:
                # Apply multiplier
                if rule.multiplier:
                    final_rate = final_rate * rule.multiplier
                
                # Apply fixed adjustment
                if rule.fixed_adjustment:
                    final_rate = final_rate + rule.fixed_adjustment
                
                # Apply conditions (simplified for now)
                if rule.conditions:
                    # Check day of week conditions
                    if 'day_of_week' in rule.conditions:
                        if check_date.weekday() in rule.conditions['day_of_week']:
                            continue  # Rule applies
                        else:
                            continue  # Rule doesn't apply
                
                logger.debug(f"Applied rule {rule.name}: {base_rate} -> {final_rate}")
            
            return final_rate
            
        except Exception as e:
            logger.error(f"Error applying rate rules: {e}")
            return base_rate
    
    def set_rate(
        self, 
        room_type: RoomType, 
        rate_type: RateType, 
        base_rate: Decimal, 
        effective_date: date, 
        end_date: date,
        min_nights: int = 1,
        max_nights: Optional[int] = None
    ) -> RoomRate:
        """Set a new rate for a room type"""
        try:
            # Get a room of this type to associate the rate with
            room = self.db.query(Room).filter(Room.room_type == room_type).first()
            if not room:
                raise ValueError(f"No room found for type {room_type}")
            
            rate = RoomRate(
                room_id=room.id,
                rate_type=rate_type,
                base_rate=base_rate,
                effective_date=effective_date,
                end_date=end_date,
                min_nights=min_nights,
                max_nights=max_nights
            )
            
            self.db.add(rate)
            self.db.commit()
            
            logger.info(f"Set rate for {room_type}: ${base_rate} from {effective_date} to {end_date}")
            return rate
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting rate: {e}")
            raise


class AvailabilityService:
    """Service for managing room availability"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def check_availability(
        self, 
        check_in: date, 
        check_out: date, 
        room_type: Optional[RoomType] = None,
        adults: int = 2,
        pets: bool = False
    ) -> Dict[str, Any]:
        """
        Check room availability for a date range
        
        Args:
            check_in: Check-in date
            check_out: Check-out date
            room_type: Specific room type to check (None for all)
            adults: Number of adult guests
            pets: Whether pets are required
            
        Returns:
            Availability information including room types and pricing
        """
        try:
            num_nights = (check_out - check_in).days
            if num_nights <= 0:
                return {
                    "available": False,
                    "error": "Check-out must be after check-in"
                }
            
            # Get room types to check
            if room_type:
                room_types = [room_type]
            else:
                # Filter by pet requirement
                if pets:
                    room_types = [RoomType.PET_FRIENDLY]
                else:
                    room_types = [RoomType.STANDARD_QUEEN, RoomType.KING_SUITE, RoomType.DELUXE_SUITE]
            
            available_rooms = []
            rate_service = RateService(self.db)
            
            for rt in room_types:
                # Check if rooms are available for all dates in the range
                min_available = self._get_min_availability(rt, check_in, check_out)
                
                if min_available > 0:
                    # Get rate for the first night
                    rate_per_night = rate_service.get_rate_for_date(rt, check_in)
                    
                    # Calculate total price
                    total_price = rate_per_night * num_nights
                    
                    # Add pet fee if applicable
                    pet_fee = Decimal('20.00') if pets else Decimal('0.00')
                    if pet_fee > 0:
                        total_price += pet_fee * num_nights
                    
                    room_info = {
                        "room_type": rt.value,
                        "available": min_available,
                        "rate_per_night": float(rate_per_night),
                        "total_price": float(total_price),
                        "num_nights": num_nights,
                        "pet_fee_per_night": float(pet_fee) if pets else 0
                    }
                    
                    available_rooms.append(room_info)
            
            return {
                "available": len(available_rooms) > 0,
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "num_nights": num_nights,
                "adults": adults,
                "pets": pets,
                "rooms": available_rooms
            }
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def _get_min_availability(self, room_type: RoomType, check_in: date, check_out: date) -> int:
        """Get minimum availability for a room type across the date range"""
        try:
            min_available = float('inf')
            current_date = check_in
            
            while current_date < check_out:
                # Get availability for this date
                availability = self.db.query(RoomAvailability).filter(
                    and_(
                        RoomAvailability.room_id == Room.id,
                        Room.room_type == room_type,
                        RoomAvailability.date == current_date,
                        RoomAvailability.available == True
                    )
                ).join(Room).first()
                
                if availability:
                    min_available = min(min_available, availability.available_count)
                else:
                    # No availability record - assume default availability
                    default_availability = {
                        RoomType.STANDARD_QUEEN: 10,
                        RoomType.KING_SUITE: 5,
                        RoomType.PET_FRIENDLY: 3,
                        RoomType.DELUXE_SUITE: 2
                    }
                    min_available = min(min_available, default_availability.get(room_type, 5))
                
                current_date += timedelta(days=1)
            
            return int(min_available) if min_available != float('inf') else 0
            
        except Exception as e:
            logger.error(f"Error getting min availability for {room_type}: {e}")
            return 0
    
    def update_availability(
        self, 
        room_type: RoomType, 
        date: date, 
        total_inventory: int,
        booked_count: int = 0,
        maintenance: bool = False
    ) -> RoomAvailability:
        """Update availability for a specific room type and date"""
        try:
            # Get a room of this type
            room = self.db.query(Room).filter(Room.room_type == room_type).first()
            if not room:
                raise ValueError(f"No room found for type {room_type}")
            
            # Get or create availability record
            availability = self.db.query(RoomAvailability).filter(
                and_(
                    RoomAvailability.room_id == room.id,
                    RoomAvailability.date == date
                )
            ).first()
            
            if not availability:
                availability = RoomAvailability(
                    room_id=room.id,
                    date=date,
                    total_inventory=total_inventory,
                    booked_count=booked_count,
                    available_count=total_inventory - booked_count,
                    maintenance=maintenance
                )
                self.db.add(availability)
            else:
                availability.total_inventory = total_inventory
                availability.booked_count = booked_count
                availability.available_count = total_inventory - booked_count
                availability.maintenance = maintenance
                availability.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Updated availability for {room_type} on {date}: {availability.available_count} available")
            return availability
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating availability: {e}")
            raise


class BookingService:
    """Service for managing bookings and reservations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_booking(
        self,
        guest_data: Dict[str, Any],
        room_type: RoomType,
        check_in: date,
        check_out: date,
        adults: int = 2,
        children: int = 0,
        pets: bool = False,
        special_requests: Optional[str] = None,
        source: str = "voice_ai"
    ) -> Booking:
        """
        Create a new booking
        
        Args:
            guest_data: Guest information dictionary
            room_type: Type of room to book
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adult guests
            children: Number of child guests
            pets: Whether pets are included
            special_requests: Special requests or notes
            source: Booking source (voice_ai, website, etc.)
            
        Returns:
            Created booking object
        """
        try:
            # Validate dates
            num_nights = (check_out - check_in).days
            if num_nights <= 0:
                raise ValueError("Check-out must be after check-in")
            
            # Check availability
            availability_service = AvailabilityService(self.db)
            availability = availability_service.check_availability(
                check_in, check_out, room_type, adults, pets
            )
            
            if not availability["available"]:
                raise ValueError("No rooms available for the selected dates")
            
            # Get or create guest
            guest = self._get_or_create_guest(guest_data)
            
            # Get room
            room = self.db.query(Room).filter(Room.room_type == room_type).first()
            if not room:
                raise ValueError(f"No room found for type {room_type}")
            
            # Calculate pricing
            rate_service = RateService(self.db)
            rate_per_night = rate_service.get_rate_for_date(room_type, check_in)
            
            # Calculate total amount
            total_amount = rate_per_night * num_nights
            
            # Add pet fee if applicable
            if pets:
                pet_fee = Decimal('20.00') * num_nights
                total_amount += pet_fee
            
            # Generate confirmation number
            confirmation_number = self._generate_confirmation_number()
            
            # Create booking
            booking = Booking(
                confirmation_number=confirmation_number,
                guest_id=guest.id,
                room_id=room.id,
                check_in_date=check_in,
                check_out_date=check_out,
                adults=adults,
                children=children,
                pets=pets,
                pet_count=1 if pets else 0,
                special_requests=special_requests,
                status=BookingStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                total_amount=total_amount,
                rate_type=RateType.STANDARD,
                rate_per_night=rate_per_night,
                source=source,
                balance_due=total_amount
            )
            
            self.db.add(booking)
            self.db.commit()
            
            # Update availability
            self._update_availability_for_booking(room_type, check_in, check_out, 1)
            
            logger.info(f"Created booking {confirmation_number} for {guest.first_name} {guest.last_name}")
            return booking
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating booking: {e}")
            raise
    
    def _get_or_create_guest(self, guest_data: Dict[str, Any]) -> Guest:
        """Get existing guest or create new one"""
        try:
            # Try to find existing guest by email
            guest = self.db.query(Guest).filter(Guest.email == guest_data["email"]).first()
            
            if guest:
                # Update guest information
                guest.first_name = guest_data.get("first_name", guest.first_name)
                guest.last_name = guest_data.get("last_name", guest.last_name)
                guest.phone = guest_data.get("phone", guest.phone)
                guest.updated_at = datetime.utcnow()
            else:
                # Create new guest
                guest = Guest(
                    first_name=guest_data["first_name"],
                    last_name=guest_data["last_name"],
                    email=guest_data["email"],
                    phone=guest_data.get("phone"),
                    address=guest_data.get("address"),
                    city=guest_data.get("city"),
                    state=guest_data.get("state"),
                    postal_code=guest_data.get("postal_code"),
                    country=guest_data.get("country", "USA")
                )
                self.db.add(guest)
            
            return guest
            
        except Exception as e:
            logger.error(f"Error getting/creating guest: {e}")
            raise
    
    def _generate_confirmation_number(self) -> str:
        """Generate unique confirmation number"""
        import random
        import string
        
        # Generate 8-character alphanumeric confirmation number
        while True:
            confirmation = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Check if it's unique
            existing = self.db.query(Booking).filter(Booking.confirmation_number == confirmation).first()
            if not existing:
                return confirmation
    
    def _update_availability_for_booking(self, room_type: RoomType, check_in: date, check_out: date, rooms_booked: int):
        """Update availability when a booking is made"""
        try:
            availability_service = AvailabilityService(self.db)
            current_date = check_in
            
            while current_date < check_out:
                # Get current availability
                availability = self.db.query(RoomAvailability).filter(
                    and_(
                        RoomAvailability.room_id == Room.id,
                        Room.room_type == room_type,
                        RoomAvailability.date == current_date
                    )
                ).join(Room).first()
                
                if availability:
                    availability.booked_count += rooms_booked
                    availability.available_count = availability.total_inventory - availability.booked_count
                    availability.updated_at = datetime.utcnow()
                else:
                    # Create new availability record
                    room = self.db.query(Room).filter(Room.room_type == room_type).first()
                    if room:
                        default_inventory = {
                            RoomType.STANDARD_QUEEN: 10,
                            RoomType.KING_SUITE: 5,
                            RoomType.PET_FRIENDLY: 3,
                            RoomType.DELUXE_SUITE: 2
                        }
                        total_inventory = default_inventory.get(room_type, 5)
                        
                        availability = RoomAvailability(
                            room_id=room.id,
                            date=current_date,
                            total_inventory=total_inventory,
                            booked_count=rooms_booked,
                            available_count=total_inventory - rooms_booked
                        )
                        self.db.add(availability)
                
                current_date += timedelta(days=1)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating availability for booking: {e}")
            raise
    
    def get_booking(self, confirmation_number: str) -> Optional[Booking]:
        """Get booking by confirmation number"""
        return self.db.query(Booking).filter(Booking.confirmation_number == confirmation_number).first()
    
    def cancel_booking(self, confirmation_number: str, reason: Optional[str] = None) -> bool:
        """Cancel a booking"""
        try:
            booking = self.get_booking(confirmation_number)
            if not booking:
                return False
            
            if booking.status in [BookingStatus.CANCELLED, BookingStatus.CHECKED_OUT]:
                return False
            
            # Update booking status
            booking.status = BookingStatus.CANCELLED
            booking.cancellation_reason = reason
            booking.cancellation_date = datetime.utcnow()
            booking.updated_at = datetime.utcnow()
            
            # Update availability (release rooms)
            self._update_availability_for_booking(
                booking.room.room_type, 
                booking.check_in_date, 
                booking.check_out_date, 
                -1  # Negative to release rooms
            )
            
            self.db.commit()
            
            logger.info(f"Cancelled booking {confirmation_number}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling booking: {e}")
            return False
