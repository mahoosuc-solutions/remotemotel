#!/usr/bin/env python3
"""Seed database with sample hotel data"""
import os
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.hotel.models import (
    Base, Room, RoomRate, RoomAvailability,
    RoomType, RateType, HotelSettings
)


def get_database_url():
    """Get database URL from environment with fallback for Codespaces."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback for Codespaces
        db_url = "postgresql://stayhive:stayhive@localhost:5433/stayhive"
        print(f"⚠️  DATABASE_URL not set, using default: {db_url}")
    return db_url


def seed_database():
    db_url = get_database_url()
    engine = create_engine(db_url)
    # Don't create tables - use Alembic migrations instead
    # Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Create hotel settings (key-value format)
        settings_data = {
            "hotel_name": ("RemoteMotel", "string", "Hotel name", "general"),
            "hotel_code": ("RM001", "string", "Hotel code", "general"),
            "currency": ("USD", "string", "Currency code", "general"),
            "timezone": ("America/New_York", "string", "Timezone", "general"),
            "check_in_time": ("15:00", "string", "Check-in time", "policies"),
            "check_out_time": ("11:00", "string", "Check-out time", "policies"),
            "cancellation_policy": ("Free cancellation up to 24 hours before check-in", "string", "Cancellation policy", "policies"),
            "pet_policy": ("Pets allowed in designated rooms with $20/night fee", "string", "Pet policy", "policies"),
            "parking_policy": ("Free on-site parking available", "string", "Parking policy", "policies"),
            "wifi_policy": ("Complimentary high-speed WiFi in all rooms", "string", "WiFi policy", "policies"),
        }

        for key, (value, setting_type, description, category) in settings_data.items():
            setting = HotelSettings(
                setting_key=key,
                setting_value=value,
                setting_type=setting_type,
                description=description,
                category=category
            )
            session.add(setting)

        # 2. Create rooms
        rooms_data = [
            # Standard Queen Rooms (5 rooms)
            {"number": "101", "type": RoomType.STANDARD_QUEEN, "floor": 1, "pets": False},
            {"number": "102", "type": RoomType.STANDARD_QUEEN, "floor": 1, "pets": False},
            {"number": "103", "type": RoomType.STANDARD_QUEEN, "floor": 1, "pets": False},
            {"number": "201", "type": RoomType.STANDARD_QUEEN, "floor": 2, "pets": False},
            {"number": "202", "type": RoomType.STANDARD_QUEEN, "floor": 2, "pets": False},

            # King Suites (3 rooms)
            {"number": "104", "type": RoomType.KING_SUITE, "floor": 1, "pets": False},
            {"number": "203", "type": RoomType.KING_SUITE, "floor": 2, "pets": False},
            {"number": "204", "type": RoomType.KING_SUITE, "floor": 2, "pets": False},

            # Pet-Friendly Rooms (2 rooms)
            {"number": "105", "type": RoomType.PET_FRIENDLY, "floor": 1, "pets": True},
            {"number": "205", "type": RoomType.PET_FRIENDLY, "floor": 2, "pets": True},
        ]

        rooms = []
        for room_data in rooms_data:
            room = Room(
                room_number=room_data["number"],
                room_type=room_data["type"],
                floor=room_data["floor"],
                max_occupancy=2 if room_data["type"] == RoomType.STANDARD_QUEEN else 4,
                max_adults=2,
                max_children=2,
                pet_friendly=room_data["pets"],
                smoking_allowed=False,
                amenities=["WiFi", "TV", "Coffee Maker", "Mini Fridge"],
                square_footage=250 if room_data["type"] == RoomType.STANDARD_QUEEN else 400,
                bed_configuration="1 Queen" if room_data["type"] == RoomType.STANDARD_QUEEN else "1 King",
                description=f"{room_data['type'].value.replace('_', ' ').title()} - Comfortable room"
            )
            session.add(room)
            rooms.append(room)

        session.flush()  # Get room IDs

        # 3. Create rates
        today = date.today()
        end_date = today + timedelta(days=365)

        rate_configs = {
            RoomType.STANDARD_QUEEN: Decimal('120.00'),
            RoomType.KING_SUITE: Decimal('180.00'),
            RoomType.PET_FRIENDLY: Decimal('140.00')
        }

        for room in rooms:
            base_rate = rate_configs[room.room_type]

            # Standard rate
            rate = RoomRate(
                room_id=room.id,
                rate_type=RateType.STANDARD,
                base_rate=base_rate,
                effective_date=today,
                end_date=end_date,
                min_nights=1,
                max_nights=30
            )
            session.add(rate)

            # Weekend rate (20% higher)
            weekend_rate = RoomRate(
                room_id=room.id,
                rate_type=RateType.WEEKEND,
                base_rate=base_rate * Decimal('1.2'),
                effective_date=today,
                end_date=end_date,
                min_nights=1,
                max_nights=30
            )
            session.add(weekend_rate)

        session.flush()

        # 4. Create availability for next 90 days
        for room in rooms:
            for day_offset in range(90):
                avail_date = today + timedelta(days=day_offset)
                availability = RoomAvailability(
                    room_id=room.id,
                    date=avail_date,
                    total_inventory=1,
                    booked_count=0,
                    available_count=1,
                    available=True,
                    maintenance=False
                )
                session.add(availability)

        session.commit()

        print("✓ Database seeded successfully!")
        print(f"  - Created {len(rooms)} rooms")
        print(f"  - Created {len(rooms) * 2} rates")
        print(f"  - Created {len(rooms) * 90} availability records")

    except Exception as e:
        session.rollback()
        print(f"✗ Error seeding database: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
