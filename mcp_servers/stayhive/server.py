#!/usr/bin/env python3
"""
StayHive MCP Server - Hospitality AI Agent

This MCP server provides tools, resources, and prompts for hotel/motel operations.
It can run standalone locally or connect to BizHive.cloud for analytics and sync.

Usage:
    # Run standalone
    python -m mcp_servers.stayhive.server

    # Run with cloud sync
    BIZHIVE_CLOUD_ENABLED=true BIZHIVE_CLOUD_API_KEY=your_key python -m mcp_servers.stayhive.server
"""
import asyncio
import logging
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types

from . import tools, resources, prompts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("stayhive")

# Initialize MCP server
server = Server("stayhive")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List all available tools for StayHive

    Tools are executable functions that the LLM can call.
    """
    return [
        types.Tool(
            name="check_availability",
            description="Check room availability for specific dates. Returns available room types with pricing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "check_in": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format",
                    },
                    "check_out": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format",
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adult guests",
                        "default": 2,
                    },
                    "pets": {
                        "type": "boolean",
                        "description": "Whether the guest has pets",
                        "default": False,
                    },
                },
                "required": ["check_in", "check_out"],
            },
        ),
        types.Tool(
            name="create_reservation",
            description="Create a new reservation for a guest. Returns confirmation with reservation ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "guest_name": {
                        "type": "string",
                        "description": "Full name of the guest",
                    },
                    "guest_email": {
                        "type": "string",
                        "description": "Guest email address",
                    },
                    "guest_phone": {
                        "type": "string",
                        "description": "Guest phone number",
                    },
                    "check_in": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format",
                    },
                    "check_out": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format",
                    },
                    "room_type": {
                        "type": "string",
                        "description": "Type of room (Standard Queen, King Suite, Pet-Friendly Room)",
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adults",
                        "default": 2,
                    },
                    "pets": {
                        "type": "boolean",
                        "description": "Whether guest has pets",
                        "default": False,
                    },
                },
                "required": ["guest_name", "guest_email", "guest_phone", "check_in", "check_out", "room_type"],
            },
        ),
        types.Tool(
            name="create_lead",
            description="Create a guest lead for follow-up. Use when guest shows interest but isn't ready to book.",
            inputSchema={
                "type": "object",
                "properties": {
                    "full_name": {
                        "type": "string",
                        "description": "Guest's full name",
                    },
                    "email": {
                        "type": "string",
                        "description": "Guest email address",
                    },
                    "phone": {
                        "type": "string",
                        "description": "Guest phone number",
                    },
                    "channel": {
                        "type": "string",
                        "description": "How they contacted us (chat, phone, email, web)",
                        "default": "chat",
                    },
                    "interest": {
                        "type": "string",
                        "description": "What they're interested in or asking about",
                        "default": "",
                    },
                },
                "required": ["full_name", "email", "phone"],
            },
        ),
        types.Tool(
            name="generate_payment_link",
            description="Generate a secure payment link for deposits or full payment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount_cents": {
                        "type": "integer",
                        "description": "Amount in cents (e.g., 20000 = $200.00)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Payment description (e.g., 'Deposit for June 1-3 reservation')",
                    },
                    "reservation_id": {
                        "type": "string",
                        "description": "Optional reservation ID to associate payment with",
                    },
                },
                "required": ["amount_cents", "description"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution

    Routes tool calls to appropriate functions.
    """
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        if name == "check_availability":
            result = await tools.check_availability(**arguments)
        elif name == "create_reservation":
            result = await tools.create_reservation(**arguments)
        elif name == "create_lead":
            result = await tools.create_lead(**arguments)
        elif name == "generate_payment_link":
            result = await tools.generate_payment_link(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        # Return result as JSON text content
        import json
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        error_result = {
            "success": False,
            "error": str(e),
            "message": f"Error executing {name}: {str(e)}"
        }
        import json
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List all available resources for StayHive

    Resources provide data that can be loaded into LLM context.
    """
    return [
        types.Resource(
            uri="stayhive://hotel_policies",
            name="Hotel Policies",
            description="Complete hotel policies including check-in/out, pets, cancellation, etc.",
            mimeType="application/json",
        ),
        types.Resource(
            uri="stayhive://room_information",
            name="Room Information",
            description="Detailed information about all room types, features, and pricing",
            mimeType="application/json",
        ),
        types.Resource(
            uri="stayhive://amenities",
            name="Property Amenities",
            description="All property amenities including breakfast, WiFi, parking, accessibility",
            mimeType="application/json",
        ),
        types.Resource(
            uri="stayhive://local_area_guide",
            name="Local Area Guide",
            description="Guide to Bethel, Maine area including attractions, restaurants, and services",
            mimeType="application/json",
        ),
        types.Resource(
            uri="stayhive://seasonal_information",
            name="Seasonal Information",
            description="Season-specific information and recommendations for visitors",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """
    Handle resource reading

    Retrieves resource data based on URI.
    """
    logger.info(f"Resource requested: {uri}")

    try:
        resource_map = {
            "stayhive://hotel_policies": resources.get_hotel_policies,
            "stayhive://room_information": resources.get_room_information,
            "stayhive://amenities": resources.get_amenities,
            "stayhive://local_area_guide": resources.get_local_area_guide,
            "stayhive://seasonal_information": resources.get_seasonal_information,
        }

        if uri not in resource_map:
            raise ValueError(f"Unknown resource: {uri}")

        resource_func = resource_map[uri]
        result = await resource_func()

        import json
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
        import json
        return json.dumps({
            "error": str(e),
            "message": f"Error reading resource {uri}"
        })


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List all available prompts for StayHive

    Prompts are reusable templates for common interactions.
    """
    return [
        types.Prompt(
            name="guest_greeting",
            description="Generate a welcoming greeting for guests",
            arguments=[
                types.PromptArgument(
                    name="style",
                    description="Greeting style (friendly, formal, casual)",
                    required=False,
                )
            ],
        ),
        types.Prompt(
            name="availability_inquiry",
            description="Handle room availability inquiries",
        ),
        types.Prompt(
            name="booking_confirmation",
            description="Guide through booking confirmation process",
        ),
        types.Prompt(
            name="pet_policy",
            description="Answer pet policy questions",
        ),
        types.Prompt(
            name="local_recommendations",
            description="Provide local area recommendations",
        ),
        types.Prompt(
            name="problem_resolution",
            description="Handle guest issues and complaints",
        ),
    ]


@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Handle prompt retrieval

    Returns prompt templates based on name and arguments.
    """
    logger.info(f"Prompt requested: {name} with arguments: {arguments}")

    try:
        prompt_map = {
            "guest_greeting": prompts.guest_greeting_prompt,
            "availability_inquiry": prompts.availability_inquiry_prompt,
            "booking_confirmation": prompts.booking_confirmation_prompt,
            "pet_policy": prompts.pet_policy_inquiry_prompt,
            "local_recommendations": prompts.local_recommendations_prompt,
            "problem_resolution": prompts.problem_resolution_prompt,
        }

        if name not in prompt_map:
            raise ValueError(f"Unknown prompt: {name}")

        prompt_func = prompt_map[name]

        # Call prompt function with arguments
        if arguments and name == "guest_greeting":
            prompt_data = await prompt_func(style=arguments.get("style", "friendly"))
        else:
            prompt_data = await prompt_func()

        # Return prompt result
        messages = [
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=prompt_data.get("template", "")
                ),
            )
        ]

        return types.GetPromptResult(
            description=prompt_data.get("name", name),
            messages=messages,
        )

    except Exception as e:
        logger.error(f"Error getting prompt {name}: {e}", exc_info=True)
        # Return error as prompt
        return types.GetPromptResult(
            description=f"Error: {name}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Error loading prompt {name}: {str(e)}"
                    ),
                )
            ],
        )


async def main():
    """Run the StayHive MCP server"""
    logger.info("Starting StayHive MCP Server...")
    logger.info("Local-first operation with optional BizHive.cloud sync")

    # Initialize database
    from mcp_servers.shared.database import DatabaseManager
    db = DatabaseManager(business_module="stayhive")
    db.create_tables()
    logger.info("Database initialized")

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="stayhive",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
