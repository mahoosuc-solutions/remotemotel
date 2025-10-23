import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from packages.voice import workflows


@pytest.mark.asyncio
async def test_create_reservation_with_payment_happy_path(monkeypatch):
    booking_response = {
        "confirmation_number": "RSV-123",
        "check_in": "2025-06-01",
        "total_amount": 360,
    }

    async def fake_create_booking(**kwargs):
        return booking_response | {"success": True}

    monkeypatch.setattr(workflows.create_booking, "create_booking", fake_create_booking)

    payment_link = {"url": "https://example.com/pay", "id": "plink_123"}
    monkeypatch.setattr(
        workflows.generate_payment_link,
        "generate_payment_link",
        lambda **kwargs: payment_link,
    )

    sms_result = {"success": True}
    monkeypatch.setattr(
        workflows,
        "send_sms_confirmation",
        AsyncMock(return_value=sms_result),
    )

    monkeypatch.setattr(
        workflows,
        "format_for_voice",
        AsyncMock(return_value="Reservation confirmed."),
    )

    result = await workflows.create_reservation_with_payment(
        guest_name="John Doe",
        guest_email="john@example.com",
        guest_phone="+15551234567",
        check_in="2025-06-01",
        check_out="2025-06-03",
        room_type="Standard",
        deposit_amount_cents=20000,
    )

    assert result["booking"]["confirmation_number"] == "RSV-123"
    assert result["payment_link"] == payment_link
    workflows.send_sms_confirmation.assert_awaited_once()
    workflows.format_for_voice.assert_awaited_once()


@pytest.mark.asyncio
async def test_schedule_guest_callback_parses_iso(monkeypatch):
    callback_result = {"success": True, "callback_time": "2025-01-01T12:00:00"}
    monkeypatch.setattr(
        workflows,
        "schedule_callback",
        AsyncMock(return_value=callback_result),
    )
    monkeypatch.setattr(
        workflows,
        "send_sms_confirmation",
        AsyncMock(return_value={"success": True}),
    )

    result = await workflows.schedule_guest_callback(
        phone="+15550000000",
        callback_time="2025-01-01T12:00:00",
        reason="Follow up",
        notify_sms=True,
    )

    assert result["callback"] == callback_result
    workflows.schedule_callback.assert_awaited_once()
    workflows.send_sms_confirmation.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_confirmation_notification(monkeypatch):
    monkeypatch.setattr(
        workflows,
        "send_sms_confirmation",
        AsyncMock(return_value={"success": True}),
    )

    result = await workflows.send_confirmation_notification(
        phone="+15550000000",
        message="Thanks for booking!",
    )

    assert result["success"] is True
    workflows.send_sms_confirmation.assert_awaited_once()


@pytest.mark.asyncio
async def test_answer_guest_question(monkeypatch):
    monkeypatch.setattr(
        workflows.search_kb,
        "search_kb",
        AsyncMock(return_value=[{"content": "Check-in is after 4 PM.", "metadata": {"source": "Policies"}}]),
    )

    result = await workflows.answer_guest_question("When is check-in?")
    assert result["success"] is True
    assert "Check-in" in result["voice_summary"]
