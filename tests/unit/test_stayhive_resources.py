"""Unit tests for StayHive MCP resources"""
import pytest
from mcp_servers.stayhive import resources


@pytest.mark.unit
class TestHotelPolicies:
    """Test the hotel policies resource"""

    @pytest.mark.asyncio
    async def test_get_hotel_policies_structure(self):
        """Test that hotel policies returns proper structure"""
        result = await resources.get_hotel_policies()

        assert isinstance(result, dict)
        assert "property_name" in result
        assert "location" in result
        assert "check_in" in result
        assert "check_out" in result
        assert "pet_policy" in result
        assert "cancellation_policy" in result
        assert "parking" in result
        assert "smoking_policy" in result

    @pytest.mark.asyncio
    async def test_check_in_policy_details(self):
        """Test check-in policy has required information"""
        result = await resources.get_hotel_policies()

        check_in = result["check_in"]
        assert "time" in check_in
        assert "policy" in check_in
        assert "4" in check_in["time"] or "16" in check_in["time"]  # 4 PM or 16:00

    @pytest.mark.asyncio
    async def test_pet_policy_details(self):
        """Test pet policy has pricing and rules"""
        result = await resources.get_hotel_policies()

        pet_policy = result["pet_policy"]
        assert "allowed" in pet_policy
        assert "fee_per_night" in pet_policy
        assert "max_pets" in pet_policy
        assert "details" in pet_policy
        assert pet_policy["allowed"] is True
        assert isinstance(pet_policy["fee_per_night"], (int, float))

    @pytest.mark.asyncio
    async def test_cancellation_policy_exists(self):
        """Test cancellation policy information"""
        result = await resources.get_hotel_policies()

        cancellation = result["cancellation_policy"]
        assert isinstance(cancellation, dict)
        assert len(cancellation) > 0


@pytest.mark.unit
class TestRoomInformation:
    """Test the room information resource"""

    @pytest.mark.asyncio
    async def test_get_room_information_returns_list(self):
        """Test that room information returns list of rooms"""
        result = await resources.get_room_information()

        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_room_has_required_fields(self):
        """Test each room has required fields"""
        result = await resources.get_room_information()

        for room in result:
            assert "name" in room
            assert "capacity" in room
            assert "base_price_per_night" in room
            assert "pets_allowed" in room
            assert "features" in room
            assert isinstance(room["features"], list)

    @pytest.mark.asyncio
    async def test_room_pricing_valid(self):
        """Test room pricing is reasonable"""
        result = await resources.get_room_information()

        for room in result:
            price = room["base_price_per_night"]
            assert isinstance(price, (int, float))
            assert price > 0
            assert price < 1000  # Reasonable upper limit

    @pytest.mark.asyncio
    async def test_pet_friendly_room_has_pet_fee(self):
        """Test pet-friendly room includes pet fee"""
        result = await resources.get_room_information()

        pet_rooms = [r for r in result if "pet" in r["name"].lower()]
        assert len(pet_rooms) > 0

        for room in pet_rooms:
            assert room["pets_allowed"] is True
            # Pet-friendly rooms should have pet fee info
            if "pet_fee" in room:
                assert isinstance(room["pet_fee"], (int, float))

    @pytest.mark.asyncio
    async def test_room_features_not_empty(self):
        """Test each room has features listed"""
        result = await resources.get_room_information()

        for room in result:
            assert len(room["features"]) > 0
            # Check features are strings
            assert all(isinstance(f, str) for f in room["features"])


@pytest.mark.unit
class TestAmenities:
    """Test the amenities resource"""

    @pytest.mark.asyncio
    async def test_get_amenities_structure(self):
        """Test amenities resource structure"""
        result = await resources.get_amenities()

        assert isinstance(result, dict)
        assert "included_amenities" in result
        assert "breakfast" in result
        assert "wifi" in result
        assert "parking" in result

    @pytest.mark.asyncio
    async def test_breakfast_information(self):
        """Test breakfast details"""
        result = await resources.get_amenities()

        breakfast = result["breakfast"]
        assert "available" in breakfast
        assert "type" in breakfast
        assert "hours" in breakfast
        assert "items" in breakfast
        assert isinstance(breakfast["items"], list)

    @pytest.mark.asyncio
    async def test_wifi_information(self):
        """Test WiFi details"""
        result = await resources.get_amenities()

        wifi = result["wifi"]
        assert "available" in wifi
        assert "cost" in wifi
        assert wifi["available"] is True

    @pytest.mark.asyncio
    async def test_parking_information(self):
        """Test parking details"""
        result = await resources.get_amenities()

        parking = result["parking"]
        assert "available" in parking
        assert "cost" in parking

    @pytest.mark.asyncio
    async def test_accessibility_information(self):
        """Test accessibility features"""
        result = await resources.get_amenities()

        if "accessibility" in result:
            accessibility = result["accessibility"]
            assert isinstance(accessibility, dict)


