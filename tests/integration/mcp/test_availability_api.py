import uuid

import pytest
from fastapi.testclient import TestClient

from mcp_servers.stayhive.api import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_availability_success_basic(client):
    payload = {
        "check_in": "2025-10-20",
        "check_out": "2025-10-22",
        "adults": 2,
        "pets": False,
        "channel": "voice",
        "session_id": "test-session-123",
    }

    response = client.post("/availability", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["available"] is True
    assert data["nights"] == 2
    assert data["request"]["check_in"] == payload["check_in"]
    assert data["request"]["check_out"] == payload["check_out"]

    # Validate rooms payload
    assert isinstance(data["rooms"], list)
    assert len(data["rooms"]) >= 1
    sample_room = data["rooms"][0]
    assert {"type", "available", "rate", "currency"} <= sample_room.keys()

    # Ensure we emit a request_id suitable for tracing
    uuid.UUID(data["request_id"])


def test_availability_rejects_invalid_dates(client):
    payload = {
        "check_in": "2025-10-20",
        "check_out": "2025-10-20",
        "adults": 2,
    }

    response = client.post("/availability", json=payload)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "invalid_dates"
    assert "Check-out must be after check-in" in detail["message"]
