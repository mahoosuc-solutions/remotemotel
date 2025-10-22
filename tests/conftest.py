"""Pytest configuration and shared fixtures"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _ensure_local_site_packages() -> None:
    """Expose the repo's virtualenv site-packages to the test interpreter."""
    project_root = Path(__file__).resolve().parents[1]
    venv_root = project_root / ".venv"
    if not venv_root.exists():
        return

    for candidate in (venv_root / "lib").glob("python*/site-packages"):
        candidate_path = str(candidate)
        if candidate.exists() and candidate_path not in sys.path:
            sys.path.insert(0, candidate_path)


_ensure_local_site_packages()

from packages.voice.dependencies import check_required_dependencies

check_required_dependencies()

from mcp_servers.shared.database import Base, DatabaseManager


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp(prefix="bizhive_test_")
    yield temp_dir
    # Cleanup after all tests
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def test_db(test_data_dir):
    """Create a fresh test database for each test function"""
    db_path = os.path.join(test_data_dir, f"test_{os.getpid()}.db")
    db_url = f"sqlite:///{db_path}"

    # Create database manager
    db_manager = DatabaseManager(db_url=db_url, business_module="stayhive_test")
    db_manager.create_tables()

    yield db_manager

    # Cleanup
    try:
        os.remove(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="function")
def db_session(test_db):
    """Provide a database session for testing"""
    with test_db.get_session() as session:
        yield session


@pytest.fixture
def mock_cloud_sync(monkeypatch):
    """Mock cloud sync to prevent actual API calls during tests"""

    class MockCloudSync:
        def __init__(self, *args, **kwargs):
            self.enabled = kwargs.get('enabled', False)
            self.synced_leads = []
            self.synced_reservations = []
            self.synced_conversations = []

        async def sync_lead(self, lead_data):
            self.synced_leads.append(lead_data)
            return True

        async def sync_reservation(self, reservation_data):
            self.synced_reservations.append(reservation_data)
            return True

        async def sync_conversation(self, session_id, messages, metadata):
            self.synced_conversations.append({
                "session_id": session_id,
                "messages": messages,
                "metadata": metadata
            })
            return True

        async def fetch_knowledge_base_updates(self):
            return None

        async def push_analytics(self, metrics):
            return True

        async def close(self):
            pass

    # Patch the CloudSyncManager
    monkeypatch.setattr(
        "mcp_servers.shared.cloud_sync.CloudSyncManager",
        MockCloudSync
    )

    return MockCloudSync


@pytest.fixture
def sample_guest_data():
    """Provide sample guest data"""
    from tests.fixtures.hotel_data import SAMPLE_GUESTS
    return SAMPLE_GUESTS


@pytest.fixture
def sample_dates():
    """Provide sample date ranges"""
    from tests.fixtures.hotel_data import SAMPLE_DATES, get_future_dates
    return SAMPLE_DATES


@pytest.fixture
def sample_availability_scenarios():
    """Provide availability test scenarios"""
    from tests.fixtures.hotel_data import AVAILABILITY_SCENARIOS
    return AVAILABILITY_SCENARIOS


@pytest.fixture
def sample_reservations():
    """Provide sample reservation data"""
    from tests.fixtures.hotel_data import SAMPLE_RESERVATIONS
    return SAMPLE_RESERVATIONS


@pytest.fixture
def sample_leads():
    """Provide sample lead data"""
    from tests.fixtures.hotel_data import SAMPLE_LEADS
    return SAMPLE_LEADS


@pytest.fixture
def sample_payment_requests():
    """Provide sample payment request data"""
    from tests.fixtures.hotel_data import SAMPLE_PAYMENT_REQUESTS
    return SAMPLE_PAYMENT_REQUESTS


@pytest.fixture
def invalid_data():
    """Provide invalid data for error testing"""
    from tests.fixtures.hotel_data import INVALID_DATA
    return INVALID_DATA


@pytest.fixture(autouse=True)
def disable_cloud_sync_by_default(monkeypatch):
    """Disable cloud sync for all tests by default"""
    monkeypatch.setenv("BIZHIVE_CLOUD_ENABLED", "false")


@pytest.fixture
def enable_cloud_sync(monkeypatch):
    """Enable cloud sync for specific tests"""
    monkeypatch.setenv("BIZHIVE_CLOUD_ENABLED", "true")
    monkeypatch.setenv("BIZHIVE_CLOUD_API_KEY", "test_api_key")
    monkeypatch.setenv("BIZHIVE_CLOUD_URL", "https://test.bizhive.cloud")


# Pytest markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual functions"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for API endpoints and services"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests for complete workflows"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )
    config.addinivalue_line(
        "markers", "quality: AI conversation quality tests"
    )
