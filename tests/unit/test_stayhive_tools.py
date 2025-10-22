"""Unit tests for StayHive MCP tools"""
import pytest
from datetime import date, timedelta
from mcp_servers.stayhive import tools
from tests.fixtures.hotel_data import get_future_dates


@pytest.mark.unit
class TestCheckAvailability:
    """Test the check_availability tool"""

    @pytest.mark.asyncio
    async def test_check_availability_valid_dates(self, test_db):
        """Test checking availability with valid future dates"""
        check_in, check_out = get_future_dates(7, 3)

        result = await tools.check_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            pets=False
        )

        assert result["available"] is True
        assert result["check_in"] == check_in
        assert result["check_out"] == check_out
        assert result["num_nights"] == 3
        assert result["adults"] == 2
        assert result["pets"] is False
        assert len(result["rooms"]) >= 1
        assert all("type" in room for room in result["rooms"])
        assert all("available" in room for room in result["rooms"])
        assert all("price_per_night" in room for room in result["rooms"])

    @pytest.mark.asyncio
    async def test_check_availability_with_pets(self, test_db):
        """Test checking availability with pets"""
        check_in, check_out = get_future_dates(7, 2)

        result = await tools.check_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            pets=True
        )

        assert result["available"] is True
        assert result["pets"] is True
        # Should only return pet-friendly rooms
        pet_rooms = [r for r in result["rooms"] if "Pet-Friendly" in r["type"]]
        assert len(pet_rooms) > 0
        # Should have pet fee
        assert any("pet_fee_per_night" in room for room in pet_rooms)

    @pytest.mark.asyncio
    async def test_check_availability_no_pets_filters_correctly(self, test_db):
        """Test that non-pet requests return non-pet rooms"""
        check_in, check_out = get_future_dates(7, 3)

        result = await tools.check_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            pets=False
        )

        assert result["available"] is True
        # Should return Standard Queen and/or King Suite, not Pet-Friendly
        room_types = [r["type"] for r in result["rooms"]]
        assert any("Standard Queen" in rt or "King Suite" in rt for rt in room_types)

    @pytest.mark.asyncio
    async def test_check_availability_invalid_date_format(self, test_db):
        """Test with invalid date format"""
        result = await tools.check_availability(
            check_in="invalid-date",
            check_out="2025-06-03",
            adults=2,
            pets=False
        )

        assert result["available"] is False
        assert "error" in result
        assert "Invalid date format" in result["error"] or "invalid" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_check_availability_checkout_before_checkin(self, test_db):
        """Test with check-out before check-in"""
        check_in = (date.today() + timedelta(days=10)).isoformat()
        check_out = (date.today() + timedelta(days=7)).isoformat()

        result = await tools.check_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            pets=False
        )

        assert result["available"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_check_availability_same_day_checkout(self, test_db):
        """Test with same-day check-in and check-out"""
        same_date = (date.today() + timedelta(days=7)).isoformat()

        result = await tools.check_availability(
            check_in=same_date,
            check_out=same_date,
            adults=2,
            pets=False
        )

        assert result["available"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_check_availability_long_stay(self, test_db):
        """Test availability for extended stay"""
        check_in, check_out = get_future_dates(14, 14)  # 2 week stay

        result = await tools.check_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            pets=False
        )

        assert result["available"] is True
        assert result["num_nights"] == 14
        assert all("total_price" in room for room in result["rooms"])

    @pytest.mark.asyncio
    async def test_check_availability_default_adults(self, test_db):
        """Test that adults defaults to 2"""
        check_in, check_out = get_future_dates(7, 3)

        result = await tools.check_availability(
            check_in=check_in,
            check_out=check_out
            # adults not specified
        )

        assert result["adults"] == 2


@pytest.mark.unit
class TestCreateReservation:
    """Test the create_reservation tool"""

    @pytest.mark.asyncio
    async def test_create_reservation_success(self, test_db):
        """Test creating a valid reservation"""
        check_in, check_out = get_future_dates(7, 3)

        result = await tools.create_reservation(
            guest_name="John Doe",
            guest_email="john@example.com",
            guest_phone="555-0101",
            check_in=check_in,
            check_out=check_out,
            room_type="Standard Queen",
            adults=2,
            pets=False
        )

        assert result["success"] is True
        assert "reservation_id" in result
        assert result["reservation_id"].startswith("RSV-")
        assert result["guest_name"] == "John Doe"
        assert result["room_type"] == "Standard Queen"
        assert result["num_nights"] == 3
        assert result["total_price"] > 0
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_reservation_with_pets(self, test_db):
        """Test creating reservation with pet fee"""
        check_in, check_out = get_future_dates(7, 2)

        result = await tools.create_reservation(
            guest_name="Jane Smith",
            guest_email="jane@example.com",
            guest_phone="555-0102",
            check_in=check_in,
            check_out=check_out,
            room_type="Pet-Friendly Room",
            adults=1,
            pets=True
        )

        assert result["success"] is True
        # Pet-Friendly Room is $140/night + $20 pet fee = $160/night
        # For 2 nights = $320
        assert result["total_price"] == 320
        assert result["num_nights"] == 2

    @pytest.mark.asyncio
    async def test_create_reservation_pricing_standard_queen(self, test_db):
        """Test pricing calculation for Standard Queen"""
        check_in, check_out = get_future_dates(7, 3)

        result = await tools.create_reservation(
            guest_name="Bob Johnson",
            guest_email="bob@example.com",
            guest_phone="555-0103",
            check_in=check_in,
            check_out=check_out,
            room_type="Standard Queen",
            adults=2,
            pets=False
        )

        # Standard Queen is $120/night × 3 nights = $360
        assert result["total_price"] == 360

    @pytest.mark.asyncio
    async def test_create_reservation_pricing_king_suite(self, test_db):
        """Test pricing calculation for King Suite"""
        check_in, check_out = get_future_dates(14, 5)

        result = await tools.create_reservation(
            guest_name="Alice Williams",
            guest_email="alice@example.com",
            guest_phone="555-0104",
            check_in=check_in,
            check_out=check_out,
            room_type="King Suite",
            adults=2,
            pets=False
        )

        # King Suite is $180/night × 5 nights = $900
        assert result["total_price"] == 900

    @pytest.mark.asyncio
    async def test_create_reservation_unique_ids(self, test_db):
        """Test that each reservation gets a unique ID"""
        check_in, check_out = get_future_dates(7, 3)

        result1 = await tools.create_reservation(
            guest_name="Person One",
            guest_email="person1@example.com",
            guest_phone="555-0201",
            check_in=check_in,
            check_out=check_out,
            room_type="Standard Queen",
            adults=2,
            pets=False
        )

        result2 = await tools.create_reservation(
            guest_name="Person Two",
            guest_email="person2@example.com",
            guest_phone="555-0202",
            check_in=check_in,
            check_out=check_out,
            room_type="King Suite",
            adults=2,
            pets=False
        )

        assert result1["reservation_id"] != result2["reservation_id"]

    @pytest.mark.asyncio
    async def test_create_reservation_invalid_dates(self, test_db):
        """Test reservation with invalid dates"""
        result = await tools.create_reservation(
            guest_name="Test User",
            guest_email="test@example.com",
            guest_phone="555-0999",
            check_in="invalid-date",
            check_out="2025-06-03",
            room_type="Standard Queen",
            adults=2,
            pets=False
        )

        assert result["success"] is False
        assert "error" in result


@pytest.mark.unit
class TestCreateLead:
    """Test the create_lead tool"""

    @pytest.mark.asyncio
    async def test_create_lead_success(self, test_db):
        """Test creating a valid lead"""
        result = await tools.create_lead(
            full_name="David Miller",
            email="david@example.com",
            phone="555-0301",
            channel="chat",
            interest="Looking for room June 1-3"
        )

        assert result["success"] is True
        assert "lead_id" in result
        assert result["lead_id"].startswith("LD-")
        assert "message" in result
        assert "David Miller" in result["message"]

    @pytest.mark.asyncio
    async def test_create_lead_minimal_data(self, test_db):
        """Test creating lead with minimal required data"""
        result = await tools.create_lead(
            full_name="Emma Davis",
            email="emma@example.com",
            phone="555-0302"
        )

        assert result["success"] is True
        assert result["lead_id"].startswith("LD-")

    @pytest.mark.asyncio
    async def test_create_lead_with_detailed_interest(self, test_db):
        """Test lead with detailed interest information"""
        result = await tools.create_lead(
            full_name="Frank Wilson",
            email="frank@example.com",
            phone="555-0303",
            channel="email",
            interest="Interested in group booking for 5 rooms, June 15-20, need accessibility features"
        )

        assert result["success"] is True
        assert result["lead_id"].startswith("LD-")

    @pytest.mark.asyncio
    async def test_create_lead_unique_ids(self, test_db):
        """Test that each lead gets a unique ID"""
        result1 = await tools.create_lead(
            full_name="Lead One",
            email="lead1@example.com",
            phone="555-1001"
        )

        result2 = await tools.create_lead(
            full_name="Lead Two",
            email="lead2@example.com",
            phone="555-1002"
        )

        assert result1["lead_id"] != result2["lead_id"]

    @pytest.mark.asyncio
    async def test_create_lead_different_channels(self, test_db):
        """Test leads from different channels"""
        channels = ["chat", "phone", "email", "web"]

        for idx, channel in enumerate(channels):
            result = await tools.create_lead(
                full_name=f"Customer {idx}",
                email=f"customer{idx}@example.com",
                phone=f"555-040{idx}",
                channel=channel
            )

            assert result["success"] is True


@pytest.mark.unit
class TestGeneratePaymentLink:
    """Test the generate_payment_link tool"""

    @pytest.mark.asyncio
    async def test_generate_payment_link_basic(self):
        """Test generating a basic payment link"""
        result = await tools.generate_payment_link(
            amount_cents=20000,
            description="Deposit for reservation"
        )

        assert result["success"] is True
        assert "payment_id" in result
        assert result["payment_id"].startswith("PAY-")
        assert "url" in result
        assert result["amount_cents"] == 20000
        assert result["amount_dollars"] == 200.00
        assert "expires_in_hours" in result

    @pytest.mark.asyncio
    async def test_generate_payment_link_with_reservation(self):
        """Test generating payment link with reservation ID"""
        result = await tools.generate_payment_link(
            amount_cents=36000,
            description="Full payment for 3 night stay",
            reservation_id="RSV-20250601-ABC123"
        )

        assert result["success"] is True
        assert result["reservation_id"] == "RSV-20250601-ABC123"
        assert result["amount_dollars"] == 360.00

    @pytest.mark.asyncio
    async def test_generate_payment_link_various_amounts(self):
        """Test payment links with different amounts"""
        test_amounts = [
            (5000, 50.00),    # $50
            (10000, 100.00),  # $100
            (25000, 250.00),  # $250
            (100000, 1000.00) # $1000
        ]

        for cents, dollars in test_amounts:
            result = await tools.generate_payment_link(
                amount_cents=cents,
                description=f"Payment of ${dollars}"
            )

            assert result["amount_cents"] == cents
            assert result["amount_dollars"] == dollars

    @pytest.mark.asyncio
    async def test_generate_payment_link_unique_ids(self):
        """Test that each payment link gets unique ID"""
        result1 = await tools.generate_payment_link(
            amount_cents=10000,
            description="Payment 1"
        )

        result2 = await tools.generate_payment_link(
            amount_cents=10000,
            description="Payment 2"
        )

        assert result1["payment_id"] != result2["payment_id"]
        assert result1["url"] != result2["url"]

    @pytest.mark.asyncio
    async def test_generate_payment_link_url_format(self):
        """Test that payment URL has correct format"""
        result = await tools.generate_payment_link(
            amount_cents=15000,
            description="Test payment"
        )

        assert result["url"].startswith("https://")
        assert "pay.stayhive.ai" in result["url"] or "payment" in result["url"].lower()


# Run tests with: pytest tests/unit/test_stayhive_tools.py -v
