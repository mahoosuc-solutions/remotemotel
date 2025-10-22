"""
HTTP API for the StayHive MCP server.

Exposes REST endpoints so external services (e.g. voice agent) can
access availability and other hotel intelligence with consistent
validation, tracing, and error semantics.
"""
import uuid
from datetime import date
from typing import Literal, Optional

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mcp_servers.stayhive import tools


app = FastAPI(
    title="StayHive MCP API",
    version="0.1.0",
    description="Enterprise endpoints for West Bethel Motel operations.",
)

logger = logging.getLogger("stayhive.api")


class AvailabilityRequest(BaseModel):
    check_in: date = Field(description="Check-in date (YYYY-MM-DD)")
    check_out: date = Field(description="Check-out date (YYYY-MM-DD)")
    adults: int = Field(default=2, ge=1, description="Number of adult guests")
    pets: bool = Field(default=False, description="Whether the guest is traveling with pets")
    room_type: Optional[str] = Field(
        default=None,
        description="Preferred room type (Standard Queen, King Suite, Pet-Friendly Room)",
    )
    channel: str = Field(default="voice", description="Requesting channel (voice, chat, web, etc.)")
    session_id: Optional[str] = Field(
        default=None,
        description="Unique session identifier for tracing across systems",
    )


class AvailabilityRoom(BaseModel):
    type: str
    available: int = Field(ge=0)
    rate: float = Field(ge=0)
    currency: Literal["USD"] = "USD"
    total: Optional[float] = None
    pet_fee: Optional[float] = None


class AvailabilityResponse(BaseModel):
    status: Literal["success", "unavailable"]
    request_id: str
    available: bool
    nights: int
    currency: Literal["USD"]
    quote_total: float
    rooms: list[AvailabilityRoom]
    request: dict
    metadata: dict


@app.post("/availability", response_model=AvailabilityResponse, tags=["availability"])
async def post_availability(payload: AvailabilityRequest) -> AvailabilityResponse:
    """
    Availability endpoint backed by the `check_availability` MCP tool.
    """
    request_id = str(uuid.uuid4())
    logger.info(
        "availability_request_received",
        extra={
            "request_id": request_id,
            "check_in": str(payload.check_in),
            "check_out": str(payload.check_out),
            "adults": payload.adults,
            "pets": payload.pets,
            "channel": payload.channel,
            "session_id": payload.session_id,
        },
    )

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                tools.check_availability_sync,
                str(payload.check_in),
                str(payload.check_out),
                payload.adults,
                payload.pets,
            ),
            timeout=3.0,
        )
    except asyncio.TimeoutError as exc:
        logger.error(
            "availability_request_timeout",
            extra={"request_id": request_id},
        )
        raise HTTPException(
            status_code=504,
            detail={
                "code": "availability_timeout",
                "message": "Availability lookup exceeded time limit. Please try again.",
            },
        ) from exc
    except Exception as exc:
        logger.exception(
            "availability_request_error",
            extra={"request_id": request_id},
        )
        raise HTTPException(
            status_code=502,
            detail={
                "code": "availability_error",
                "message": "Unable to retrieve availability at this time.",
            },
        ) from exc

    if error := result.get("error"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_dates",
                "message": error,
            },
        )

    rooms: list[AvailabilityRoom] = []
    for room in result.get("rooms", []):
        rooms.append(
            AvailabilityRoom(
                type=room.get("type", "Unknown"),
                available=int(room.get("available", 0)),
                rate=float(room.get("price_per_night", room.get("rate", 0))),
                total=float(room.get("total_price", 0)) if room.get("total_price") is not None else None,
                pet_fee=float(room.get("pet_fee_per_night")) if room.get("pet_fee_per_night") is not None else None,
            )
        )

    quote_total = sum(filter(None, (room.total for room in rooms)))

    status: Literal["success", "unavailable"] = "success" if result.get("available") else "unavailable"

    response = AvailabilityResponse(
        status=status,
        request_id=request_id,
        available=result.get("available", False),
        nights=result.get("num_nights", 0),
        currency="USD",
        quote_total=quote_total,
        rooms=rooms,
        request={
            "check_in": str(payload.check_in),
            "check_out": str(payload.check_out),
            "adults": payload.adults,
            "pets": payload.pets,
            "room_type": payload.room_type,
            "channel": payload.channel,
            "session_id": payload.session_id,
        },
        metadata={
            "hotel": "West Bethel Motel",
            "location": "West Bethel, ME",
            "source": "stayhive-mcp",
        },
    )

    logger.info(
        "availability_request_completed",
        extra={
            "request_id": request_id,
            "status": response.status,
            "available": response.available,
            "nights": response.nights,
            "quote_total": response.quote_total,
            "room_count": len(response.rooms),
        },
    )

    return response
