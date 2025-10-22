"""
Tests for voice AI integration with hotel management system
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, AsyncMock

from packages.tools.check_availability import check_availability
from packages.tools.create_booking import create_booking


class TestAvailabilityVoiceIntegration:
    """Test availability checking for voice AI"""
    
    @pytest.mark.asyncio
    async def test_check_availability_success(self):
        """Test successful availability check via voice AI"""
        with patch('packages.tools.check_availability.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_session = Mock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_db_manager.return_value = mock_db
            
            with patch('packages.tools.check_availability.AvailabilityService') as mock_service_class:
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
                        },
                        {
                            'room_type': 'king_suite',
                            'available': 2,
                            'rate_per_night': 180.0,
                            'total_price': 360.0
                        }
                    ]
                }
                mock_service_class.return_value = mock_service
                
                result = await check_availability(
                    check_in="2024-12-01",
                    check_out="2024-12-03",
                    adults=2,
                    pets=False
                )
                
                assert result['available'] is True
                assert result['num_nights'] == 2
                assert len(result['rooms']) == 2
                # Check that room types are converted to readable names
                room_types = [room['type'] for room in result['rooms']]
                assert 'Standard Queen' in room_types
                assert 'King Suite' in room_types
    
    @pytest.mark.asyncio
    async def test_check_availability_pets(self):
        """Test availability check for pet-friendly rooms"""
        with patch('packages.tools.check_availability.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_session = Mock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_db_manager.return_value = mock_db
            
            with patch('packages.tools.check_availability.AvailabilityService') as mock_service_class:
                mock_service = Mock()
                mock_service.check_availability.return_value = {
                    'available': True,
                    'check_in': '2024-12-01',
                    'check_out': '2024-12-03',
                    'num_nights': 2,
                    'adults': 2,
                    'pets': True,
                    'rooms': [
                        {
                            'room_type': 'pet_friendly',
                            'available': 2,
                            'rate_per_night': 140.0,
                            'total_price': 280.0
                        }
                    ]
                }
                mock_service_class.return_value = mock_service
                
                result = await check_availability(
                    check_in="2024-12-01",
                    check_out="2024-12-03",
                    adults=2,
                    pets=True
                )
                
                assert result['available'] is True
                assert result['pets'] is True
                assert len(result['rooms']) == 1
                assert result['rooms'][0]['type'] == 'Pet-Friendly Room'
    
    @pytest.mark.asyncio
    async def test_check_availability_no_rooms(self):
        """Test availability check when no rooms available"""
        with patch('packages.tools.check_availability.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_session = Mock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_db_manager.return_value = mock_db
            
            with patch('packages.tools.check_availability.AvailabilityService') as mock_service_class:
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
                
                result = await check_availability(
                    check_in="2024-12-01",
                    check_out="2024-12-03",
                    adults=2,
                    pets=False
                )
                
                assert result['available'] is False
                assert len(result['rooms']) == 0
    
    @pytest.mark.asyncio
    async def test_check_availability_fallback(self):
        """Test availability check with fallback data"""
        with patch('packages.tools.check_availability.DatabaseManager') as mock_db_manager:
            # Mock database error
            mock_db_manager.side_effect = Exception("Database error")
            
            result = await check_availability(
                check_in="2024-12-01",
                check_out="2024-12-03",
                adults=2,
                pets=False
            )
            
            # Should use fallback data
            assert result['available'] is True
            assert result['note'] == "Using fallback availability data"
            assert len(result['rooms']) > 0
    
    @pytest.mark.asyncio
    async def test_check_availability_invalid_dates(self):
        """Test availability check with invalid dates"""
        with patch('packages.tools.check_availability.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_session = Mock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_db_manager.return_value = mock_db
            
            with patch('packages.tools.check_availability.AvailabilityService') as mock_service_class:
                mock_service = Mock()
                mock_service.check_availability.return_value = {
                    'available': False,
                    'error': 'Check-out must be after check-in'
                }
                mock_service_class.return_value = mock_service
                
                result = await check_availability(
                    check_in="2024-12-03",
                    check_out="2024-12-01",  # Invalid: check-out before check-in
                    adults=2,
                    pets=False
                )
                
                assert result['available'] is False
                assert 'error' in result


class TestBookingVoiceIntegration:
    """Test booking creation for voice AI"""
    
    @pytest.mark.asyncio
    async def test_create_booking_success(self):
        """Test successful booking creation via voice AI"""
        with patch('packages.tools.create_booking.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_session = Mock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_db_manager.return_value = mock_db
            
            with patch('packages.tools.create_booking.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_booking = Mock()
                mock_booking.confirmation_number = "ABC12345"
                mock_booking.guest = Mock()
                mock_booking.guest.first_name = "John"
                mock_booking.guest.last_name = "Doe"
                mock_booking.room = Mock()
                mock_booking.room.room_type = "standard_queen"
                mock_booking.check_in_date = date(2024, 12, 1)
                mock_booking.check_out_date = date(2024, 12, 3)
                mock_booking.adults = 2
                mock_booking.pets = False
                mock_booking.total_amount = 240.0
                mock_booking.status = "pending"
                mock_booking.special_requests = None
                mock_booking.created_at = Mock()
                mock_booking.created_at.isoformat.return_value = "2024-10-18T10:00:00"
                
                mock_service.create_booking.return_value = mock_booking
                mock_service_class.return_value = mock_service
                
                result = await create_booking(
                    guest_name="John Doe",
                    guest_email="john.doe@example.com",
                    guest_phone="555-1234",
                    check_in="2024-12-01",
                    check_out="2024-12-03",
                    room_type="Standard Queen",
                    adults=2,
                    pets=False,
                    special_requests="Ground floor preferred"
                )
                
                assert result['success'] is True
                assert result['confirmation_number'] == "ABC12345"
                assert result['guest_name'] == "John Doe"
                assert result['room_type'] == "Standard Queen"
                assert result['total_amount'] == 240.0
    
    @pytest.mark.asyncio
    async def test_create_booking_pet_friendly(self):
        """Test booking creation for pet-friendly room"""
        with patch('packages.tools.create_booking.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_session = Mock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_db_manager.return_value = mock_db
            
            with patch('packages.tools.create_booking.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_booking = Mock()
                mock_booking.confirmation_number = "ABC12346"
                mock_booking.guest = Mock()
                mock_booking.guest.first_name = "Jane"
                mock_booking.guest.last_name = "Smith"
                mock_booking.room = Mock()
                mock_booking.room.room_type = "pet_friendly"
                mock_booking.check_in_date = date(2024, 12, 1)
                mock_booking.check_out_date = date(2024, 12, 3)
                mock_booking.adults = 2
                mock_booking.pets = True
                mock_booking.total_amount = 320.0  # Higher due to pet fee
                mock_booking.status = "pending"
                mock_booking.special_requests = "Pet-friendly room needed"
                mock_booking.created_at = Mock()
                mock_booking.created_at.isoformat.return_value = "2024-10-18T10:00:00"
                
                mock_service.create_booking.return_value = mock_booking
                mock_service_class.return_value = mock_service
                
                result = await create_booking(
                    guest_name="Jane Smith",
                    guest_email="jane.smith@example.com",
                    guest_phone="555-5678",
                    check_in="2024-12-01",
                    check_out="2024-12-03",
                    room_type="Pet-Friendly",
                    adults=2,
                    pets=True,
                    special_requests="Pet-friendly room needed"
                )
                
                assert result['success'] is True
                assert result['confirmation_number'] == "ABC12346"
                assert result['guest_name'] == "Jane Smith"
                assert result['room_type'] == "Pet-Friendly"
                assert result['pets'] is True
                assert result['total_amount'] == 320.0
    
    @pytest.mark.asyncio
    async def test_create_booking_invalid_room_type(self):
        """Test booking creation with invalid room type"""
        with patch('packages.tools.create_booking.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_session = Mock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_db_manager.return_value = mock_db
            
            with patch('packages.tools.create_booking.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_service.create_booking.side_effect = ValueError("Invalid room type")
                mock_service_class.return_value = mock_service
                
                result = await create_booking(
                    guest_name="John Doe",
                    guest_email="john.doe@example.com",
                    guest_phone="555-1234",
                    check_in="2024-12-01",
                    check_out="2024-12-03",
                    room_type="Invalid Room Type",
                    adults=2
                )
                
                assert result['success'] is False
                assert 'error' in result
                assert "Invalid room type" in result['error']
    
    @pytest.mark.asyncio
    async def test_create_booking_database_error(self):
        """Test booking creation with database error"""
        with patch('packages.tools.create_booking.DatabaseManager') as mock_db_manager:
            mock_db_manager.side_effect = Exception("Database connection failed")
            
            result = await create_booking(
                guest_name="John Doe",
                guest_email="john.doe@example.com",
                guest_phone="555-1234",
                check_in="2024-12-01",
                check_out="2024-12-03",
                room_type="Standard Queen",
                adults=2
            )
            
            assert result['success'] is False
            assert 'error' in result
            assert "Database connection failed" in result['error']
    
    @pytest.mark.asyncio
    async def test_create_booking_room_type_mapping(self):
        """Test room type string mapping"""
        with patch('packages.tools.create_booking.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_session = Mock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_db_manager.return_value = mock_db
            
            with patch('packages.tools.create_booking.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_booking = Mock()
                mock_booking.confirmation_number = "ABC12347"
                mock_booking.guest = Mock()
                mock_booking.guest.first_name = "Bob"
                mock_booking.guest.last_name = "Johnson"
                mock_booking.room = Mock()
                mock_booking.room.room_type = "king_suite"
                mock_booking.check_in_date = date(2024, 12, 1)
                mock_booking.check_out_date = date(2024, 12, 3)
                mock_booking.adults = 2
                mock_booking.pets = False
                mock_booking.total_amount = 360.0
                mock_booking.status = "pending"
                mock_booking.special_requests = None
                mock_booking.created_at = Mock()
                mock_booking.created_at.isoformat.return_value = "2024-10-18T10:00:00"
                
                mock_service.create_booking.return_value = mock_booking
                mock_service_class.return_value = mock_service
                
                # Test different room type variations
                room_type_tests = [
                    ("king suite", "King Suite"),
                    ("king", "King Suite"),
                    ("standard queen", "Standard Queen"),
                    ("queen", "Standard Queen"),
                    ("pet friendly", "Pet-Friendly"),
                    ("pet", "Pet-Friendly"),
                    ("deluxe suite", "Deluxe Suite"),
                    ("deluxe", "Deluxe Suite")
                ]
                
                for input_type, expected_type in room_type_tests:
                    result = await create_booking(
                        guest_name="Bob Johnson",
                        guest_email="bob.johnson@example.com",
                        guest_phone="555-9999",
                        check_in="2024-12-01",
                        check_out="2024-12-03",
                        room_type=input_type,
                        adults=2
                    )
                    
                    assert result['success'] is True
                    assert result['room_type'] == expected_type


class TestVoiceAIIntegrationEndToEnd:
    """Test end-to-end voice AI integration"""
    
    @pytest.mark.asyncio
    async def test_complete_booking_flow(self):
        """Test complete booking flow from availability check to booking creation"""
        # Step 1: Check availability
        with patch('packages.tools.check_availability.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_session = Mock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_db_manager.return_value = mock_db
            
            with patch('packages.tools.check_availability.AvailabilityService') as mock_service_class:
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
                
                availability_result = await check_availability(
                    check_in="2024-12-01",
                    check_out="2024-12-03",
                    adults=2,
                    pets=False
                )
                
                assert availability_result['available'] is True
                assert len(availability_result['rooms']) == 1
        
        # Step 2: Create booking
        with patch('packages.tools.create_booking.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_session = Mock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_db_manager.return_value = mock_db
            
            with patch('packages.tools.create_booking.BookingService') as mock_service_class:
                mock_service = Mock()
                mock_booking = Mock()
                mock_booking.confirmation_number = "ABC12348"
                mock_booking.guest = Mock()
                mock_booking.guest.first_name = "Alice"
                mock_booking.guest.last_name = "Brown"
                mock_booking.room = Mock()
                mock_booking.room.room_type = "standard_queen"
                mock_booking.check_in_date = date(2024, 12, 1)
                mock_booking.check_out_date = date(2024, 12, 3)
                mock_booking.adults = 2
                mock_booking.pets = False
                mock_booking.total_amount = 240.0
                mock_booking.status = "pending"
                mock_booking.special_requests = None
                mock_booking.created_at = Mock()
                mock_booking.created_at.isoformat.return_value = "2024-10-18T10:00:00"
                
                mock_service.create_booking.return_value = mock_booking
                mock_service_class.return_value = mock_service
                
                booking_result = await create_booking(
                    guest_name="Alice Brown",
                    guest_email="alice.brown@example.com",
                    guest_phone="555-1111",
                    check_in="2024-12-01",
                    check_out="2024-12-03",
                    room_type="Standard Queen",
                    adults=2,
                    pets=False
                )
                
                assert booking_result['success'] is True
                assert booking_result['confirmation_number'] == "ABC12348"
                assert booking_result['total_amount'] == 240.0
