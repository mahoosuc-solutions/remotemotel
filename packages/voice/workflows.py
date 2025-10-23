"""High-level voice workflows that orchestrate hotel automation tasks."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from packages.knowledge.service import DEFAULT_HOTEL_ID
from packages.tools import create_booking, generate_payment_link, search_kb
from packages.voice.tools import (
    format_for_voice,
    schedule_callback,
    send_sms_confirmation,
)

logger = logging.getLogger(__name__)


async def create_reservation_with_payment(
    guest_name: str,
    guest_email: str,
    guest_phone: str,
    check_in: str,
    check_out: str,
    room_type: str,
    adults: int = 2,
    pets: bool = False,
    special_requests: Optional[str] = None,
    deposit_amount_cents: Optional[int] = None,
    send_sms: bool = True,
    sms_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a reservation, optionally generate payment link, and notify the guest."""

    logger.info("Creating reservation workflow for %s", guest_name)

    booking = await create_booking.create_booking(
        guest_name=guest_name,
        guest_email=guest_email,
        guest_phone=guest_phone,
        check_in=check_in,
        check_out=check_out,
        room_type=room_type,
        adults=adults,
        pets=pets,
        special_requests=special_requests,
    )

    payment_link = None
    if deposit_amount_cents and deposit_amount_cents > 0:
        metadata = {"reservation_id": booking.get("confirmation_number")}
        payment_link = generate_payment_link.generate_payment_link(
            amount_cents=deposit_amount_cents,
            description=f"Deposit for {booking.get('confirmation_number', 'reservation')}",
            customer_email=guest_email,
            metadata=metadata,
        )

    notification = None
    if send_sms and booking.get("confirmation_number"):
        body = sms_message or _build_confirmation_message(booking, payment_link)
        notification = await send_sms_confirmation(
            phone=guest_phone,
            message=body,
        )

    voice_summary = await format_for_voice(
        {
            "confirmation_number": booking.get("confirmation_number"),
            "guest_name": guest_name,
            "check_in": booking.get("check_in"),
            "total_amount": booking.get("total_amount"),
        },
        data_type="reservation",
    )

    return {
        "success": booking.get("success", True),
        "booking": booking,
        "payment_link": payment_link,
        "notification": notification,
        "voice_summary": voice_summary,
    }


async def schedule_guest_callback(
    phone: str,
    callback_time: str,
    reason: Optional[str] = None,
    notify_sms: bool = False,
    sms_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Schedule a callback and optionally notify the guest via SMS."""

    callback_dt = datetime.fromisoformat(callback_time)

    callback = await schedule_callback(
        phone=phone,
        callback_time=callback_dt,
        reason=reason,
    )

    notification = None
    if notify_sms:
        message = sms_message or (
            f"We'll call you back at {callback_dt.strftime('%I:%M %p on %B %d')} "
            "to follow up on your request."
        )
        notification = await send_sms_confirmation(phone=phone, message=message)

    return {
        "success": callback.get("success", True),
        "callback": callback,
        "notification": notification,
    }


async def send_confirmation_notification(
    phone: str,
    message: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a confirmation SMS to the guest."""

    logger.info("Sending confirmation notification to %s", phone)
    return await send_sms_confirmation(phone=phone, message=message, session_id=session_id)


def _build_confirmation_message(booking: Dict[str, Any], payment_link: Optional[Dict[str, Any]]) -> str:
    confirmation = booking.get("confirmation_number", "your upcoming stay")
    check_in = booking.get("check_in")
    total_amount = booking.get("total_amount")

    base_message = f"Reservation {confirmation} confirmed"
    if check_in:
        base_message += f" for {check_in}"
    if total_amount:
        base_message += f". Total due: ${total_amount}"

    if payment_link and payment_link.get("url"):
        base_message += f". Secure payment link: {payment_link['url']}"

    return base_message


async def answer_guest_question(
    question: str,
    hotel_id: str = DEFAULT_HOTEL_ID,
    top_k: int = 3,
) -> Dict[str, Any]:
    """Use the knowledge base to answer a guest question."""

    results = await search_kb.search_kb(question, top_k=top_k, hotel_id=hotel_id)
    if not results:
        return {
            "success": False,
            "voice_summary": "I'm checking on that, but I don't have the information right now. Let me connect you with a staff member.",
            "sources": [],
        }

    top_result = results[0]
    summary = top_result.get("content", "")
    metadata = top_result.get("metadata", {})

    voice_msg = summary
    if metadata.get("source"):
        voice_msg += f" (Source: {metadata['source']})"

    return {
        "success": True,
        "voice_summary": voice_msg,
        "results": results,
    }
