"""
Integration tests for the complete hotel management system
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.hotel.models import Base, Room, RoomRate, RoomAvailability, Guest, Booking
from packages.hotel.services import RateService, AvailabilityService, BookingService
from packages.hotel.models import RoomType, RateType, BookingStatus, PaymentStatus


@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_room(test_db):
    """Create sample room for testing"""
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
    test_db.add(room)
    test_db.commit()
    return room


@pytest.fixture
def sample_rates(test_db, sample_room):
    """Create sample rates for testing"""
    rates = [
        RoomRate(
            room_id=sample_room.id,
            rate_type=RateType.STANDARD,
            base_rate=Decimal('120.00'),
            effective_date=date.today(),
            end_date=date.today() + timedelta(days=365)
        ),
        RoomRate(
            room_id=sample_room.id,
            rate_type=RateType.WEEKEND,
            base_rate=Decimal('140.00'),
            effective_date=date.today(),
            end_date=date.today() + timedelta(days=365)
        )
    ]
    for rate in rates:
        test_db.add(rate)
    test_db.commit()
    return rates


@pytest.fixture
def sample_availability(test_db, sample_room):
    """Create sample availability for testing"""
    availability = RoomAvailability(
        room_id=sample_room.id,
        date=date.today(),
        total_inventory=5,
        booked_count=2,
        available_count=3,
        available=True
    )
    test_db.add(availability)
    test_db.commit()
    return availability


class TestHotelSystemIntegration:
    """Test complete hotel system integration"""
    
    def test_rate_service_integration(self, test_db, sample_room, sample_rates):
        """Test rate service with real database"""
        rate_service = RateService(test_db)
        
        # Test getting standard rate
        rate = rate_service.get_rate_for_date(
            RoomType.STANDARD_QUEEN,
            date.today(),
            RateType.STANDARD
        )
        
        assert rate == Decimal('120.00')
        
        # Test getting weekend rate
        rate = rate_service.get_rate_for_date(
            RoomType.STANDARD_QUEEN,
            date.today(),
            RateType.WEEKEND
        )
        
        assert rate == Decimal('140.00')
    
    def test_availability_service_integration(self, test_db, sample_room, sample_availability):
        """Test availability service with real database"""
        availability_service = AvailabilityService(test_db)
        
        # Test availability check
        result = availability_service.check_availability(
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            room_type=RoomType.STANDARD_QUEEN,
            adults=2,
            pets=False
        )
        
        assert result['available'] is True
        assert result['num_nights'] == 2
        assert len(result['rooms']) == 1
        assert result['rooms'][0]['room_type'] == 'standard_queen'
        assert result['rooms'][0]['available'] == 3
    
    def test_booking_service_integration(self, test_db, sample_room, sample_availability):
        """Test booking service with real database"""
        booking_service = BookingService(test_db)
        
        # Create guest data
        guest_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '555-1234'
        }
        
        # Create booking
        booking = booking_service.create_booking(
            guest_data=guest_data,
            room_type=RoomType.STANDARD_QUEEN,
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            adults=2,
            children=0,
            pets=False,
            source="test"
        )
        
        assert booking is not None
        assert booking.confirmation_number is not None
        assert booking.guest.first_name == 'John'
        assert booking.room.room_type == RoomType.STANDARD_QUEEN
        assert booking.status == BookingStatus.PENDING
        assert booking.payment_status == PaymentStatus.PENDING
        
        # Verify guest was created
        guest = test_db.query(Guest).filter(Guest.email == 'john.doe@example.com').first()
        assert guest is not None
        assert guest.first_name == 'John'
        assert guest.last_name == 'Doe'
    
    def test_booking_cancellation_integration(self, test_db, sample_room, sample_availability):
        """Test booking cancellation with real database"""
        booking_service = BookingService(test_db)
        
        # Create guest data
        guest_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'phone': '555-5678'
        }
        
        # Create booking
        booking = booking_service.create_booking(
            guest_data=guest_data,
            room_type=RoomType.STANDARD_QUEEN,
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            adults=2,
            source="test"
        )
        
        confirmation_number = booking.confirmation_number
        
        # Cancel booking
        success = booking_service.cancel_booking(confirmation_number, "Guest cancelled")
        
        assert success is True
        
        # Verify booking was cancelled
        cancelled_booking = booking_service.get_booking(confirmation_number)
        assert cancelled_booking.status == BookingStatus.CANCELLED
        assert cancelled_booking.cancellation_reason == "Guest cancelled"
    
    def test_availability_update_after_booking(self, test_db, sample_room, sample_availability):
        """Test that availability is updated after booking"""
        booking_service = BookingService(test_db)
        availability_service = AvailabilityService(test_db)
        
        # Get initial availability
        initial_availability = availability_service.check_availability(
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            room_type=RoomType.STANDARD_QUEEN,
            adults=2
        )
        
        initial_available = initial_availability['rooms'][0]['available']
        
        # Create booking
        guest_data = {
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'email': 'bob.johnson@example.com',
            'phone': '555-9999'
        }
        
        booking = booking_service.create_booking(
            guest_data=guest_data,
            room_type=RoomType.STANDARD_QUEEN,
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            adults=2,
            source="test"
        )
        
        # Check availability after booking
        updated_availability = availability_service.check_availability(
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            room_type=RoomType.STANDARD_QUEEN,
            adults=2
        )
        
        updated_available = updated_availability['rooms'][0]['available']
        
        # Availability should be reduced by 1
        assert updated_available == initial_available - 1
    
    def test_multiple_room_types_integration(self, test_db):
        """Test system with multiple room types"""
        # Create multiple room types
        rooms = [
            Room(
                room_number="101",
                room_type=RoomType.STANDARD_QUEEN,
                floor=1,
                max_occupancy=2,
                amenities=["WiFi", "TV"]
            ),
            Room(
                room_number="201",
                room_type=RoomType.KING_SUITE,
                floor=2,
                max_occupancy=4,
                amenities=["WiFi", "TV", "Sofa"]
            ),
            Room(
                room_number="301",
                room_type=RoomType.PET_FRIENDLY,
                floor=3,
                max_occupancy=2,
                pet_friendly=True,
                amenities=["WiFi", "TV", "Pet Bowls"]
            )
        ]
        
        for room in rooms:
            test_db.add(room)
        test_db.commit()
        
        # Create rates for each room type
        rates = [
            RoomRate(
                room_id=rooms[0].id,
                rate_type=RateType.STANDARD,
                base_rate=Decimal('120.00'),
                effective_date=date.today(),
                end_date=date.today() + timedelta(days=365)
            ),
            RoomRate(
                room_id=rooms[1].id,
                rate_type=RateType.STANDARD,
                base_rate=Decimal('180.00'),
                effective_date=date.today(),
                end_date=date.today() + timedelta(days=365)
            ),
            RoomRate(
                room_id=rooms[2].id,
                rate_type=RateType.STANDARD,
                base_rate=Decimal('140.00'),
                effective_date=date.today(),
                end_date=date.today() + timedelta(days=365)
            )
        ]
        
        for rate in rates:
            test_db.add(rate)
        test_db.commit()
        
        # Create availability for each room type
        availability = [
            RoomAvailability(
                room_id=rooms[0].id,
                date=date.today(),
                total_inventory=5,
                booked_count=1,
                available_count=4,
                available=True
            ),
            RoomAvailability(
                room_id=rooms[1].id,
                date=date.today(),
                total_inventory=3,
                booked_count=0,
                available_count=3,
                available=True
            ),
            RoomAvailability(
                room_id=rooms[2].id,
                date=date.today(),
                total_inventory=2,
                booked_count=1,
                available_count=1,
                available=True
            )
        ]
        
        for avail in availability:
            test_db.add(avail)
        test_db.commit()
        
        # Test availability service with multiple room types
        availability_service = AvailabilityService(test_db)
        
        # Test without pets (should show standard and king)
        result = availability_service.check_availability(
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            adults=2,
            pets=False
        )
        
        assert result['available'] is True
        assert len(result['rooms']) >= 2  # At least Standard Queen and King Suite
        room_types = [room['room_type'] for room in result['rooms']]
        assert 'standard_queen' in room_types
        assert 'king_suite' in room_types
        
        # Test with pets (should show pet-friendly only)
        result = availability_service.check_availability(
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            adults=2,
            pets=True
        )
        
        assert result['available'] is True
        assert len(result['rooms']) == 1  # Pet-Friendly only
        assert result['rooms'][0]['room_type'] == 'pet_friendly'
    
    def test_rate_calculation_integration(self, test_db, sample_room):
        """Test rate calculation with different rate types"""
        # Create different rate types
        rates = [
            RoomRate(
                room_id=sample_room.id,
                rate_type=RateType.STANDARD,
                base_rate=Decimal('120.00'),
                effective_date=date.today(),
                end_date=date.today() + timedelta(days=365)
            ),
            RoomRate(
                room_id=sample_room.id,
                rate_type=RateType.WEEKEND,
                base_rate=Decimal('140.00'),
                effective_date=date.today(),
                end_date=date.today() + timedelta(days=365)
            ),
            RoomRate(
                room_id=sample_room.id,
                rate_type=RateType.PEAK,
                base_rate=Decimal('160.00'),
                effective_date=date.today(),
                end_date=date.today() + timedelta(days=365)
            )
        ]
        
        for rate in rates:
            test_db.add(rate)
        test_db.commit()
        
        rate_service = RateService(test_db)
        
        # Test different rate types
        standard_rate = rate_service.get_rate_for_date(
            RoomType.STANDARD_QUEEN,
            date.today(),
            RateType.STANDARD
        )
        assert standard_rate == Decimal('120.00')
        
        weekend_rate = rate_service.get_rate_for_date(
            RoomType.STANDARD_QUEEN,
            date.today(),
            RateType.WEEKEND
        )
        assert weekend_rate == Decimal('140.00')
        
        peak_rate = rate_service.get_rate_for_date(
            RoomType.STANDARD_QUEEN,
            date.today(),
            RateType.PEAK
        )
        assert peak_rate == Decimal('160.00')
    
    def test_booking_with_special_requests(self, test_db, sample_room, sample_availability):
        """Test booking creation with special requests"""
        booking_service = BookingService(test_db)
        
        guest_data = {
            'first_name': 'Alice',
            'last_name': 'Brown',
            'email': 'alice.brown@example.com',
            'phone': '555-1111'
        }
        
        booking = booking_service.create_booking(
            guest_data=guest_data,
            room_type=RoomType.STANDARD_QUEEN,
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            adults=2,
            children=1,
            pets=False,
            special_requests="Ground floor room preferred, late check-in",
            source="test"
        )
        
        assert booking is not None
        assert booking.special_requests == "Ground floor room preferred, late check-in"
        assert booking.children == 1
        assert booking.adults == 2
    
    def test_booking_confirmation_number_uniqueness(self, test_db, sample_room, sample_availability):
        """Test that booking confirmation numbers are unique"""
        booking_service = BookingService(test_db)
        
        guest_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '555-0000'
        }
        
        # Create multiple bookings
        bookings = []
        for i in range(5):
            booking = booking_service.create_booking(
                guest_data=guest_data,
                room_type=RoomType.STANDARD_QUEEN,
                check_in=date.today() + timedelta(days=i),
                check_out=date.today() + timedelta(days=i+2),
                adults=2,
                source="test"
            )
            bookings.append(booking)
        
        # Check that all confirmation numbers are unique
        confirmation_numbers = [booking.confirmation_number for booking in bookings]
        assert len(confirmation_numbers) == len(set(confirmation_numbers))
        
        # Check that all confirmation numbers are 8 characters
        for conf_num in confirmation_numbers:
            assert len(conf_num) == 8
            assert conf_num.isalnum()  # Should be alphanumeric