@pytest.mark.unit
class TestLocalAreaGuide:
    """Test the local area guide resource"""

    @pytest.mark.asyncio
    async def test_local_area_guide_structure(self):
        """Test local area guide structure"""
        result = await resources.get_local_area_guide()

        assert isinstance(result, dict)
        assert "location" in result
        assert "description" in result
        assert "nearby_attractions" in result
        assert "restaurants" in result
        assert "services" in result

    @pytest.mark.asyncio
    async def test_attractions_have_details(self):
        """Test attractions include necessary details"""
        result = await resources.get_local_area_guide()

        attractions = result["nearby_attractions"]
        assert isinstance(attractions, list)
        assert len(attractions) > 0

        for attraction in attractions:
            assert "name" in attraction
            assert "distance" in attraction
            assert "type" in attraction
            assert "description" in attraction

    @pytest.mark.asyncio
    async def test_restaurants_have_details(self):
        """Test restaurant information"""
        result = await resources.get_local_area_guide()

        restaurants = result["restaurants"]
        assert isinstance(restaurants, list)
        assert len(restaurants) > 0

        for restaurant in restaurants:
            assert "name" in restaurant
            assert "distance" in restaurant
            assert "cuisine" in restaurant

    @pytest.mark.asyncio
    async def test_services_information(self):
        """Test local services information"""
        result = await resources.get_local_area_guide()

        services = result["services"]
        assert isinstance(services, dict)
        # Should have at least a few service types
        assert len(services) >= 3

    @pytest.mark.asyncio
    async def test_transportation_information(self):
        """Test transportation details"""
        result = await resources.get_local_area_guide()

        if "transportation" in result:
            transportation = result["transportation"]
            assert isinstance(transportation, dict)
            # Common transportation fields
            expected_fields = ["airport", "taxi", "car_rental"]
            # At least one should be present
            assert any(field in transportation for field in expected_fields)


@pytest.mark.unit
class TestSeasonalInformation:
    """Test the seasonal information resource"""

    @pytest.mark.asyncio
    async def test_seasonal_information_structure(self):
        """Test seasonal information structure"""
        result = await resources.get_seasonal_information()

        assert isinstance(result, dict)
        assert "seasons" in result
        assert "best_time_to_visit" in result

    @pytest.mark.asyncio
    async def test_all_seasons_present(self):
        """Test all four seasons are included"""
        result = await resources.get_seasonal_information()

        seasons = result["seasons"]
        assert "winter" in seasons
        assert "spring" in seasons
        assert "summer" in seasons
        assert "fall" in seasons

    @pytest.mark.asyncio
    async def test_season_details(self):
        """Test each season has proper details"""
        result = await resources.get_seasonal_information()

        seasons = result["seasons"]
        for season_name, season_data in seasons.items():
            assert "months" in season_data
            assert "highlights" in season_data
            assert "weather" in season_data
            assert "what_to_bring" in season_data
            assert isinstance(season_data["highlights"], list)

    @pytest.mark.asyncio
    async def test_best_time_to_visit(self):
        """Test best time to visit recommendations"""
        result = await resources.get_seasonal_information()

        best_times = result["best_time_to_visit"]
        assert isinstance(best_times, dict)
        assert len(best_times) > 0

        # Should have recommendations for different activities
        for activity, recommendation in best_times.items():
            assert isinstance(recommendation, str)
            assert len(recommendation) > 0


@pytest.mark.unit
class TestResourceRegistry:
    """Test the resource registry"""

    def test_resources_registry_exists(self):
        """Test that RESOURCES registry exists"""
        assert hasattr(resources, "RESOURCES")
        assert isinstance(resources.RESOURCES, dict)

    def test_all_resources_registered(self):
        """Test all expected resources are in registry"""
        expected_resources = [
            "hotel_policies",
            "room_information",
            "amenities",
            "local_area_guide",
            "seasonal_information"
        ]

        for resource_name in expected_resources:
            assert resource_name in resources.RESOURCES

    def test_resource_functions_are_callable(self):
        """Test all registered resources are callable"""
        for resource_name, resource_func in resources.RESOURCES.items():
            assert callable(resource_func)


# Run tests with: pytest tests/unit/test_stayhive_resources.py -v
