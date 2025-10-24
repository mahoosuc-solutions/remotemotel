"""
Hotel Management Data Models

Comprehensive data models for rates, availability, bookings, and hotel operations.
"""

from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Time, Boolean, 
    Text, ForeignKey, Numeric, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy import JSON
import json

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class RoomType(str, Enum):
    """Room type enumeration"""
    STANDARD_QUEEN = "standard_queen"
    KING_SUITE = "king_suite"
    PET_FRIENDLY = "pet_friendly"
    DELUXE_SUITE = "deluxe_suite"


class BookingStatus(str, Enum):
    """Booking status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class RateType(str, Enum):
    """Rate type enumeration"""
    STANDARD = "standard"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"
    PEAK = "peak"
    OFF_PEAK = "off_peak"
    GROUP = "group"
    CORPORATE = "corporate"
    LAST_MINUTE = "last_minute"


class LeadStatus(str, Enum):
    """Lead status enumeration"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class Room(Base):
    """Room definition and configuration"""
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type = Column(SQLEnum(RoomType), nullable=False)
    floor = Column(Integer, nullable=False)
    max_occupancy = Column(Integer, nullable=False, default=2)
    max_adults = Column(Integer, nullable=False, default=2)
    max_children = Column(Integer, nullable=False, default=2)
    pet_friendly = Column(Boolean, default=False)
    smoking_allowed = Column(Boolean, default=False)
    amenities = Column(JSON, default=list)  # List of amenity strings
    square_footage = Column(Integer)
    bed_configuration = Column(String(100))  # e.g., "1 Queen", "1 King + Sofa"
    description = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    availability = relationship("RoomAvailability", back_populates="room")
    bookings = relationship("Booking", back_populates="room")
    rates = relationship("RoomRate", back_populates="room")
    
    def __repr__(self):
        return f"<Room(room_number='{self.room_number}', type='{self.room_type}')>"


class RoomRate(Base):
    """Dynamic room rates and pricing"""
    __tablename__ = "room_rates"
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    rate_type = Column(SQLEnum(RateType), nullable=False)
    base_rate = Column(Numeric(10, 2), nullable=False)  # Base rate per night
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    min_nights = Column(Integer, default=1)
    max_nights = Column(Integer)
    advance_booking_days = Column(Integer)  # How many days in advance required
    cancellation_hours = Column(Integer, default=24)  # Hours before check-in for free cancellation
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    room = relationship("Room", back_populates="rates")
    
    # Indexes
    __table_args__ = (
        Index('idx_room_rate_dates', 'room_id', 'effective_date', 'end_date'),
        Index('idx_room_rate_type', 'rate_type', 'effective_date'),
    )
    
    def __repr__(self):
        return f"<RoomRate(room_id={self.room_id}, type='{self.rate_type}', rate={self.base_rate})>"


class RoomAvailability(Base):
    """Daily room availability tracking"""
    __tablename__ = "room_availability"
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    date = Column(Date, nullable=False)
    available = Column(Boolean, default=True)
    total_inventory = Column(Integer, default=1)  # Total rooms of this type
    booked_count = Column(Integer, default=0)  # Number of rooms booked
    available_count = Column(Integer, default=1)  # Calculated: total_inventory - booked_count
    maintenance = Column(Boolean, default=False)  # Room out of service
    overbooked = Column(Boolean, default=False)  # Allow overbooking
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    room = relationship("Room", back_populates="availability")
    
    # Indexes
    __table_args__ = (
        Index('idx_availability_date', 'date', 'available'),
        Index('idx_availability_room_date', 'room_id', 'date'),
    )
    
    def __repr__(self):
        return f"<RoomAvailability(room_id={self.room_id}, date={self.date}, available={self.available_count})>"


class Guest(Base):
    """Guest information and preferences"""
    __tablename__ = "guests"
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(100), default="USA")
    date_of_birth = Column(Date)
    preferences = Column(JSON, default=dict)  # Guest preferences
    loyalty_tier = Column(String(50))  # Gold, Silver, etc.
    loyalty_points = Column(Integer, default=0)
    vip_status = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = relationship("Booking", back_populates="guest")
    
    def __repr__(self):
        return f"<Guest(name='{self.first_name} {self.last_name}', email='{self.email}')>"


