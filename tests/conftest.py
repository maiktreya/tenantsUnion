import pytest
import respx
from httpx import Response, AsyncClient
from unittest.mock import AsyncMock

# Adjust the path to import from the project's source code
import sys
from pathlib import Path

# Add the project root to the Python path to allow imports from 'build'
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.client import APIClient
from build.niceGUI.main import app as nicegui_app
from build.niceGUI.views import HomeView, AdminView
from nicegui import ui

# =====================================================================
# Fixtures for API Client Testing
# =====================================================================


@pytest.fixture
def mock_api_url() -> str:
    """Provides a consistent mock URL for the API."""
    return "http://test-api:3000"


@pytest.fixture
def api_client(mock_api_url: str) -> APIClient:
    """
    Provides an instance of the APIClient, configured to use the mock URL.
    This is used for unit-testing components that depend on the API client.
    """
    # We create a new instance for each test to ensure isolation
    client = APIClient(base_url=mock_api_url)
    # Ensure client is reset for each test run
    client.client = None
    return client


# =====================================================================
# Fixtures for NiceGUI E2E Testing
# =====================================================================


@pytest.fixture
def screen(nicegui_client):
    """
    Provides a 'screen' object for interacting with the NiceGUI UI in tests.
    This fixture is provided by the nicegui.testing module.
    """
    return nicegui_client


# =====================================================================
# Fixtures for Mocking Application State
# =====================================================================


@pytest.fixture
def mocked_app_storage(monkeypatch):
    """
    Mocks the nicegui.app.storage to simulate different user authentication states.
    This is essential for testing role-based access control (RBAC).
    """
    # Mock storage dictionary
    mock_storage = {"user": {}}

    # Use monkeypatch to replace the real app.storage with our mock
    monkeypatch.setattr(nicegui_app, "storage", mock_storage)

    def set_user_auth(
        authenticated: bool, username: str = "testuser", roles: list = None
    ):
        """Helper function to easily set the user's auth state."""
        if roles is None:
            roles = []
        mock_storage["user"] = {
            "authenticated": authenticated,
            "username": username,
            "roles": roles,
            "user_id": 1,
        }

    # The fixture returns the helper function so tests can configure the auth state
    return set_user_auth
