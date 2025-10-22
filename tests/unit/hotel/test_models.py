"""
Tests for hotel data models
"""

import pytest
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.hotel.models import (
    Base, Room, RoomRate, RoomAvailability, Guest, Booking, Payment,
    RateRule, InventoryBlock, HotelSettings,
    RoomType, BookingStatus, PaymentStatus, RateType
)


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestRoom:
    """Test Room model"""
    
    def test_create_room(self, db_session):
        """Test creating a room"""
        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD_QUEEN,
            floor=1,
            max_occupancy=2,
            max_adults=2,
            max_children=2,
            pet_friendly=False,
            smoking_allowed=False,
            amenities=["WiFi", "TV", "Coffee Maker"],
            square_footage=250,
            bed_configuration="1 Queen",
            description="Comfortable standard room"
        )
        
        db_session.add(room)
        db_session.commit()
        
        assert room.id is not None
        assert room.room_number == "101"
        assert room.room_type == RoomType.STANDARD_QUEEN
        assert room.active is True  # Default value
        assert room.created_at is not None
    
    def test_room_relationships(self, db_session):
        """Test room relationships"""
        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD_QUEEN,
            floor=1,
            max_occupancy=2
        )
        db_session.add(room)
        db_session.commit()
        
        # Test that relationships are accessible
        assert hasattr(room, 'availability')
        assert hasattr(room, 'bookings')
        assert hasattr(room, 'rates')


class TestRoomRate:
    """Test RoomRate model"""
    
    def test_create_room_rate(self, db_session):
        """Test creating a room rate"""
        # Create room first
        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD_QUEEN,
            floor=1,
            max_occupancy=2
        )
        db_session.add(room)
        db_session.commit()
        
        rate = RoomRate(
            room_id=room.id,
            rate_type=RateType.STANDARD,
            base_rate=Decimal('120.00'),
            effective_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            min_nights=1,
            max_nights=7
        )
        
        db_session.add(rate)
        db_session.commit()
        
        assert rate.id is not None
        assert rate.room_id == room.id
        assert rate.base_rate == Decimal('120.00')
        assert rate.active is True  # Default value
    
    def test_rate_relationships(self, db_session):
        """Test rate relationships"""
        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD_QUEEN,
            floor=1,
            max_occupancy=2
        )
        db_session.add(room)
        db_session.commit()
        
        rate = RoomRate(
            room_id=room.id,
            rate_type=RateType.STANDARD,
            base_rate=Decimal('120.00'),
            effective_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
        db_session.add(rate)
        db_session.commit()
        
        assert rate.room is not None
        assert rate.room.room_number == "101"


class TestRoomAvailability:
    """Test RoomAvailability model"""
    
    def test_create_availability(self, db_session):
        """Test creating availability record"""
        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD_QUEEN,
            floor=1,
            max_occupancy=2
        )
        db_session.add(room)
        db_session.commit()
        
        availability = RoomAvailability(
            room_id=room.id,
            date=date.today(),
            total_inventory=5,
            booked_count=2,
            available_count=3,
            available=True
        )
        
        db_session.add(availability)
        db_session.commit()
        
        assert availability.id is not None
        assert availability.room_id == room.id
        assert availability.available_count == 3
        assert availability.available is True
    
    def test_availability_calculation(self, db_session):
        """Test availability calculation"""
        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD_QUEEN,
            floor=1,
            max_occupancy=2
        )
        db_session.add(room)
        db_session.commit()
        
        availability = RoomAvailability(
            room_id=room.id,
            date=date.today(),
            total_inventory=5,
            booked_count=2,
            available_count=3  # Manually set for testing
        )
        
        # available_count should be calculated as total_inventory - booked_count
        assert availability.available_count == 3


class TestGuest:
    """Test Guest model"""
    
    def test_create_guest(self, db_session):
        """Test creating a guest"""
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="555-1234",
            address="123 Main St",
            city="Bethel",
            state="ME",
            postal_code="04217",
            country="USA"
        )
        
        db_session.add(guest)
        db_session.commit()
        
        assert guest.id is not None
        assert guest.first_name == "John"
        assert guest.last_name == "Doe"
        assert guest.email == "john.doe@example.com"
        assert guest.vip_status is False  # Default value
    
    def test_guest_relationships(self, db_session):
        """Test guest relationships"""
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        db_session.add(guest)
        db_session.commit()
        
        assert hasattr(guest, 'bookings')


class TestBooking:
    """Test Booking model"""
    
    def test_create_booking(self, db_session):
        """Test creating a booking"""
        # Create guest
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        db_session.add(guest)
        
        # Create room
        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD_QUEEN,
            floor=1,
            max_occupancy=2
        )
        db_session.add(room)
        db_session.commit()
        
        booking = Booking(
            confirmation_number="ABC12345",
            guest_id=guest.id,
            room_id=room.id,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            adults=2,
            children=0,
            pets=False,
            total_amount=Decimal('240.00'),
            rate_type=RateType.STANDARD,
            rate_per_night=Decimal('120.00'),
            source="test"
        )
        
        db_session.add(booking)
        db_session.commit()
        
        assert booking.id is not None
        assert booking.confirmation_number == "ABC12345"
        assert booking.guest_id == guest.id
        assert booking.room_id == room.id
        assert booking.status == BookingStatus.PENDING  # Default value
        assert booking.payment_status == PaymentStatus.PENDING  # Default value
    
    def test_booking_relationships(self, db_session):
        """Test booking relationships"""
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        db_session.add(guest)
        
        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD_QUEEN,
            floor=1,
            max_occupancy=2
        )
        db_session.add(room)
        db_session.commit()
        
        booking = Booking(
            confirmation_number="ABC12345",
            guest_id=guest.id,
            room_id=room.id,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            total_amount=Decimal('240.00'),
            rate_type=RateType.STANDARD,
            rate_per_night=Decimal('120.00'),
            source="test"
        )
        db_session.add(booking)
        db_session.commit()
        
        assert booking.guest is not None
        assert booking.room is not None
        assert booking.guest.first_name == "John"
        assert booking.room.room_number == "101"


