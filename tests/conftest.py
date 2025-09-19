# tests/conftest.py

import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock

import sys
from pathlib import Path

# Point sys.path directly to the application's source directory.
SRC_DIR = Path(__file__).parent.parent / "build" / "niceGUI"
sys.path.insert(0, str(SRC_DIR))

from debug_client import DebugAPIClient
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
    This is a convenience pass-through for the official nicegui_client fixture.
    """
    return nicegui_client


# =====================================================================
# Fixtures for Mocking Application State
# =====================================================================


@pytest.fixture
def mocked_app_storage(monkeypatch):
    """
    Mocks the nicegui.app.storage to simulate different user authentication states.
    """
    mock_storage = {"user": {}}
    import nicegui.app as nicegui_app

    monkeypatch.setattr(nicegui_app, "storage", mock_storage)

    def set_user_auth(
        authenticated: bool, username: str = "testuser", roles: list = None
    ):
        if roles is None:
            roles = []
        mock_storage["user"] = {
            "authenticated": authenticated,
            "username": username,
            "roles": roles,
            "user_id": 1,
        }

    return set_user_auth
