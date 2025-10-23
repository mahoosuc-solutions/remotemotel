"""
Hotel Management API Endpoints

REST API for managing rates, availability, and bookings.
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from packages.hotel.models import RoomType, BookingStatus, PaymentStatus, RateType
from packages.hotel.services import RateService, AvailabilityService, BookingService
from mcp_servers.shared.database import DatabaseManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/hotel", tags=["hotel"])

# Dependency to get database session
def get_db_session():
    db = DatabaseManager(business_module="hotel")
    db.create_tables()
    with db.get_session() as session:
        yield session


# Pydantic models for API requests/responses
class GuestInfo(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = Field(default="USA", max_length=100)


class AvailabilityRequest(BaseModel):
    check_in: date
    check_out: date
    adults: int = Field(default=2, ge=1, le=8)
    children: int = Field(default=0, ge=0, le=6)
    pets: bool = Field(default=False)
    room_type: Optional[RoomType] = None


class BookingRequest(BaseModel):
    guest: GuestInfo
    room_type: RoomType
    check_in: date
    check_out: date
    adults: int = Field(default=2, ge=1, le=8)
    children: int = Field(default=0, ge=0, le=6)
    pets: bool = Field(default=False)
    special_requests: Optional[str] = None
    source: str = Field(default="api")
    
    @field_validator('check_out')
    @classmethod
    def check_out_after_check_in(cls, v, info):
        if 'check_in' in info.data and v <= info.data['check_in']:
            raise ValueError('Check-out must be after check-in')
        return v


class RateRequest(BaseModel):
    room_type: RoomType
    rate_type: RateType
    base_rate: Decimal = Field(..., gt=0)
    effective_date: date
    end_date: date
    min_nights: int = Field(default=1, ge=1)
    max_nights: Optional[int] = Field(None, ge=1)
    
    @field_validator('end_date')
    @classmethod
    def end_date_after_effective_date(cls, v, info):
        if 'effective_date' in info.data and v <= info.data['effective_date']:
            raise ValueError('End date must be after effective date')
        return v


class AvailabilityResponse(BaseModel):
    available: bool
    check_in: str
    check_out: str
    num_nights: int
    adults: int
    pets: bool
    rooms: List[Dict[str, Any]]
    error: Optional[str] = None


class BookingResponse(BaseModel):
    confirmation_number: str
    guest_name: str
    room_type: str
    check_in: str
    check_out: str
    total_amount: float
    status: str
    created_at: str


# API Endpoints

@router.get("/availability", response_model=AvailabilityResponse)
async def check_availability(
    check_in: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    adults: int = Query(2, ge=1, le=8, description="Number of adult guests"),
    children: int = Query(0, ge=0, le=6, description="Number of child guests"),
    pets: bool = Query(False, description="Whether pets are required"),
    room_type: Optional[RoomType] = Query(None, description="Specific room type to check"),
    db: Session = Depends(get_db_session)
):
    """
    Check room availability for specific dates
    
    Returns available room types, rates, and pricing information.
    """
    try:
        availability_service = AvailabilityService(db)
        result = availability_service.check_availability(
            check_in=check_in,
            check_out=check_out,
            room_type=room_type,
            adults=adults,
            pets=pets
        )
        
        return AvailabilityResponse(**result)
        
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bookings", response_model=BookingResponse)
async def create_booking(
    booking_request: BookingRequest,
    db: Session = Depends(get_db_session)
):
    """
    Create a new hotel booking
    
    Creates a booking with guest information and room details.
    """
    try:
        booking_service = BookingService(db)
        
        # Convert guest info to dict
        guest_data = booking_request.guest.model_dump()
        
        booking = booking_service.create_booking(
            guest_data=guest_data,
            room_type=booking_request.room_type,
            check_in=booking_request.check_in,
            check_out=booking_request.check_out,
            adults=booking_request.adults,
            children=booking_request.children,
            pets=booking_request.pets,
            special_requests=booking_request.special_requests,
            source=booking_request.source
        )
        
        return BookingResponse(
            confirmation_number=booking.confirmation_number,
            guest_name=f"{booking.guest.first_name} {booking.guest.last_name}",
            room_type=booking.room.room_type.value,
            check_in=booking.check_in_date.isoformat(),
            check_out=booking.check_out_date.isoformat(),
            total_amount=float(booking.total_amount),
            status=booking.status.value,
            created_at=booking.created_at.isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings/{confirmation_number}")
async def get_booking(
    confirmation_number: str,
    db: Session = Depends(get_db_session)
):
    """
    Get booking details by confirmation number
    """
    try:
        booking_service = BookingService(db)
        booking = booking_service.get_booking(confirmation_number)
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return {
            "confirmation_number": booking.confirmation_number,
            "guest": {
                "first_name": booking.guest.first_name,
                "last_name": booking.guest.last_name,
                "email": booking.guest.email,
                "phone": booking.guest.phone
            },
            "room_type": booking.room.room_type.value,
            "check_in": booking.check_in_date.isoformat(),
            "check_out": booking.check_out_date.isoformat(),
            "adults": booking.adults,
            "children": booking.children,
            "pets": booking.pets,
            "total_amount": float(booking.total_amount),
            "status": booking.status.value,
            "payment_status": booking.payment_status.value,
            "special_requests": booking.special_requests,
            "created_at": booking.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bookings/{confirmation_number}")
async def cancel_booking(
    confirmation_number: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """
    Cancel a booking
    """
    try:
        booking_service = BookingService(db)
        success = booking_service.cancel_booking(confirmation_number, reason)
        
        if not success:
            raise HTTPException(status_code=404, detail="Booking not found or cannot be cancelled")
        
        return {"message": "Booking cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rates")
async def set_rate(
    rate_request: RateRequest,
    db: Session = Depends(get_db_session)
):
    """
    Set room rates for specific dates and room types
    """
    try:
        rate_service = RateService(db)
        
        rate = rate_service.set_rate(
            room_type=rate_request.room_type,
            rate_type=rate_request.rate_type,
            base_rate=rate_request.base_rate,
            effective_date=rate_request.effective_date,
            end_date=rate_request.end_date,
            min_nights=rate_request.min_nights,
            max_nights=rate_request.max_nights
        )
        
        return {
            "id": rate.id,
            "room_type": rate.room_type.value,
            "rate_type": rate.rate_type.value,
            "base_rate": float(rate.base_rate),
            "effective_date": rate.effective_date.isoformat(),
            "end_date": rate.end_date.isoformat(),
            "created_at": rate.created_at.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rates/{room_type}")
async def get_rates(
    room_type: RoomType,
    start_date: Optional[date] = Query(None, description="Start date for rate lookup"),
    end_date: Optional[date] = Query(None, description="End date for rate lookup"),
    db: Session = Depends(get_db_session)
):
    """
    Get rates for a specific room type
    """
    try:
        rate_service = RateService(db)
        
        # If no dates provided, get rates for next 30 days
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        # Get rates for each date in range
        rates = []
        current_date = start_date
        
        while current_date <= end_date:
            rate = rate_service.get_rate_for_date(room_type, current_date)
            rates.append({
                "date": current_date.isoformat(),
                "rate": float(rate)
            })
            current_date += timedelta(days=1)
        
        return {
            "room_type": room_type.value,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "rates": rates
        }
        
    except Exception as e:
        logger.error(f"Error getting rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AvailabilityUpdateRequest(BaseModel):
    """Request model for updating availability"""
    room_type: RoomType
    date: date
    total_inventory: int = Field(..., ge=0, description="Total inventory for this room type")
    booked_count: int = Field(default=0, ge=0, description="Number of rooms already booked")
    maintenance: bool = Field(default=False, description="Whether rooms are out for maintenance")


@router.post("/availability/update")
async def update_availability(
    request: AvailabilityUpdateRequest,
    db: Session = Depends(get_db_session)
):
    """
    Update room availability for a specific date
    """
    try:
        availability_service = AvailabilityService(db)

        availability = availability_service.update_availability(
            room_type=request.room_type,
            date=request.date,
            total_inventory=request.total_inventory,
            booked_count=request.booked_count,
            maintenance=request.maintenance
        )

        return {
            "room_type": request.room_type.value,
            "date": request.date.isoformat(),
            "total_inventory": availability.total_inventory,
            "booked_count": availability.booked_count,
            "available_count": availability.available_count,
            "maintenance": availability.maintenance,
            "updated_at": availability.updated_at.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rooms")
async def get_rooms(
    room_type: Optional[RoomType] = Query(None, description="Filter by room type"),
    active_only: bool = Query(True, description="Show only active rooms"),
    db: Session = Depends(get_db_session)
):
    """
    Get list of rooms
    """
    try:
        from packages.hotel.models import Room
        
        query = db.query(Room)
        
        if room_type:
            query = query.filter(Room.room_type == room_type)
        
        if active_only:
            query = query.filter(Room.active == True)
        
        rooms = query.all()
        
        return [
            {
                "id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type.value,
                "floor": room.floor,
                "max_occupancy": room.max_occupancy,
                "max_adults": room.max_adults,
                "max_children": room.max_children,
                "pet_friendly": room.pet_friendly,
                "smoking_allowed": room.smoking_allowed,
                "amenities": room.amenities,
                "square_footage": room.square_footage,
                "bed_configuration": room.bed_configuration,
                "description": room.description,
                "active": room.active
            }
            for room in rooms
        ]
        
    except Exception as e:
        logger.error(f"Error getting rooms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data(
    start_date: Optional[date] = Query(None, description="Start date for dashboard data"),
    end_date: Optional[date] = Query(None, description="End date for dashboard data"),
    db: Session = Depends(get_db_session)
):
    """
    Get hotel dashboard data including occupancy, revenue, and availability
    """
    try:
        from packages.hotel.models import Booking, RoomAvailability, Room
        
        # Default to next 30 days if no dates provided
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        # Get occupancy data
        bookings = db.query(Booking).filter(
            Booking.check_in_date >= start_date,
            Booking.check_in_date <= end_date,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN])
        ).all()
        
        # Calculate metrics
        total_bookings = len(bookings)
        total_revenue = sum(float(booking.total_amount) for booking in bookings)
        
        # Get availability summary
        availability_service = AvailabilityService(db)
        availability_summary = {}
        
        for room_type in RoomType:
            availability = availability_service.check_availability(
                start_date, end_date, room_type
            )
            availability_summary[room_type.value] = {
                "available": availability["available"],
                "rooms": availability.get("rooms", [])
            }
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "bookings": {
                "total": total_bookings,
                "revenue": total_revenue
            },
            "availability": availability_summary,
            "generated_at": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
