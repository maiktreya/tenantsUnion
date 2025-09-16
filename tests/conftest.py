import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock

import sys
from pathlib import Path

# --- ROBUST FIX ---
# Point sys.path directly to the application's source directory.
# This makes all imports within the tests and the app itself resolve correctly.
SRC_DIR = Path(__file__).parent.parent / 'build' / 'niceGUI'
sys.path.insert(0, str(SRC_DIR))
# --- END FIX ---

from tests.debug_client import DebugAPIClient
# Imports can now be made directly, as if we were inside the `niceGUI` directory
from main import app as nicegui_app
from nicegui import ui

# =====================================================================
# Fixtures for API Client Testing
# =====================================================================


@pytest.fixture
def mock_api_url() -> str:
    """Provides a consistent mock URL for the API."""
    return "http://test-api:3000"


@pytest.fixture
def api_client(mock_api_url: str) -> DebugAPIClient:
    """
    Provides an instance of the DebugAPIClient, configured to use the mock URL.
    This is used for unit-testing components that depend on the API client.
    """
    client = DebugAPIClient(base_url=mock_api_url)
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
