"""
Hotel Admin Interface

Simple admin interface for managing rates, availability, and bookings.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from packages.hotel.models import RoomType, RateType, BookingStatus
from packages.hotel.services import RateService, AvailabilityService, BookingService
from mcp_servers.shared.database import DatabaseManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Dependency to get database session
def get_db_session():
    db = DatabaseManager(business_module="hotel")
    db.create_tables()
    with db.get_session() as session:
        yield session


# Pydantic models
class RateUpdateRequest(BaseModel):
    room_type: RoomType
    rate_type: RateType
    base_rate: Decimal = Field(..., gt=0)
    effective_date: date
    end_date: date
    min_nights: int = Field(default=1, ge=1)
    max_nights: Optional[int] = Field(None, ge=1)


class AvailabilityUpdateRequest(BaseModel):
    room_type: RoomType
    date: date
    total_inventory: int = Field(..., ge=0)
    booked_count: int = Field(default=0, ge=0)
    maintenance: bool = Field(default=False)


class BookingSearchRequest(BaseModel):
    confirmation_number: Optional[str] = None
    guest_name: Optional[str] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    status: Optional[BookingStatus] = None


# Admin Endpoints

@router.get("/dashboard")
async def get_admin_dashboard(
    start_date: Optional[date] = Query(None, description="Start date for dashboard data"),
    end_date: Optional[date] = Query(None, description="End date for dashboard data"),
    db: Session = Depends(get_db_session)
):
    """Get comprehensive admin dashboard data"""
    try:
        from packages.hotel.models import Booking, RoomAvailability, Room
        
        # Default to next 30 days if no dates provided
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        # Get booking statistics
        bookings = db.query(Booking).filter(
            Booking.check_in_date >= start_date,
            Booking.check_in_date <= end_date
        ).all()
        
        confirmed_bookings = [b for b in bookings if b.status in [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]]
        cancelled_bookings = [b for b in bookings if b.status == BookingStatus.CANCELLED]
        
        # Calculate revenue
        total_revenue = sum(float(b.total_amount) for b in confirmed_bookings)
        cancelled_revenue = sum(float(b.total_amount) for b in cancelled_bookings)
        
        # Get occupancy by room type
        occupancy_by_type = {}
        for room_type in RoomType:
            room_bookings = [b for b in confirmed_bookings if b.room.room_type == room_type]
            occupancy_by_type[room_type.value] = {
                "bookings": len(room_bookings),
                "revenue": sum(float(b.total_amount) for b in room_bookings)
            }
        
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
                "total": len(bookings),
                "confirmed": len(confirmed_bookings),
                "cancelled": len(cancelled_bookings),
                "total_revenue": total_revenue,
                "cancelled_revenue": cancelled_revenue
            },
            "occupancy_by_type": occupancy_by_type,
            "availability": availability_summary,
            "generated_at": date.today().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings")
async def search_bookings(
    confirmation_number: Optional[str] = Query(None, description="Search by confirmation number"),
    guest_name: Optional[str] = Query(None, description="Search by guest name"),
    check_in_date: Optional[date] = Query(None, description="Filter by check-in date"),
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db_session)
):
    """Search and filter bookings"""
    try:
        from packages.hotel.models import Booking
        
        query = db.query(Booking)
        
        if confirmation_number:
            query = query.filter(Booking.confirmation_number.ilike(f"%{confirmation_number}%"))
        
        if guest_name:
            query = query.join(Booking.guest).filter(
                (Booking.guest.has(first_name__ilike=f"%{guest_name}%")) |
                (Booking.guest.has(last_name__ilike=f"%{guest_name}%"))
            )
        
        if check_in_date:
            query = query.filter(Booking.check_in_date == check_in_date)
        
        if status:
            query = query.filter(Booking.status == status)
        
        bookings = query.order_by(Booking.created_at.desc()).limit(limit).all()
        
        return [
            {
                "confirmation_number": booking.confirmation_number,
                "guest_name": f"{booking.guest.first_name} {booking.guest.last_name}",
                "guest_email": booking.guest.email,
                "guest_phone": booking.guest.phone,
                "room_type": booking.room.room_type.value,
                "check_in": booking.check_in_date.isoformat(),
                "check_out": booking.check_out_date.isoformat(),
                "adults": booking.adults,
                "children": booking.children,
                "pets": booking.pets,
                "total_amount": float(booking.total_amount),
                "status": booking.status.value,
                "payment_status": booking.payment_status.value,
                "source": booking.source,
                "created_at": booking.created_at.isoformat()
            }
            for booking in bookings
        ]
        
    except Exception as e:
        logger.error(f"Error searching bookings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rates")
async def update_rate(
    rate_request: RateUpdateRequest,
    db: Session = Depends(get_db_session)
):
    """Update room rates"""
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
            "success": True,
            "rate_id": rate.id,
            "room_type": rate.room_type.value,
            "rate_type": rate.rate_type.value,
            "base_rate": float(rate.base_rate),
            "effective_date": rate.effective_date.isoformat(),
            "end_date": rate.end_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/availability")
async def update_availability(
    availability_request: AvailabilityUpdateRequest,
    db: Session = Depends(get_db_session)
):
    """Update room availability"""
    try:
        availability_service = AvailabilityService(db)
        
        availability = availability_service.update_availability(
            room_type=availability_request.room_type,
            date=availability_request.date,
            total_inventory=availability_request.total_inventory,
            booked_count=availability_request.booked_count,
            maintenance=availability_request.maintenance
        )
        
        return {
            "success": True,
            "room_type": availability_request.room_type.value,
            "date": availability_request.date.isoformat(),
            "total_inventory": availability.total_inventory,
            "booked_count": availability.booked_count,
            "available_count": availability.available_count,
            "maintenance": availability.maintenance
        }
        
    except Exception as e:
        logger.error(f"Error updating availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rates/summary")
async def get_rates_summary(
    room_type: Optional[RoomType] = Query(None, description="Filter by room type"),
    start_date: Optional[date] = Query(None, description="Start date for rate lookup"),
    end_date: Optional[date] = Query(None, description="End date for rate lookup"),
    db: Session = Depends(get_db_session)
):
    """Get rates summary for all room types or specific room type"""
    try:
        rate_service = RateService(db)
        
        # Default to next 30 days if no dates provided
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        room_types = [room_type] if room_type else list(RoomType)
        rates_summary = {}
        
        for rt in room_types:
            # Get rates for each date in range
            rates = []
            current_date = start_date
            
            while current_date <= end_date:
                rate = rate_service.get_rate_for_date(rt, current_date)
                rates.append({
                    "date": current_date.isoformat(),
                    "rate": float(rate)
                })
                current_date += timedelta(days=1)
            
            rates_summary[rt.value] = {
                "room_type": rt.value,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "rates": rates
            }
        
        return rates_summary
        
    except Exception as e:
        logger.error(f"Error getting rates summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bookings/{confirmation_number}/cancel")
async def cancel_booking_admin(
    confirmation_number: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """Cancel a booking (admin function)"""
    try:
        booking_service = BookingService(db)
        success = booking_service.cancel_booking(confirmation_number, reason)
        
        if not success:
            raise HTTPException(status_code=404, detail="Booking not found or cannot be cancelled")
        
        return {
            "success": True,
            "message": f"Booking {confirmation_number} cancelled successfully",
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rooms")
async def get_rooms_admin(
    room_type: Optional[RoomType] = Query(None, description="Filter by room type"),
    active_only: bool = Query(True, description="Show only active rooms"),
    db: Session = Depends(get_db_session)
):
    """Get detailed room information for admin"""
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
                "active": room.active,
                "created_at": room.created_at.isoformat()
            }
            for room in rooms
        ]
        
    except Exception as e:
        logger.error(f"Error getting rooms: {e}")
        raise HTTPException(status_code=500, detail=str(e))
