import pytest
import respx
from httpx import Response
from unittest.mock import MagicMock
from nicegui import ui
from nicegui.testing import User
from components.filters import FilterPanel

# Ensure we point to the correct main file relative to pytest.ini
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.nicegui_main_file("build/niceGUI/main.py"),
]


@pytest.fixture
def sample_records():
    return [
        {
            "id": 1,
            "name": "Event A",
            "status": "active",
            "fecha_alta": "2025-01-15T10:00:00Z",
            "fecha_baja": None,
        },
        {
            "id": 2,
            "name": "Event B",
            "status": "inactive",
            "fecha_alta": "2025-02-20T11:00:00Z",
            "fecha_baja": "2025-08-01T11:00:00Z",
        },
        {
            "id": 3,
            "name": "Event C",
            "status": "active",
            "fecha_alta": "2025-03-25T12:00:00Z",
            "fecha_baja": None,
        },
    ]


@pytest.fixture
async def filter_panel_context(user: User, sample_records):
    # --- SETUP: Mock the Login API Call ---
    # The frontend needs these responses to successfully log the user in.
    mock_api_url = "http://localhost:3001"

    with respx.mock(base_url=mock_api_url) as mock:
        # After the rpc_login refactor (audit item #3a), the login view
        # makes one POST /rpc/rpc_login call instead of fetching usuarios,
        # usuario_credenciales, usuario_roles and roles separately as
        # web_anon.
        mock.post("/rpc/rpc_login").mock(
            return_value=Response(
                200,
                json=[{"user_id": 1, "alias": "sumate", "roles": ["admin"]}],
            )
        )

        # --- ACTION: Perform Real Login via UI ---
        await user.open("/login")
        user.find("Username").type("sumate")
        # Use a dummy password. The login is mocked and does not use a real credential.
        user.find("Password").type("test-password")
        user.find("Log in").click()

        # After the login click, the authentication cookie is set. We do not need to
        # wait for the intermediate home page ('/') to fully render, as this was
        # the source of the race condition. We can immediately navigate to the
        # target test page, which will be accessed with the now-authenticated session.
        # This avoids the fragile wait and makes the test more direct and robust.

        # --- SETUP: Create the Test Page ---
        mock_callback = MagicMock()
        panel = FilterPanel(records=sample_records, on_filter_change=mock_callback)

        @ui.page("/test_filters")
        def test_page():
            panel.create()

        # --- ACTION: Open the Test Page (Authenticated) ---
        await user.open("/test_filters")
        await user.should_see("Búsqueda rápida")  # Wait for panel to render

        return panel, mock_callback


async def test_filter_panel_initialization(filter_panel_context):
    panel, _ = filter_panel_context
    assert "global_search" in panel.inputs
    assert "status" in panel.inputs
    assert panel.date_field_select is not None


async def test_on_date_change_emits_correct_event(filter_panel_context):
    panel, mock_callback = filter_panel_context

    # Simulate UI interactions directly on the python objects
    panel._on_date_field_select(MagicMock(value="fecha_alta"))
    panel._on_date_change(part="start", value="2025-01-01")

    mock_callback.assert_called()
    args, _ = mock_callback.call_args
    assert args[0] == "date_range_fecha_alta"
    assert args[1]["start"] == "2025-01-01"

    panel._on_date_change(part="end", value="2025-03-31")
    args, _ = mock_callback.call_args
    assert args[1]["end"] == "2025-03-31"


async def test_selecting_new_date_field_clears_old_filter(filter_panel_context):
    panel, mock_callback = filter_panel_context
    panel._on_date_field_select(MagicMock(value="fecha_alta"))
    panel._on_date_change(part="start", value="2025-01-01")

    panel._on_date_field_select(MagicMock(value="fecha_baja"))
    mock_callback.assert_any_call("date_range_fecha_alta", None)
    assert panel.selected_date_column == "fecha_baja"


async def test_clearing_date_field_selection(filter_panel_context):
    panel, mock_callback = filter_panel_context
    panel._on_date_field_select(MagicMock(value="fecha_alta"))
    panel._on_date_change(part="start", value="2025-01-01")

    panel._on_date_field_select(MagicMock(value=None))
    mock_callback.assert_called_with("date_range_fecha_alta", None)
    assert panel.selected_date_column is None
