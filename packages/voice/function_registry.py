"""
Function Registry for Realtime API

Registers hotel tools as functions callable by the Realtime API,
converting between OpenAI function calling format and our tool implementations.
"""

import logging
import inspect
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FunctionSchema:
    """Schema for a registered function"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    required_params: List[str]


class FunctionRegistry:
    """
    Registry for functions callable by Realtime API

    Manages the conversion between hotel tools and OpenAI function schemas.
    """

    def __init__(self):
        """Initialize function registry"""
        self.functions: Dict[str, FunctionSchema] = {}
        self.logger = logging.getLogger(f"{__name__}.FunctionRegistry")

    def register(
        self,
        name: str,
        function: Callable,
        description: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a function

        Args:
            name: Function name
            function: Callable function
            description: Function description
            parameters: JSON schema for parameters (auto-generated if None)
        """
        if parameters is None:
            parameters = self._generate_schema(function)

        required = parameters.get("required", [])

        schema = FunctionSchema(
            name=name,
            description=description,
            parameters=parameters,
            function=function,
            required_params=required
        )

        self.functions[name] = schema
        self.logger.info(f"Registered function: {name}")

    def _generate_schema(self, function: Callable) -> Dict[str, Any]:
        """
        Generate JSON schema from function signature

        Args:
            function: Function to analyze

        Returns:
            JSON schema for parameters
        """
        sig = inspect.signature(function)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            # Skip special parameters
            if param_name in ["self", "cls"]:
                continue

            # Determine type
            param_type = "string"  # Default
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"
                elif param.annotation == dict:
                    param_type = "object"

            properties[param_name] = {
                "type": param_type,
                "description": f"Parameter: {param_name}"
            }

            # Check if required (no default value)
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def get_function(self, name: str) -> Optional[FunctionSchema]:
        """
        Get function by name

        Args:
            name: Function name

        Returns:
            FunctionSchema or None
        """
        return self.functions.get(name)

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """
        Get all functions in OpenAI tools format

        Returns:
            List of tool definitions
        """
        tools = []

        for schema in self.functions.values():
            tool = {
                "type": "function",
                "name": schema.name,
                "description": schema.description,
                "parameters": schema.parameters
            }
            tools.append(tool)

        return tools

    async def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a registered function

        Args:
            name: Function name
            arguments: Function arguments

        Returns:
            Function result
        """
        schema = self.functions.get(name)
        if not schema:
            raise ValueError(f"Function not found: {name}")

        self.logger.info(f"Executing {name} with args: {arguments}")

        # Validate required parameters
        for param in schema.required_params:
            if param not in arguments:
                raise ValueError(f"Missing required parameter: {param}")

        # Execute function
        import asyncio
        if asyncio.iscoroutinefunction(schema.function):
            result = await schema.function(**arguments)
        else:
            result = schema.function(**arguments)

        return result

    def list_functions(self) -> List[str]:
        """
        List all registered function names

        Returns:
            List of function names
        """
        return list(self.functions.keys())


def create_hotel_function_registry() -> FunctionRegistry:
    """
    Create a function registry with all hotel tools

    Returns:
        FunctionRegistry with hotel tools registered
    """
    registry = FunctionRegistry()

    # Import hotel tools
    from packages.tools import check_availability, create_lead, generate_payment_link
    from packages.voice.tools import (
        transfer_to_human,
        send_sms_confirmation,
        schedule_callback
    )

    # Register check_availability
    registry.register(
        name="check_availability",
        function=check_availability.check_availability,
        description="Check room availability for given dates and guest count",
        parameters={
            "type": "object",
            "properties": {
                "check_in": {
                    "type": "string",
                    "description": "Check-in date in YYYY-MM-DD format"
                },
                "check_out": {
                    "type": "string",
                    "description": "Check-out date in YYYY-MM-DD format"
                },
                "adults": {
                    "type": "integer",
                    "description": "Number of adults"
                },
                "pets": {
                    "type": "boolean",
                    "description": "Whether guest has pets"
                }
            },
            "required": ["check_in", "check_out", "adults"]
        }
    )

    # Register create_lead
    registry.register(
        name="create_lead",
        function=create_lead.create_lead,
        description="Create a guest inquiry lead for follow-up",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Guest name"
                },
                "phone": {
                    "type": "string",
                    "description": "Guest phone number"
                },
                "email": {
                    "type": "string",
                    "description": "Guest email address"
                },
                "check_in": {
                    "type": "string",
                    "description": "Desired check-in date"
                },
                "check_out": {
                    "type": "string",
                    "description": "Desired check-out date"
                },
                "adults": {
                    "type": "integer",
                    "description": "Number of adults"
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes or special requests"
                }
            },
            "required": ["name", "phone"]
        }
    )

    # Register generate_payment_link
    registry.register(
        name="generate_payment_link",
        function=generate_payment_link.generate_payment_link,
        description="Generate a payment link for booking deposit or full payment",
        parameters={
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Payment amount in USD"
                },
                "description": {
                    "type": "string",
                    "description": "Payment description"
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer email for receipt"
                }
            },
            "required": ["amount", "description"]
        }
    )

    # Register transfer_to_human
    registry.register(
        name="transfer_to_human",
        function=transfer_to_human,
        description="Transfer the call to a human staff member",
        parameters={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Voice session ID"
                },
                "department": {
                    "type": "string",
                    "enum": ["front_desk", "housekeeping", "management", "maintenance"],
                    "description": "Department to transfer to"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for transfer"
                }
            },
            "required": ["session_id", "department"]
        }
    )

    # Register send_sms_confirmation
    registry.register(
        name="send_sms",
        function=send_sms_confirmation,
        description="Send an SMS confirmation to the guest",
        parameters={
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Guest phone number"
                },
                "message": {
                    "type": "string",
                    "description": "Message to send"
                }
            },
            "required": ["phone", "message"]
        }
    )

    # Register schedule_callback
    registry.register(
        name="schedule_callback",
        function=schedule_callback,
        description="Schedule a callback to the guest at a specific time",
        parameters={
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Guest phone number"
                },
                "callback_time": {
                    "type": "string",
                    "description": "Callback time in ISO format"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for callback"
                }
            },
            "required": ["phone", "callback_time"]
        }
    )

    logger.info(f"Hotel function registry created with {len(registry.functions)} functions")
    return registry
