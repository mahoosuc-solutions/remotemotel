"""
Tests for hotel services
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from packages.hotel.services import RateService, AvailabilityService, BookingService
from packages.hotel.models import (
    Room, RoomRate, RoomAvailability, Guest, Booking,
    RoomType, RateType, BookingStatus, PaymentStatus
)


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    session = Mock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def sample_room():
    """Create sample room for testing"""
    room = Mock()
    room.id = 1
    room.room_type = RoomType.STANDARD_QUEEN
    room.room_number = "101"
    return room


@pytest.fixture
def sample_guest():
    """Create sample guest for testing"""
    guest = Mock()
    guest.id = 1
    guest.first_name = "John"
    guest.last_name = "Doe"
    guest.email = "john.doe@example.com"
    guest.phone = "555-1234"
    return guest


class TestRateService:
    """Test RateService"""
    
    def test_get_rate_for_date_with_existing_rate(self, mock_db_session, sample_room):
        """Test getting rate when rate exists"""
        # Mock rate
        rate = Mock()
        rate.base_rate = Decimal('120.00')
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.join.return_value.first.return_value = rate
        mock_db_session.query.return_value = mock_query
        
        rate_service = RateService(mock_db_session)
        result = rate_service.get_rate_for_date(
            RoomType.STANDARD_QUEEN, 
            date.today(), 
            RateType.STANDARD
        )
        
        assert result == Decimal('120.00')
    
    def test_get_rate_for_date_with_fallback(self, mock_db_session):
        """Test getting rate when no rate exists (fallback to default)"""
        # Mock empty query result
        mock_query = Mock()
        mock_query.filter.return_value.join.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        rate_service = RateService(mock_db_session)
        result = rate_service.get_rate_for_date(
            RoomType.STANDARD_QUEEN, 
            date.today(), 
            RateType.STANDARD
        )
        
        # Should return default rate
        assert result == Decimal('120.00')
    
    def test_get_rate_for_different_room_types(self, mock_db_session):
        """Test getting rates for different room types"""
        mock_query = Mock()
        mock_query.filter.return_value.join.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        rate_service = RateService(mock_db_session)
        
        # Test different room types
        standard_rate = rate_service.get_rate_for_date(RoomType.STANDARD_QUEEN, date.today())
        king_rate = rate_service.get_rate_for_date(RoomType.KING_SUITE, date.today())
        pet_rate = rate_service.get_rate_for_date(RoomType.PET_FRIENDLY, date.today())
        deluxe_rate = rate_service.get_rate_for_date(RoomType.DELUXE_SUITE, date.today())
        
        assert standard_rate == Decimal('120.00')
        assert king_rate == Decimal('180.00')
        assert pet_rate == Decimal('140.00')
        assert deluxe_rate == Decimal('220.00')
    
    def test_set_rate(self, mock_db_session, sample_room):
        """Test setting a new rate"""
        # Mock room query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_room
        mock_db_session.query.return_value = mock_query
        
        rate_service = RateService(mock_db_session)
        
        result = rate_service.set_rate(
            room_type=RoomType.STANDARD_QUEEN,
            rate_type=RateType.STANDARD,
            base_rate=Decimal('130.00'),
            effective_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
        
        # Verify rate was added and committed
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result is not None


class TestAvailabilityService:
    """Test AvailabilityService"""
    
    def test_check_availability_success(self, mock_db_session):
        """Test successful availability check"""
        # Mock availability service
        with patch.object(AvailabilityService, '_get_min_availability') as mock_min_avail:
            mock_min_avail.return_value = 3
            
            availability_service = AvailabilityService(mock_db_session)
            
            result = availability_service.check_availability(
                check_in=date.today(),
                check_out=date.today() + timedelta(days=2),
                room_type=RoomType.STANDARD_QUEEN,
                adults=2,
                pets=False
            )
            
            assert result['available'] is True
            assert result['num_nights'] == 2
            assert len(result['rooms']) > 0
    
    def test_check_availability_no_rooms(self, mock_db_session):
        """Test availability check when no rooms available"""
        with patch.object(AvailabilityService, '_get_min_availability') as mock_min_avail:
            mock_min_avail.return_value = 0
            
            availability_service = AvailabilityService(mock_db_session)
            
            result = availability_service.check_availability(
                check_in=date.today(),
                check_out=date.today() + timedelta(days=2),
                room_type=RoomType.STANDARD_QUEEN,
                adults=2,
                pets=False
            )
            
            assert result['available'] is False
            assert len(result['rooms']) == 0
    
    def test_check_availability_invalid_dates(self, mock_db_session):
        """Test availability check with invalid dates"""
        availability_service = AvailabilityService(mock_db_session)
        
        result = availability_service.check_availability(
            check_in=date.today(),
            check_out=date.today(),  # Same date
            room_type=RoomType.STANDARD_QUEEN,
            adults=2,
            pets=False
        )
        
        assert result['available'] is False
        assert 'error' in result
    
    def test_get_min_availability_with_data(self, mock_db_session, sample_room):
        """Test getting minimum availability with data"""
        # Mock availability record
        availability = Mock()
        availability.available_count = 3
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.join.return_value.first.return_value = availability
        mock_db_session.query.return_value = mock_query
        
        availability_service = AvailabilityService(mock_db_session)
        
        result = availability_service._get_min_availability(
            RoomType.STANDARD_QUEEN,
            date.today(),
            date.today() + timedelta(days=2)
        )
        
        assert result == 3
    
    def test_get_min_availability_no_data(self, mock_db_session):
        """Test getting minimum availability with no data (default)"""
        # Mock empty query result
        mock_query = Mock()
        mock_query.filter.return_value.join.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        availability_service = AvailabilityService(mock_db_session)
        
        result = availability_service._get_min_availability(
            RoomType.STANDARD_QUEEN,
            date.today(),
            date.today() + timedelta(days=2)
        )
        
        # Should return default availability
        assert result == 10  # Default for STANDARD_QUEEN
    
    def test_update_availability(self, mock_db_session, sample_room):
        """Test updating availability"""
        # Mock room query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_room
        mock_db_session.query.return_value = mock_query
        
        availability_service = AvailabilityService(mock_db_session)
        
        result = availability_service.update_availability(
            room_type=RoomType.STANDARD_QUEEN,
            date=date.today(),
            total_inventory=5,
            booked_count=2,
            maintenance=False
        )
        
        # Verify availability was added and committed
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result is not None


class TestBookingService:
    """Test BookingService"""
    
    def test_create_booking_success(self, mock_db_session, sample_room, sample_guest):
        """Test successful booking creation"""
        # Mock guest query
        mock_guest_query = Mock()
        mock_guest_query.filter.return_value.first.return_value = sample_guest
        mock_room_query = Mock()
        mock_room_query.filter.return_value.first.return_value = sample_room
        
        def query_side_effect(model):
            if model == Guest:
                return mock_guest_query
            elif model == Room:
                return mock_room_query
            return Mock()
        
        mock_db_session.query.side_effect = query_side_effect
        
        # Mock availability check
        with patch.object(AvailabilityService, 'check_availability') as mock_avail:
            mock_avail.return_value = {'available': True, 'rooms': [{'type': 'Standard Queen'}]}
            
            booking_service = BookingService(mock_db_session)
            
            guest_data = {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'phone': '555-1234'
            }
            
            result = booking_service.create_booking(
                guest_data=guest_data,
                room_type=RoomType.STANDARD_QUEEN,
                check_in=date.today(),
                check_out=date.today() + timedelta(days=2),
                adults=2,
                children=0,
                pets=False,
                source="test"
            )
            
            # Verify booking was created
            mock_db_session.add.assert_called()
            mock_db_session.commit.assert_called()
            assert result is not None
            assert result.confirmation_number is not None
    
    def test_create_booking_no_availability(self, mock_db_session, sample_guest):
        """Test booking creation when no availability"""
        # Mock guest query
        mock_guest_query = Mock()
        mock_guest_query.filter.return_value.first.return_value = sample_guest
        mock_db_session.query.return_value = mock_guest_query
        
        # Mock availability check returning no availability
        with patch.object(AvailabilityService, 'check_availability') as mock_avail:
            mock_avail.return_value = {'available': False, 'rooms': []}
            
            booking_service = BookingService(mock_db_session)
            
            guest_data = {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com'
            }
            
            with pytest.raises(ValueError, match="No rooms available"):
                booking_service.create_booking(
                    guest_data=guest_data,
                    room_type=RoomType.STANDARD_QUEEN,
                    check_in=date.today(),
                    check_out=date.today() + timedelta(days=2),
                    adults=2
                )
    
    def test_create_booking_invalid_dates(self, mock_db_session, sample_guest):
        """Test booking creation with invalid dates"""
        booking_service = BookingService(mock_db_session)
        
        guest_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        
        with pytest.raises(ValueError, match="Check-out must be after check-in"):
            booking_service.create_booking(
                guest_data=guest_data,
                room_type=RoomType.STANDARD_QUEEN,
                check_in=date.today(),
                check_out=date.today(),  # Same date
                adults=2
            )
    
    def test_get_booking(self, mock_db_session):
        """Test getting booking by confirmation number"""
        # Mock booking
        booking = Mock()
        booking.confirmation_number = "ABC12345"
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = booking
        mock_db_session.query.return_value = mock_query
        
        booking_service = BookingService(mock_db_session)
        
        result = booking_service.get_booking("ABC12345")
        
        assert result == booking
    
    def test_get_booking_not_found(self, mock_db_session):
        """Test getting booking that doesn't exist"""
        # Mock empty query result
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        booking_service = BookingService(mock_db_session)
        
        result = booking_service.get_booking("NONEXISTENT")
        
        assert result is None
    
    def test_cancel_booking_success(self, mock_db_session):
        """Test successful booking cancellation"""
        # Mock booking
        booking = Mock()
        booking.confirmation_number = "ABC12345"
        booking.status = BookingStatus.CONFIRMED
        booking.room = Mock()
        booking.room.room_type = RoomType.STANDARD_QUEEN
        booking.check_in_date = date.today()
        booking.check_out_date = date.today() + timedelta(days=2)
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = booking
        mock_db_session.query.return_value = mock_query
        
        booking_service = BookingService(mock_db_session)
        
        result = booking_service.cancel_booking("ABC12345", "Guest cancelled")
        
        # Verify booking was updated and committed
        mock_db_session.commit.assert_called()
        assert result is True
        assert booking.status == BookingStatus.CANCELLED
    
    def test_cancel_booking_not_found(self, mock_db_session):
        """Test cancelling booking that doesn't exist"""
        # Mock empty query result
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        booking_service = BookingService(mock_db_session)
        
        result = booking_service.cancel_booking("NONEXISTENT")
        
        assert result is False
    
    def test_cancel_booking_already_cancelled(self, mock_db_session):
        """Test cancelling booking that's already cancelled"""
        # Mock cancelled booking
        booking = Mock()
        booking.confirmation_number = "ABC12345"
        booking.status = BookingStatus.CANCELLED
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = booking
        mock_db_session.query.return_value = mock_query
        
        booking_service = BookingService(mock_db_session)
        
        result = booking_service.cancel_booking("ABC12345")
        
        assert result is False
