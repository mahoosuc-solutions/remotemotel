"""
Tests for hotel API endpoints
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from packages.hotel.api import app
from packages.hotel.models import RoomType, BookingStatus, PaymentStatus, RateType


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


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


class TestAvailabilityAPI:
    """Test availability API endpoints"""
    
    def test_check_availability_success(self, client):
        """Test successful availability check"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.AvailabilityService') as mock_service_class:
                mock_service = Mock()
                mock_service.check_availability.return_value = {
                    'available': True,
                    'check_in': '2024-12-01',
                    'check_out': '2024-12-03',
                    'num_nights': 2,
                    'adults': 2,
                    'pets': False,
                    'rooms': [
                        {
                            'room_type': 'standard_queen',
                            'available': 3,
                            'rate_per_night': 120.0,
                            'total_price': 240.0
                        }
                    ]
                }
                mock_service_class.return_value = mock_service
                
                response = client.get(
                    "/hotel/availability",
                    params={
                        "check_in": "2024-12-01",
                        "check_out": "2024-12-03",
                        "adults": 2,
                        "pets": False
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['available'] is True
                assert data['num_nights'] == 2
                assert len(data['rooms']) == 1
                assert data['rooms'][0]['type'] == 'Standard Queen'  # Converted to readable name
    
    def test_check_availability_no_rooms(self, client):
        """Test availability check when no rooms available"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.AvailabilityService') as mock_service_class:
                mock_service = Mock()
                mock_service.check_availability.return_value = {
                    'available': False,
                    'check_in': '2024-12-01',
                    'check_out': '2024-12-03',
                    'num_nights': 2,
                    'adults': 2,
                    'pets': False,
                    'rooms': []
                }
                mock_service_class.return_value = mock_service
                
                response = client.get(
                    "/hotel/availability",
                    params={
                        "check_in": "2024-12-01",
                        "check_out": "2024-12-03",
                        "adults": 2
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['available'] is False
                assert len(data['rooms']) == 0
    
    def test_check_availability_invalid_dates(self, client):
        """Test availability check with invalid dates"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.AvailabilityService') as mock_service_class:
                mock_service = Mock()
                mock_service.check_availability.return_value = {
                    'available': False,
                    'error': 'Check-out must be after check-in'
                }
                mock_service_class.return_value = mock_service
                
                response = client.get(
                    "/hotel/availability",
                    params={
                        "check_in": "2024-12-03",
                        "check_out": "2024-12-01",  # Invalid: check-out before check-in
                        "adults": 2
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['available'] is False
                assert 'error' in data


class TestBookingAPI:
    """Test booking API endpoints"""
    
    def test_create_booking_success(self, client):
        """Test successful booking creation"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_booking = Mock()
                mock_booking.confirmation_number = "ABC12345"
                mock_booking.guest = Mock()
                mock_booking.guest.first_name = "John"
                mock_booking.guest.last_name = "Doe"
                mock_booking.room = Mock()
                mock_booking.room.room_type = RoomType.STANDARD_QUEEN
                mock_booking.check_in_date = date(2024, 12, 1)
                mock_booking.check_out_date = date(2024, 12, 3)
                mock_booking.total_amount = Decimal('240.00')
                mock_booking.status = BookingStatus.PENDING
                mock_booking.created_at = Mock()
                mock_booking.created_at.isoformat.return_value = "2024-10-18T10:00:00"
                
                mock_service.create_booking.return_value = mock_booking
                mock_service_class.return_value = mock_service
                
                booking_data = {
                    "guest": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "phone": "555-1234"
                    },
                    "room_type": "standard_queen",
                    "check_in": "2024-12-01",
                    "check_out": "2024-12-03",
                    "adults": 2,
                    "children": 0,
                    "pets": False,
                    "source": "test"
                }
                
                response = client.post("/hotel/bookings", json=booking_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data['confirmation_number'] == "ABC12345"
                assert data['guest_name'] == "John Doe"
                assert data['room_type'] == "standard_queen"
                assert data['total_amount'] == 240.0
    
    def test_create_booking_validation_error(self, client):
        """Test booking creation with validation error"""
        booking_data = {
            "guest": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "invalid-email",  # Invalid email
                "phone": "555-1234"
            },
            "room_type": "standard_queen",
            "check_in": "2024-12-01",
            "check_out": "2024-12-03",
            "adults": 2
        }
        
        response = client.post("/hotel/bookings", json=booking_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_booking_invalid_dates(self, client):
        """Test booking creation with invalid dates"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_service.create_booking.side_effect = ValueError("Check-out must be after check-in")
                mock_service_class.return_value = mock_service
                
                booking_data = {
                    "guest": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "phone": "555-1234"
                    },
                    "room_type": "standard_queen",
                    "check_in": "2024-12-03",
                    "check_out": "2024-12-01",  # Invalid: check-out before check-in
                    "adults": 2
                }
                
                response = client.post("/hotel/bookings", json=booking_data)
                
                assert response.status_code == 400
                data = response.json()
                assert "Check-out must be after check-in" in data['detail']
    
    def test_get_booking_success(self, client):
        """Test getting booking by confirmation number"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_booking = Mock()
                mock_booking.confirmation_number = "ABC12345"
                mock_booking.guest = Mock()
                mock_booking.guest.first_name = "John"
                mock_booking.guest.last_name = "Doe"
                mock_booking.guest.email = "john.doe@example.com"
                mock_booking.guest.phone = "555-1234"
                mock_booking.room = Mock()
                mock_booking.room.room_type = RoomType.STANDARD_QUEEN
                mock_booking.check_in_date = date(2024, 12, 1)
                mock_booking.check_out_date = date(2024, 12, 3)
                mock_booking.adults = 2
                mock_booking.children = 0
                mock_booking.pets = False
                mock_booking.total_amount = Decimal('240.00')
                mock_booking.status = BookingStatus.PENDING
                mock_booking.payment_status = PaymentStatus.PENDING
                mock_booking.special_requests = None
                mock_booking.created_at = Mock()
                mock_booking.created_at.isoformat.return_value = "2024-10-18T10:00:00"
                
                mock_service.get_booking.return_value = mock_booking
                mock_service_class.return_value = mock_service
                
                response = client.get("/hotel/bookings/ABC12345")
                
                assert response.status_code == 200
                data = response.json()
                assert data['confirmation_number'] == "ABC12345"
                assert data['guest']['first_name'] == "John"
                assert data['room_type'] == "standard_queen"
    
    def test_get_booking_not_found(self, client):
        """Test getting booking that doesn't exist"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_service.get_booking.return_value = None
                mock_service_class.return_value = mock_service
                
                response = client.get("/hotel/bookings/NONEXISTENT")
                
                assert response.status_code == 404
                data = response.json()
                assert "Booking not found" in data['detail']
    
    def test_cancel_booking_success(self, client):
        """Test successful booking cancellation"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_service.cancel_booking.return_value = True
                mock_service_class.return_value = mock_service
                
                response = client.delete(
                    "/hotel/bookings/ABC12345",
                    params={"reason": "Guest cancelled"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['message'] == "Booking cancelled successfully"
    
    def test_cancel_booking_not_found(self, client):
        """Test cancelling booking that doesn't exist"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_service.cancel_booking.return_value = False
                mock_service_class.return_value = mock_service
                
                response = client.delete("/hotel/bookings/NONEXISTENT")
                
                assert response.status_code == 404
                data = response.json()
                assert "Booking not found or cannot be cancelled" in data['detail']


class TestRatesAPI:
    """Test rates API endpoints"""
    
    def test_set_rate_success(self, client):
        """Test successful rate setting"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.RateService') as mock_service_class:
                mock_service = Mock()
                mock_rate = Mock()
                mock_rate.id = 1
                mock_rate.room_type = RoomType.STANDARD_QUEEN
                mock_rate.rate_type = RateType.STANDARD
                mock_rate.base_rate = Decimal('130.00')
                mock_rate.effective_date = date(2024, 12, 1)
                mock_rate.end_date = date(2024, 12, 31)
                mock_rate.created_at = Mock()
                mock_rate.created_at.isoformat.return_value = "2024-10-18T10:00:00"
                
                mock_service.set_rate.return_value = mock_rate
                mock_service_class.return_value = mock_service
                
                rate_data = {
                    "room_type": "standard_queen",
                    "rate_type": "standard",
                    "base_rate": 130.0,
                    "effective_date": "2024-12-01",
                    "end_date": "2024-12-31",
                    "min_nights": 1,
                    "max_nights": 7
                }
                
                response = client.post("/hotel/rates", json=rate_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data['room_type'] == "standard_queen"
                assert data['base_rate'] == 130.0
    
    def test_set_rate_validation_error(self, client):
        """Test rate setting with validation error"""
        rate_data = {
            "room_type": "standard_queen",
            "rate_type": "standard",
            "base_rate": -10.0,  # Invalid: negative rate
            "effective_date": "2024-12-01",
            "end_date": "2024-12-31"
        }
        
        response = client.post("/hotel/rates", json=rate_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_rates_success(self, client):
        """Test getting rates for room type"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            with patch('packages.hotel.api.RateService') as mock_service_class:
                mock_service = Mock()
                mock_service.get_rate_for_date.return_value = Decimal('120.00')
                mock_service_class.return_value = mock_service
                
                response = client.get(
                    "/hotel/rates/standard_queen",
                    params={
                        "start_date": "2024-12-01",
                        "end_date": "2024-12-03"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['room_type'] == "standard_queen"
                assert len(data['rates']) == 3  # 3 days
                assert data['rates'][0]['rate'] == 120.0


class TestRoomsAPI:
    """Test rooms API endpoints"""
    
    def test_get_rooms_success(self, client):
        """Test getting rooms list"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            # Mock room data
            mock_room = Mock()
            mock_room.id = 1
            mock_room.room_number = "101"
            mock_room.room_type = RoomType.STANDARD_QUEEN
            mock_room.floor = 1
            mock_room.max_occupancy = 2
            mock_room.max_adults = 2
            mock_room.max_children = 2
            mock_room.pet_friendly = False
            mock_room.smoking_allowed = False
            mock_room.amenities = ["WiFi", "TV"]
            mock_room.square_footage = 250
            mock_room.bed_configuration = "1 Queen"
            mock_room.description = "Comfortable room"
            mock_room.active = True
            mock_room.created_at = Mock()
            mock_room.created_at.isoformat.return_value = "2024-10-18T10:00:00"
            
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [mock_room]
            mock_session.query.return_value = mock_query
            
            response = client.get("/hotel/rooms")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]['room_number'] == "101"
            assert data[0]['room_type'] == "standard_queen"


class TestDashboardAPI:
    """Test dashboard API endpoints"""
    
    def test_get_dashboard_success(self, client):
        """Test getting dashboard data"""
        with patch('packages.hotel.api.get_db_session') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            # Mock booking data
            mock_booking = Mock()
            mock_booking.check_in_date = date(2024, 12, 1)
            mock_booking.status = BookingStatus.CONFIRMED
            mock_booking.total_amount = Decimal('240.00')
            mock_booking.room = Mock()
            mock_booking.room.room_type = RoomType.STANDARD_QUEEN
            
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [mock_booking]
            mock_session.query.return_value = mock_query
            
            with patch('packages.hotel.api.AvailabilityService') as mock_service_class:
                mock_service = Mock()
                mock_service.check_availability.return_value = {
                    'available': True,
                    'rooms': [{'type': 'Standard Queen', 'available': 3}]
                }
                mock_service_class.return_value = mock_service
                
                response = client.get("/hotel/dashboard")
                
                assert response.status_code == 200
                data = response.json()
                assert 'bookings' in data
                assert 'availability' in data
                assert data['bookings']['total'] == 1
                assert data['bookings']['total_revenue'] == 240.0
