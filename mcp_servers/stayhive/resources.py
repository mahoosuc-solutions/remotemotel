"""MCP Resources for StayHive Hospitality Module

Resources are data sources that can be loaded into LLM context.
Think of these as "GET" endpoints that provide information.
"""
from typing import Dict, Any, List
import yaml
import os


def load_config() -> Dict:
    """Load StayHive configuration"""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


async def get_hotel_policies() -> Dict[str, Any]:
    """
    Get hotel policies and rules

    Returns comprehensive hotel policy information
    """
    config = load_config()

    return {
        "property_name": config['business']['name'],
        "location": config['business']['location'],
        "check_in": {
            "time": config['property']['check_in_time'],
            "policy": "Check-in is after 4:00 PM. Early check-in may be available upon request, subject to availability."
        },
        "check_out": {
            "time": config['property']['check_out_time'],
            "policy": "Check-out is by 10:00 AM. Late check-out until 12:00 PM can be arranged for an additional $25, subject to availability."
        },
        "pet_policy": {
            "allowed": True,
            "fee_per_night": 20,
            "max_pets": 2,
            "details": "Pets are welcome! There is a $20 per night fee for each pet. Please inform us at booking so we can assign a pet-friendly room. Maximum 2 pets per room."
        },
        "cancellation_policy": {
            "standard": "Free cancellation up to 48 hours before check-in. Cancellations within 48 hours will forfeit one night's room charge.",
            "peak_season": "During peak season (summer months and holidays), cancellations must be made 7 days in advance for full refund."
        },
        "parking": {
            "available": True,
            "cost": "Free",
            "details": "Complimentary parking available for all guests."
        },
        "smoking_policy": "This is a non-smoking property. Smoking is permitted in designated outdoor areas only.",
        "quiet_hours": "10:00 PM to 8:00 AM",
        "guest_capacity": "Maximum 2 adults per standard room. Children under 12 stay free with parents."
    }


async def get_room_information() -> List[Dict[str, Any]]:
    """
    Get detailed information about room types

    Returns list of available room types with details
    """
    config = load_config()

    rooms = []
    for room in config['property']['room_types']:
        room_info = {
            "name": room['name'],
            "capacity": f"{room['capacity']} adults",
            "base_price_per_night": room['base_price'],
            "pets_allowed": room['pets_allowed'],
            "features": []
        }

        # Add room-specific features
        if room['name'] == "Standard Queen":
            room_info['features'] = [
                "Queen-size bed",
                "Private bathroom",
                "Flat-screen TV",
                "Mini refrigerator",
                "Coffee maker",
                "Free WiFi",
                "Air conditioning/heating"
            ]
        elif room['name'] == "King Suite":
            room_info['features'] = [
                "King-size bed",
                "Separate sitting area",
                "Large private bathroom",
                "Flat-screen TV",
                "Full refrigerator",
                "Microwave",
                "Coffee maker",
                "Free WiFi",
                "Air conditioning/heating",
                "Work desk"
            ]
        elif room['name'] == "Pet-Friendly Room":
            room_info['features'] = [
                "Queen-size bed",
                "Private bathroom",
                "Flat-screen TV",
                "Mini refrigerator",
                "Coffee maker",
                "Free WiFi",
                "Air conditioning/heating",
                "Easy outdoor access",
                "Pet bowls and mat provided"
            ]
            room_info['pet_fee'] = room.get('pet_fee', 0)

        rooms.append(room_info)

    return rooms


async def get_amenities() -> Dict[str, Any]:
    """
    Get property amenities and services

    Returns comprehensive amenity information
    """
    config = load_config()

    return {
        "included_amenities": config['property']['amenities'],
        "breakfast": {
            "available": True,
            "type": "Continental Breakfast",
            "hours": "7:00 AM - 9:30 AM",
            "location": "Lobby area",
            "items": [
                "Fresh coffee and tea",
                "Orange juice",
                "Assorted pastries and bagels",
                "Cereal",
                "Fresh fruit",
                "Yogurt"
            ]
        },
        "wifi": {
            "available": True,
            "cost": "Free",
            "coverage": "Entire property",
            "password": "Available at check-in"
        },
        "parking": {
            "available": True,
            "cost": "Free",
            "type": "Open lot",
            "spaces": "Ample parking for all guests"
        },
        "accessibility": {
            "ada_compliant_rooms": True,
            "elevator": False,
            "ramps": True,
            "accessible_parking": True
        }
    }