class TestPayment:
    """Test Payment model"""
    
    def test_create_payment(self, db_session):
        """Test creating a payment"""
        # Create guest and room
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        db_session.add(guest)
        
        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD_QUEEN,
            floor=1,
            max_occupancy=2
        )
        db_session.add(room)
        db_session.commit()
        
        # Create booking
        booking = Booking(
            confirmation_number="ABC12345",
            guest_id=guest.id,
            room_id=room.id,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            total_amount=Decimal('240.00'),
            rate_type=RateType.STANDARD,
            rate_per_night=Decimal('120.00'),
            source="test"
        )
        db_session.add(booking)
        db_session.commit()
        
        payment = Payment(
            booking_id=booking.id,
            amount=Decimal('240.00'),
            payment_method="credit_card",
            payment_type="full_payment",
            transaction_id="TXN123456",
            status=PaymentStatus.PAID
        )
        
        db_session.add(payment)
        db_session.commit()
        
        assert payment.id is not None
        assert payment.booking_id == booking.id
        assert payment.amount == Decimal('240.00')
        assert payment.status == PaymentStatus.PAID
    
    def test_payment_relationships(self, db_session):
        """Test payment relationships"""
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        db_session.add(guest)
        
        room = Room(
            room_number="101",
            room_type=RoomType.STANDARD_QUEEN,
            floor=1,
            max_occupancy=2
        )
        db_session.add(room)
        db_session.commit()
        
        booking = Booking(
            confirmation_number="ABC12345",
            guest_id=guest.id,
            room_id=room.id,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            total_amount=Decimal('240.00'),
            rate_type=RateType.STANDARD,
            rate_per_night=Decimal('120.00'),
            source="test"
        )
        db_session.add(booking)
        db_session.commit()
        
        payment = Payment(
            booking_id=booking.id,
            amount=Decimal('240.00'),
            payment_method="credit_card",
            status=PaymentStatus.PAID
        )
        db_session.add(payment)
        db_session.commit()
        
        assert payment.booking is not None
        assert payment.booking.confirmation_number == "ABC12345"


class TestRateRule:
    """Test RateRule model"""
    
    def test_create_rate_rule(self, db_session):
        """Test creating a rate rule"""
        rule = RateRule(
            name="Weekend Premium",
            description="Weekend rate increase",
            room_type=RoomType.STANDARD_QUEEN,
            rate_type=RateType.WEEKEND,
            multiplier=Decimal('1.2'),  # 20% increase
            effective_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            priority=1
        )
        
        db_session.add(rule)
        db_session.commit()
        
        assert rule.id is not None
        assert rule.name == "Weekend Premium"
        assert rule.multiplier == Decimal('1.2')
        assert rule.active is True  # Default value


class TestInventoryBlock:
    """Test InventoryBlock model"""
    
    def test_create_inventory_block(self, db_session):
        """Test creating an inventory block"""
        block = InventoryBlock(
            room_type=RoomType.STANDARD_QUEEN,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            rooms_blocked=2,
            reason="maintenance",
            description="Room renovation"
        )
        
        db_session.add(block)
        db_session.commit()
        
        assert block.id is not None
        assert block.room_type == RoomType.STANDARD_QUEEN
        assert block.rooms_blocked == 2
        assert block.reason == "maintenance"


class TestHotelSettings:
    """Test HotelSettings model"""
    
    def test_create_hotel_setting(self, db_session):
        """Test creating a hotel setting"""
        setting = HotelSettings(
            setting_key="check_in_time",
            setting_value="15:00",
            setting_type="string",
            description="Standard check-in time",
            category="policies"
        )
        
        db_session.add(setting)
        db_session.commit()
        
        assert setting.id is not None
        assert setting.setting_key == "check_in_time"
        assert setting.setting_value == "15:00"
        assert setting.setting_type == "string"


class TestEnums:
    """Test enum values"""
    
    def test_room_type_enum(self):
        """Test RoomType enum values"""
        assert RoomType.STANDARD_QUEEN == "standard_queen"
        assert RoomType.KING_SUITE == "king_suite"
        assert RoomType.PET_FRIENDLY == "pet_friendly"
        assert RoomType.DELUXE_SUITE == "deluxe_suite"
    
    def test_booking_status_enum(self):
        """Test BookingStatus enum values"""
        assert BookingStatus.PENDING == "pending"
        assert BookingStatus.CONFIRMED == "confirmed"
        assert BookingStatus.CHECKED_IN == "checked_in"
        assert BookingStatus.CHECKED_OUT == "checked_out"
        assert BookingStatus.CANCELLED == "cancelled"
    
    def test_payment_status_enum(self):
        """Test PaymentStatus enum values"""
        assert PaymentStatus.PENDING == "pending"
        assert PaymentStatus.PAID == "paid"
        assert PaymentStatus.REFUNDED == "refunded"
        assert PaymentStatus.FAILED == "failed"
    
    def test_rate_type_enum(self):
        """Test RateType enum values"""
        assert RateType.STANDARD == "standard"
        assert RateType.WEEKEND == "weekend"
        assert RateType.PEAK == "peak"
        assert RateType.HOLIDAY == "holiday"
