"""Utility helpers for creating Stripe payment links."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def generate_payment_link(
    amount_cents: int,
    description: str,
    customer_email: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a payment link using Stripe if configured, otherwise fallback."""

    if amount_cents <= 0:
        raise ValueError("amount_cents must be positive")

    stripe_api_key = os.getenv("STRIPE_API_KEY")
    stripe_account = os.getenv("STRIPE_ACCOUNT_ID")

    if stripe_api_key:
        try:
            import stripe  # type: ignore

            stripe.api_key = stripe_api_key
            if stripe_account:
                stripe.Account.retrieve(stripe_account)  # validate account

            params: Dict[str, Any] = {
                "line_items": [
                    {
                        "price_data": {
                            "currency": os.getenv("STRIPE_CURRENCY", "usd"),
                            "product_data": {"name": description[:100]},
                            "unit_amount": amount_cents,
                        },
                        "quantity": 1,
                    }
                ],
                "allow_promotion_codes": True,
            }

            if customer_email:
                params["customer_email"] = customer_email

            if metadata:
                params["metadata"] = metadata

            payment_link = stripe.PaymentLink.create(**params)
            return {
                "id": payment_link.get("id"),
                "url": payment_link.get("url"),
                "amount_cents": amount_cents,
                "provider": "stripe",
            }

        except Exception as exc:  # pragma: no cover - network/stripe errors
            logger.warning("Stripe payment link generation failed: %s", exc, exc_info=True)

    slug = description.replace(" ", "-").lower()
    fallback_id = uuid.uuid4().hex[:8]
    domain = os.getenv("FAKE_PAYMENT_LINK_DOMAIN", "https://example-payments.local")
    url = f"{domain}/{slug}-{amount_cents}-{fallback_id}"

    return {
        "id": fallback_id,
        "url": url,
        "amount_cents": amount_cents,
        "provider": "mock",
    }
