import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import voice_ai_server as vas


def test_create_realtime_client_registers_shared_functions(monkeypatch):
    registered = []

    class FakeClient:
        def register_function(self, name, func, description, parameters):
            registered.append(name)

    fake_client = FakeClient()

    fake_registry = SimpleNamespace(
        functions={
            "check_room_availability": SimpleNamespace(
                name="check_room_availability",
                description="Check availability",
                parameters={"type": "object"},
                function=lambda **kwargs: None,
            ),
            "send_sms": SimpleNamespace(
                name="send_sms",
                description="Send SMS",
                parameters={"type": "object"},
                function=lambda **kwargs: None,
            ),
        }
    )

    monkeypatch.setattr(vas, "create_hotel_realtime_client", lambda api_key: fake_client)
    monkeypatch.setattr(vas, "create_hotel_function_registry", lambda: fake_registry)

    client = vas.create_realtime_client()

    assert client is fake_client
    assert registered == ["check_room_availability", "send_sms"]


class StubWebSocket:
    headers = {}

    def __init__(self):
        self.accept_called = False
        self.close_called = False
        self.close_payload = None

    async def accept(self):
        self.accept_called = True

    async def close(self, **kwargs):
        self.close_called = True
        self.close_payload = kwargs


@pytest.mark.asyncio
async def test_handle_media_stream_runs_relay(monkeypatch):
    websocket = StubWebSocket()
    mock_client = AsyncMock()
    mock_client.is_connected = True

    monkeypatch.setattr(vas, "create_realtime_client", lambda: mock_client)
    class FakeRegistry:
        def __init__(self):
            self.functions = {}

        def get_openai_tools(self):
            return []

    monkeypatch.setattr(vas, "create_hotel_function_registry", lambda: FakeRegistry())

    instances = []

    class FakeRelay:
        def __init__(self, twilio_ws, openai_client, **kwargs):
            self.twilio_ws = twilio_ws
            self.openai_client = openai_client
            self.kwargs = kwargs
            self.started = False
            self.stopped = False
            instances.append(self)

        async def start(self):
            self.started = True

        async def stop(self):
            self.stopped = True

    monkeypatch.setattr(vas, "TwilioOpenAIRelay", FakeRelay)
    monkeypatch.setattr(vas, "OPENAI_API_KEY", "test-key")

    await vas.handle_media_stream(websocket)

    assert websocket.accept_called is True
    assert mock_client.connect.await_count == 1
    assert mock_client.disconnect.await_count == 1
    assert len(instances) == 1
    assert instances[0].started is True
    assert instances[0].stopped is True


@pytest.mark.asyncio
async def test_send_session_update_uses_system_message(monkeypatch):
    vas.SYSTEM_MESSAGE = "Custom Instructions"

    class FakeRegistry:
        def get_openai_tools(self):
            return [{"type": "function", "name": "check_room_availability", "parameters": {}}]

        functions = {}

    monkeypatch.setattr(vas, "create_hotel_function_registry", lambda: FakeRegistry())

    class DummyConnection:
        def __init__(self):
            self.sent = None

        async def send(self, payload):
            self.sent = payload

    connection = DummyConnection()

    await vas.send_session_update(connection)

    payload = json.loads(connection.sent)
    assert payload["type"] == "session.update"
    session = payload["session"]
    assert session["instructions"] == "Custom Instructions"
    assert [tool["name"] for tool in session["tools"]] == ["check_room_availability"]