class Booking(Base):
    """Hotel booking/reservation"""
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True)
    confirmation_number = Column(String(20), unique=True, nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    check_in_time = Column(Time, default=time(15, 0))  # 3:00 PM default
    check_out_time = Column(Time, default=time(11, 0))  # 11:00 AM default
    adults = Column(Integer, nullable=False, default=2)
    children = Column(Integer, default=0)
    infants = Column(Integer, default=0)
    pets = Column(Boolean, default=False)
    pet_count = Column(Integer, default=0)
    special_requests = Column(Text)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    total_amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    fees_amount = Column(Numeric(10, 2), default=0)  # Resort fees, pet fees, etc.
    discount_amount = Column(Numeric(10, 2), default=0)
    paid_amount = Column(Numeric(10, 2), default=0)
    balance_due = Column(Numeric(10, 2), default=0)
    rate_type = Column(SQLEnum(RateType), nullable=False)
    rate_per_night = Column(Numeric(10, 2), nullable=False)
    source = Column(String(100))  # Website, phone, walk-in, OTA, etc.
    source_reference = Column(String(100))  # Booking.com confirmation, etc.
    cancellation_reason = Column(Text)
    cancellation_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    guest = relationship("Guest", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking")
    
    # Indexes
    __table_args__ = (
        Index('idx_booking_dates', 'check_in_date', 'check_out_date'),
        Index('idx_booking_status', 'status', 'payment_status'),
        Index('idx_booking_guest', 'guest_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Booking(confirmation='{self.confirmation_number}', guest_id={self.guest_id}, dates='{self.check_in_date} to {self.check_out_date}')>"


class Payment(Base):
    """Payment tracking for bookings"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # credit_card, cash, check, etc.
    payment_type = Column(String(50))  # deposit, full_payment, refund, etc.
    transaction_id = Column(String(100))  # External payment processor ID
    status = Column(SQLEnum(PaymentStatus), nullable=False)
    processed_at = Column(DateTime)
    refunded_at = Column(DateTime)
    refund_amount = Column(Numeric(10, 2), default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    booking = relationship("Booking", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(booking_id={self.booking_id}, amount={self.amount}, method='{self.payment_method}')>"


class RateRule(Base):
    """Dynamic pricing rules and conditions"""
    __tablename__ = "rate_rules"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    room_type = Column(SQLEnum(RoomType), nullable=False)
    rate_type = Column(SQLEnum(RateType), nullable=False)
    multiplier = Column(Numeric(5, 4), nullable=False)  # 1.0 = 100%, 1.2 = 120%
    fixed_adjustment = Column(Numeric(10, 2), default=0)  # Fixed dollar adjustment
    conditions = Column(JSON, default=dict)  # Complex conditions (day of week, season, etc.)
    priority = Column(Integer, default=0)  # Higher priority rules override lower ones
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_rate_rule_priority', 'priority', 'active'),
        Index('idx_rate_rule_dates', 'effective_date', 'end_date'),
    )
    
    def __repr__(self):
        return f"<RateRule(name='{self.name}', room_type='{self.room_type}', multiplier={self.multiplier})>"


class InventoryBlock(Base):
    """Inventory blocks for maintenance, group bookings, etc."""
    __tablename__ = "inventory_blocks"
    
    id = Column(Integer, primary_key=True)
    room_type = Column(SQLEnum(RoomType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    rooms_blocked = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=False)  # maintenance, group_booking, etc.
    description = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_inventory_block_dates', 'start_date', 'end_date'),
        Index('idx_inventory_block_room_type', 'room_type', 'start_date'),
    )
    
    def __repr__(self):
        return f"<InventoryBlock(room_type='{self.room_type}', dates='{self.start_date} to {self.end_date}', rooms={self.rooms_blocked})>"


class HotelSettings(Base):
    """Hotel configuration and settings"""
    __tablename__ = "hotel_settings"

    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text, nullable=False)
    setting_type = Column(String(50), default="string")  # string, number, boolean, json
    description = Column(Text)
    category = Column(String(50))  # pricing, policies, features, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<HotelSettings(key='{self.setting_key}', value='{self.setting_value}')>"


class Lead(Base):
    """Lead/inquiry model for potential guests"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    check_in_date = Column(String(50))
    check_out_date = Column(String(50))
    adults = Column(Integer, default=2)
    source = Column(String(50), default="web")
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Lead(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}')>"
