import pytest

from packages.voice.function_registry import create_hotel_function_registry


@pytest.mark.asyncio
async def test_generate_payment_link_converts_usd(monkeypatch):
    captured = {}

    def fake_generate_payment_link(
        *,
        amount_cents: int,
        description: str,
        customer_email=None,
        metadata=None,
    ):
        captured["amount_cents"] = amount_cents
        captured["description"] = description
        captured["customer_email"] = customer_email
        captured["metadata"] = metadata
        return {
            "id": "plink_123",
            "amount_cents": amount_cents,
            "description": description,
            "metadata": metadata,
        }

    monkeypatch.setattr(
        "packages.tools.generate_payment_link.generate_payment_link",
        fake_generate_payment_link,
    )

    registry = create_hotel_function_registry()

    result = await registry.execute(
        "generate_payment_link",
        {
            "amount_usd": 12.34,
            "description": "Test Deposit",
            "customer_email": "guest@example.com",
            "lead_id": "lead_001",
            "metadata": {"source": "voice"},
        },
    )

    assert captured["amount_cents"] == 1234
    assert captured["metadata"] == {"source": "voice", "lead_id": "lead_001"}
    assert result["amount_cents"] == 1234
