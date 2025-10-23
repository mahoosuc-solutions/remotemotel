import os

import pytest

from packages.tools import generate_payment_link


def test_generate_payment_link_fallback(monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    result = generate_payment_link.generate_payment_link(1000, "Test Payment")
    assert result["provider"] == "mock"
    assert result["url"].startswith("https://")


def test_generate_payment_link_validation():
    with pytest.raises(ValueError):
        generate_payment_link.generate_payment_link(0, "Invalid")
