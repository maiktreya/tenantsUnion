# tests/conftest.py

import os
import sys
from pathlib import Path

# Add the project's source directory to the Python path
SRC_DIR = Path(__file__).parent.parent / "build" / "niceGUI"
sys.path.insert(0, str(SRC_DIR))

import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock

from debug_client import DebugAPIClient
from nicegui import ui, app
from nicegui.testing import User

# =====================================================================
# Fixtures for API Client Testing
# =====================================================================


@pytest.fixture
def mock_api_url() -> str:
    """Provides a consistent mock URL for the API."""
    return "http://test-api:300"


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


@pytest.fixture(scope="session", autouse=True)
def setup_nicegui_app():
    """
    Ensures the NiceGUI app and routes are properly initialized for testing.
    This fixture runs once per test session and automatically sets up the app.
    """
    # Set environment variable to indicate we're in test mode
    os.environ["TESTING"] = "true"

    # The nicegui.testing User fixture runs main.py via runpy.run_path with
    # run_name='__main__', so ui.run() executes and reads these env vars.
    # They must be set before the user fixture runs.
    os.environ.setdefault("NICEGUI_STORAGE_SECRET", "test-storage-secret")
    os.environ.setdefault("POSTGREST_API_URL", "http://localhost:3001")
    os.environ.setdefault("PGRST_JWT_SECRET", "test-jwt-secret")

    # config.py and token_utils.py were already imported via debug_client
    # at top of this file, so their env-var reads happened before the
    # setdefault calls above. Refresh the cached values.
    from config import config
    config.API_BASE_URL = os.environ["POSTGREST_API_URL"]
    import auth.token_utils
    auth.token_utils.SECRET = os.environ["PGRST_JWT_SECRET"]

    # Import and initialize your main application
    # This should register all your @ui.page decorators
    try:
        from main import (
            main_page_entry,
        )  # This should register your routes

        print("✅ Successfully imported main application")
    except ImportError as e:
        print(f"⚠️ Could not import main application: {e}")
        # If main.py is in a different location, adjust the import
        try:
            import main as main_module

            print("✅ Successfully imported main from main")
        except ImportError as e2:
            print(f"❌ Could not import main application from any location: {e2}")


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
