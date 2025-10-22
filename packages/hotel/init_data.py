"""
Hotel Data Initialization

Initialize the hotel database with sample rooms, rates, and availability data.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from packages.hotel.models import (
    Room, RoomRate, RoomAvailability, HotelSettings,
    RoomType, RateType
)
from mcp_servers.shared.database import DatabaseManager

logger = logging.getLogger(__name__)


def initialize_hotel_data(db_session: Session) -> None:
    """Initialize hotel with sample data"""
    try:
        logger.info("Initializing hotel data...")
        
        # Create rooms
        create_rooms(db_session)
        
        # Create room rates
        create_room_rates(db_session)
        
        # Create availability data
        create_availability_data(db_session)
        
        # Create hotel settings
        create_hotel_settings(db_session)
        
        db_session.commit()
        logger.info("Hotel data initialization completed successfully")
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error initializing hotel data: {e}")
        raise


def create_rooms(db_session: Session) -> None:
    """Create sample rooms"""
    rooms_data = [
        # Standard Queen Rooms
        {"room_number": "101", "room_type": RoomType.STANDARD_QUEEN, "floor": 1, "max_occupancy": 2, "max_adults": 2, "max_children": 2, "pet_friendly": False, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron"], "square_footage": 250, "bed_configuration": "1 Queen", "description": "Comfortable standard room with queen bed"},
        {"room_number": "102", "room_type": RoomType.STANDARD_QUEEN, "floor": 1, "max_occupancy": 2, "max_adults": 2, "max_children": 2, "pet_friendly": False, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron"], "square_footage": 250, "bed_configuration": "1 Queen", "description": "Comfortable standard room with queen bed"},
        {"room_number": "103", "room_type": RoomType.STANDARD_QUEEN, "floor": 1, "max_occupancy": 2, "max_adults": 2, "max_children": 2, "pet_friendly": False, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron"], "square_footage": 250, "bed_configuration": "1 Queen", "description": "Comfortable standard room with queen bed"},
        {"room_number": "201", "room_type": RoomType.STANDARD_QUEEN, "floor": 2, "max_occupancy": 2, "max_adults": 2, "max_children": 2, "pet_friendly": False, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron"], "square_footage": 250, "bed_configuration": "1 Queen", "description": "Comfortable standard room with queen bed"},
        {"room_number": "202", "room_type": RoomType.STANDARD_QUEEN, "floor": 2, "max_occupancy": 2, "max_adults": 2, "max_children": 2, "pet_friendly": False, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron"], "square_footage": 250, "bed_configuration": "1 Queen", "description": "Comfortable standard room with queen bed"},
        
        # King Suite Rooms
        {"room_number": "301", "room_type": RoomType.KING_SUITE, "floor": 3, "max_occupancy": 4, "max_adults": 4, "max_children": 2, "pet_friendly": False, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron", "Mini Fridge", "Sofa"], "square_footage": 400, "bed_configuration": "1 King + Sofa Bed", "description": "Spacious king suite with separate living area"},
        {"room_number": "302", "room_type": RoomType.KING_SUITE, "floor": 3, "max_occupancy": 4, "max_adults": 4, "max_children": 2, "pet_friendly": False, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron", "Mini Fridge", "Sofa"], "square_footage": 400, "bed_configuration": "1 King + Sofa Bed", "description": "Spacious king suite with separate living area"},
        {"room_number": "303", "room_type": RoomType.KING_SUITE, "floor": 3, "max_occupancy": 4, "max_adults": 4, "max_children": 2, "pet_friendly": False, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron", "Mini Fridge", "Sofa"], "square_footage": 400, "bed_configuration": "1 King + Sofa Bed", "description": "Spacious king suite with separate living area"},
        
        # Pet-Friendly Rooms
        {"room_number": "104", "room_type": RoomType.PET_FRIENDLY, "floor": 1, "max_occupancy": 2, "max_adults": 2, "max_children": 2, "pet_friendly": True, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron", "Pet Bowls", "Pet Bed"], "square_footage": 250, "bed_configuration": "1 Queen", "description": "Pet-friendly room with queen bed"},
        {"room_number": "105", "room_type": RoomType.PET_FRIENDLY, "floor": 1, "max_occupancy": 2, "max_adults": 2, "max_children": 2, "pet_friendly": True, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron", "Pet Bowls", "Pet Bed"], "square_footage": 250, "bed_configuration": "1 Queen", "description": "Pet-friendly room with queen bed"},
        {"room_number": "106", "room_type": RoomType.PET_FRIENDLY, "floor": 1, "max_occupancy": 2, "max_adults": 2, "max_children": 2, "pet_friendly": True, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron", "Pet Bowls", "Pet Bed"], "square_footage": 250, "bed_configuration": "1 Queen", "description": "Pet-friendly room with queen bed"},
        
        # Deluxe Suite Rooms
        {"room_number": "401", "room_type": RoomType.DELUXE_SUITE, "floor": 4, "max_occupancy": 6, "max_adults": 6, "max_children": 4, "pet_friendly": False, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron", "Mini Fridge", "Sofa", "Balcony", "Jacuzzi"], "square_footage": 600, "bed_configuration": "1 King + 2 Queen Sofa Beds", "description": "Luxurious deluxe suite with balcony and jacuzzi"},
        {"room_number": "402", "room_type": RoomType.DELUXE_SUITE, "floor": 4, "max_occupancy": 6, "max_adults": 6, "max_children": 4, "pet_friendly": False, "smoking_allowed": False, "amenities": ["WiFi", "TV", "Coffee Maker", "Iron", "Mini Fridge", "Sofa", "Balcony", "Jacuzzi"], "square_footage": 600, "bed_configuration": "1 King + 2 Queen Sofa Beds", "description": "Luxurious deluxe suite with balcony and jacuzzi"},
    ]
    
    for room_data in rooms_data:
        # Check if room already exists
        existing_room = db_session.query(Room).filter(Room.room_number == room_data["room_number"]).first()
        if not existing_room:
            room = Room(**room_data)
            db_session.add(room)
            logger.info(f"Created room {room_data['room_number']} ({room_data['room_type'].value})")
        else:
            logger.info(f"Room {room_data['room_number']} already exists")


def create_room_rates(db_session: Session) -> None:
    """Create sample room rates"""
    today = date.today()
    end_date = today + timedelta(days=365)  # Rates for next year
    
    # Get rooms for each type
    standard_queen_room = db_session.query(Room).filter(Room.room_type == RoomType.STANDARD_QUEEN).first()
    king_suite_room = db_session.query(Room).filter(Room.room_type == RoomType.KING_SUITE).first()
    pet_friendly_room = db_session.query(Room).filter(Room.room_type == RoomType.PET_FRIENDLY).first()
    deluxe_suite_room = db_session.query(Room).filter(Room.room_type == RoomType.DELUXE_SUITE).first()
    
    rates_data = [
        # Standard Queen Rates
        {"room_id": standard_queen_room.id, "rate_type": RateType.STANDARD, "base_rate": Decimal('120.00'), "effective_date": today, "end_date": end_date},
        {"room_id": standard_queen_room.id, "rate_type": RateType.WEEKEND, "base_rate": Decimal('140.00'), "effective_date": today, "end_date": end_date},
        {"room_id": standard_queen_room.id, "rate_type": RateType.PEAK, "base_rate": Decimal('160.00'), "effective_date": today, "end_date": end_date},
        
        # King Suite Rates
        {"room_id": king_suite_room.id, "rate_type": RateType.STANDARD, "base_rate": Decimal('180.00'), "effective_date": today, "end_date": end_date},
        {"room_id": king_suite_room.id, "rate_type": RateType.WEEKEND, "base_rate": Decimal('200.00'), "effective_date": today, "end_date": end_date},
        {"room_id": king_suite_room.id, "rate_type": RateType.PEAK, "base_rate": Decimal('220.00'), "effective_date": today, "end_date": end_date},
        
        # Pet-Friendly Rates
        {"room_id": pet_friendly_room.id, "rate_type": RateType.STANDARD, "base_rate": Decimal('140.00'), "effective_date": today, "end_date": end_date},
        {"room_id": pet_friendly_room.id, "rate_type": RateType.WEEKEND, "base_rate": Decimal('160.00'), "effective_date": today, "end_date": end_date},
        {"room_id": pet_friendly_room.id, "rate_type": RateType.PEAK, "base_rate": Decimal('180.00'), "effective_date": today, "end_date": end_date},
        
        # Deluxe Suite Rates
        {"room_id": deluxe_suite_room.id, "rate_type": RateType.STANDARD, "base_rate": Decimal('220.00'), "effective_date": today, "end_date": end_date},
        {"room_id": deluxe_suite_room.id, "rate_type": RateType.WEEKEND, "base_rate": Decimal('250.00'), "effective_date": today, "end_date": end_date},
        {"room_id": deluxe_suite_room.id, "rate_type": RateType.PEAK, "base_rate": Decimal('280.00'), "effective_date": today, "end_date": end_date},
    ]
    
    for rate_data in rates_data:
        # Check if rate already exists
        existing_rate = db_session.query(RoomRate).filter(
            RoomRate.room_id == rate_data["room_id"],
            RoomRate.rate_type == rate_data["rate_type"],
            RoomRate.effective_date == rate_data["effective_date"]
        ).first()
        
        if not existing_rate:
            rate = RoomRate(**rate_data)
            db_session.add(rate)
            logger.info(f"Created rate for room {rate_data['room_id']}: {rate_data['rate_type'].value} - ${rate_data['base_rate']}")
        else:
            logger.info(f"Rate for room {rate_data['room_id']} ({rate_data['rate_type'].value}) already exists")


def create_availability_data(db_session: Session) -> None:
    """Create availability data for the next 90 days"""
    today = date.today()
    end_date = today + timedelta(days=90)
    
    # Get rooms for each type
    rooms_by_type = {}
    for room_type in RoomType:
        rooms = db_session.query(Room).filter(Room.room_type == room_type).all()
        if rooms:
            rooms_by_type[room_type] = rooms[0]  # Use first room of each type
    
    # Default inventory counts
    inventory_counts = {
        RoomType.STANDARD_QUEEN: 5,
        RoomType.KING_SUITE: 3,
        RoomType.PET_FRIENDLY: 3,
        RoomType.DELUXE_SUITE: 2
    }
    
    current_date = today
    while current_date <= end_date:
        for room_type, room in rooms_by_type.items():
            # Check if availability already exists
            existing_availability = db_session.query(RoomAvailability).filter(
                RoomAvailability.room_id == room.id,
                RoomAvailability.date == current_date
            ).first()
            
            if not existing_availability:
                total_inventory = inventory_counts.get(room_type, 1)
                booked_count = 0  # Start with no bookings
                
                # Add some random bookings for demo purposes
                import random
                if random.random() < 0.3:  # 30% chance of having some bookings
                    booked_count = random.randint(0, min(2, total_inventory))
                
                availability = RoomAvailability(
                    room_id=room.id,
                    date=current_date,
                    total_inventory=total_inventory,
                    booked_count=booked_count,
                    available_count=total_inventory - booked_count,
                    available=total_inventory > booked_count
                )
                db_session.add(availability)
        
        current_date += timedelta(days=1)
    
    logger.info(f"Created availability data from {today} to {end_date}")


def create_hotel_settings(db_session: Session) -> None:
    """Create hotel settings"""
    settings_data = [
        {"setting_key": "hotel_name", "setting_value": "West Bethel Motel", "setting_type": "string", "description": "Hotel name", "category": "general"},
        {"setting_key": "hotel_address", "setting_value": "123 Main Street, Bethel, ME 04217", "setting_type": "string", "description": "Hotel address", "category": "general"},
        {"setting_key": "hotel_phone", "setting_value": "+1 (207) 220-3501", "setting_type": "string", "description": "Hotel phone number", "category": "general"},
        {"setting_key": "check_in_time", "setting_value": "15:00", "setting_type": "string", "description": "Standard check-in time", "category": "policies"},
        {"setting_key": "check_out_time", "setting_value": "11:00", "setting_type": "string", "description": "Standard check-out time", "category": "policies"},
        {"setting_key": "cancellation_hours", "setting_value": "24", "setting_type": "number", "description": "Hours before check-in for free cancellation", "category": "policies"},
        {"setting_key": "pet_fee_per_night", "setting_value": "20.00", "setting_type": "number", "description": "Pet fee per night", "category": "pricing"},
        {"setting_key": "tax_rate", "setting_value": "0.08", "setting_type": "number", "description": "Tax rate (8%)", "category": "pricing"},
        {"setting_key": "resort_fee", "setting_value": "0.00", "setting_type": "number", "description": "Resort fee per night", "category": "pricing"},
        {"setting_key": "max_advance_booking_days", "setting_value": "365", "setting_type": "number", "description": "Maximum days in advance for booking", "category": "policies"},
        {"setting_key": "min_advance_booking_hours", "setting_value": "2", "setting_type": "number", "description": "Minimum hours in advance for booking", "category": "policies"},
    ]
    
    for setting_data in settings_data:
        # Check if setting already exists
        existing_setting = db_session.query(HotelSettings).filter(
            HotelSettings.setting_key == setting_data["setting_key"]
        ).first()
        
        if not existing_setting:
            setting = HotelSettings(**setting_data)
            db_session.add(setting)
            logger.info(f"Created setting: {setting_data['setting_key']} = {setting_data['setting_value']}")
        else:
            logger.info(f"Setting {setting_data['setting_key']} already exists")


def main():
    """Main function to initialize hotel data"""
    try:
        db = DatabaseManager(business_module="hotel")
        db.create_tables()
        
        with db.get_session() as session:
            initialize_hotel_data(session)
        
        print("Hotel data initialization completed successfully!")
        
    except Exception as e:
        print(f"Error initializing hotel data: {e}")
        raise


if __name__ == "__main__":
    main()
