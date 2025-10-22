"""Test fixtures for hotel/motel data"""
from datetime import date, timedelta


# Sample guest data
SAMPLE_GUESTS = [
    {
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "555-0101",
        "adults": 2,
        "pets": False
    },
    {
        "full_name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "555-0102",
        "adults": 1,
        "pets": True
    },
    {
        "full_name": "Bob Johnson",
        "email": "bob.johnson@example.com",
        "phone": "555-0103",
        "adults": 2,
        "pets": False
    },
]

# Sample date ranges for testing
def get_future_dates(days_ahead: int = 7, num_nights: int = 3):
    """Get a date range in the future"""
    check_in = date.today() + timedelta(days=days_ahead)
    check_out = check_in + timedelta(days=num_nights)
    return check_in.isoformat(), check_out.isoformat()

SAMPLE_DATES = {
    "valid_future": get_future_dates(7, 3),
    "valid_long_stay": get_future_dates(14, 7),
    "valid_weekend": get_future_dates(10, 2),
    "invalid_past": ("2020-01-01", "2020-01-03"),
    "invalid_same_day": (date.today().isoformat(), date.today().isoformat()),
    "invalid_reversed": get_future_dates(10, -3),  # Check-out before check-in
}

# Room types
ROOM_TYPES = {
    "standard_queen": {
        "name": "Standard Queen",
        "capacity": 2,
        "base_price": 120,
        "pets_allowed": False
    },
    "king_suite": {
        "name": "King Suite",
        "capacity": 2,
        "base_price": 180,
        "pets_allowed": False
    },
    "pet_friendly": {
        "name": "Pet-Friendly Room",
        "capacity": 2,
        "base_price": 140,
        "pets_allowed": True,
        "pet_fee": 20
    }
}

# Sample availability scenarios
AVAILABILITY_SCENARIOS = [
    {
        "name": "high_availability",
        "check_in": get_future_dates(7, 3)[0],
        "check_out": get_future_dates(7, 3)[1],
        "adults": 2,
        "pets": False,
        "expected_available": True,
        "expected_room_count": 2  # Standard Queen and King Suite
    },
    {
        "name": "with_pets",
        "check_in": get_future_dates(14, 2)[0],
        "check_out": get_future_dates(14, 2)[1],
        "adults": 2,
        "pets": True,
        "expected_available": True,
        "expected_room_count": 1  # Only Pet-Friendly Room
    },
    {
        "name": "single_night",
        "check_in": get_future_dates(21, 1)[0],
        "check_out": get_future_dates(21, 1)[1],
        "adults": 1,
        "pets": False,
        "expected_available": True,
        "expected_room_count": 2
    }
]

# Sample reservation data
SAMPLE_RESERVATIONS = [
    {
        "guest_name": "Alice Williams",
        "guest_email": "alice@example.com",
        "guest_phone": "555-0201",
        "check_in": get_future_dates(7, 3)[0],
        "check_out": get_future_dates(7, 3)[1],
        "room_type": "Standard Queen",
        "adults": 2,
        "pets": False
    },
    {
        "guest_name": "Charlie Brown",
        "guest_email": "charlie@example.com",
        "guest_phone": "555-0202",
        "check_in": get_future_dates(14, 2)[0],
        "check_out": get_future_dates(14, 2)[1],
        "room_type": "Pet-Friendly Room",
        "adults": 1,
        "pets": True
    }
]

# Sample lead data
SAMPLE_LEADS = [
    {
        "full_name": "David Miller",
        "email": "david@example.com",
        "phone": "555-0301",
        "channel": "chat",
        "interest": "Looking for a room June 1-3 with pet"
    },
    {
        "full_name": "Emma Davis",
        "email": "emma@example.com",
        "phone": "555-0302",
        "channel": "phone",
        "interest": "Inquiring about group booking for 5 rooms"
    },
    {
        "full_name": "Frank Wilson",
        "email": "frank@example.com",
        "phone": "555-0303",
        "channel": "email",
        "interest": "Question about ski packages"
    }
]

# Payment link data
SAMPLE_PAYMENT_REQUESTS = [
    {
        "amount_cents": 20000,  # $200 deposit
        "description": "Deposit for June 1-3 reservation",
        "reservation_id": "RSV-20250601-ABC123"
    },
    {
        "amount_cents": 36000,  # $360 full payment
        "description": "Full payment for 3 night stay",
        "reservation_id": "RSV-20250614-XYZ789"
    },
    {
        "amount_cents": 5000,   # $50 cancellation fee
        "description": "Cancellation fee",
        "reservation_id": None
    }
]

# Invalid data for error testing
INVALID_DATA = {
    "invalid_email": [
        "not-an-email",
        "missing@domain",
        "@nodomain.com",
        "spaces in@email.com"
    ],
    "invalid_phone": [
        "123",  # Too short
        "not-a-number",
        "",
    ],
    "invalid_dates": [
        ("2020-01-01", "2020-01-03"),  # Past dates
        ("invalid-date", "2025-06-03"),  # Invalid format
        ("2025-06-03", "2025-06-01"),  # Check-out before check-in
        (date.today().isoformat(), date.today().isoformat()),  # Same day
    ],
    "invalid_room_types": [
        "Luxury Suite",  # Doesn't exist
        "Presidential",
        "",
        None
    ]
}

# Expected error messages
ERROR_MESSAGES = {
    "invalid_date_format": "Invalid date format",
    "checkout_before_checkin": "Check-out must be after check-in",
    "past_dates": "Cannot book dates in the past",
    "invalid_email": "Invalid email address",
    "invalid_phone": "Invalid phone number format",
    "unknown_room_type": "Unknown room type",
    "missing_required_field": "Missing required field"
}