async def get_local_area_guide() -> Dict[str, Any]:
    """
    Get local area information and attractions

    Returns guide to nearby attractions, restaurants, and services
    """
    return {
        "location": "Bethel, Maine",
        "description": "Located in the beautiful Western Mountains region of Maine, known for outdoor recreation and natural beauty.",
        "nearby_attractions": [
            {
                "name": "Sunday River Ski Resort",
                "distance": "5 miles",
                "type": "Skiing/Snowboarding",
                "season": "Winter (November - April)",
                "description": "Premier ski resort with 135+ trails and 8 mountain peaks"
            },
            {
                "name": "Grafton Notch State Park",
                "distance": "15 miles",
                "type": "Hiking/Nature",
                "season": "Year-round",
                "description": "Stunning hiking trails, waterfalls, and scenic views"
            },
            {
                "name": "Downtown Bethel",
                "distance": "2 miles",
                "type": "Shopping/Dining",
                "description": "Charming village with local shops, restaurants, and galleries"
            },
            {
                "name": "Bethel Outdoor Adventure",
                "distance": "3 miles",
                "type": "Activities",
                "description": "Kayaking, canoeing, hiking, and mountain biking"
            }
        ],
        "restaurants": [
            {
                "name": "Sunday River Brewing Company",
                "distance": "2 miles",
                "cuisine": "American/Pub",
                "price_range": "$$"
            },
            {
                "name": "22 Broad Street",
                "distance": "2 miles",
                "cuisine": "Fine Dining",
                "price_range": "$$$"
            },
            {
                "name": "Sudbury Inn",
                "distance": "2 miles",
                "cuisine": "American",
                "price_range": "$$"
            }
        ],
        "services": {
            "grocery": "Bethel Village Market - 2 miles",
            "pharmacy": "Walgreens - 3 miles",
            "hospital": "Stephens Memorial Hospital - 3 miles",
            "gas_stations": "Multiple locations within 2 miles"
        },
        "transportation": {
            "airport": "Portland International Jetport - 75 miles (1.5 hours)",
            "bus": "No public transportation available",
            "car_rental": "Available at Portland airport",
            "taxi": "Local taxi services available"
        }
    }


async def get_seasonal_information() -> Dict[str, Any]:
    """
    Get seasonal information and recommendations

    Returns season-specific information for planning
    """
    return {
        "seasons": {
            "winter": {
                "months": "December - March",
                "highlights": [
                    "Skiing and snowboarding at Sunday River",
                    "Snowshoeing and cross-country skiing",
                    "Cozy indoor fireplace activities"
                ],
                "weather": "Cold with snow, average temps 10-30°F",
                "what_to_bring": "Winter clothing, ski gear, warm layers"
            },
            "spring": {
                "months": "April - May",
                "highlights": [
                    "Late-season skiing (early April)",
                    "Maple sugaring season",
                    "Wildlife viewing"
                ],
                "weather": "Cool to mild, 30-60°F, occasional rain",
                "what_to_bring": "Layers, rain jacket, hiking boots"
            },
            "summer": {
                "months": "June - August",
                "highlights": [
                    "Hiking and mountain biking",
                    "Water activities (kayaking, swimming)",
                    "Scenic gondola rides"
                ],
                "weather": "Warm and pleasant, 60-80°F",
                "what_to_bring": "Light clothing, sunscreen, hiking gear"
            },
            "fall": {
                "months": "September - November",
                "highlights": [
                    "Peak fall foliage viewing",
                    "Hiking in crisp weather",
                    "Harvest festivals"
                ],
                "weather": "Cool, 40-65°F, beautiful colors",
                "what_to_bring": "Layers, camera for foliage, hiking boots"
            }
        },
        "best_time_to_visit": {
            "skiing": "December - March",
            "foliage": "Late September - Early October",
            "hiking": "June - October",
            "value": "April - May, November (shoulder seasons)"
        }
    }


# Resource registry for MCP server
RESOURCES = {
    "hotel_policies": get_hotel_policies,
    "room_information": get_room_information,
    "amenities": get_amenities,
    "local_area_guide": get_local_area_guide,
    "seasonal_information": get_seasonal_information
}
