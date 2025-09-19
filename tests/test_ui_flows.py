# tests/test_ui_flows.py

import pytest
import respx
from httpx import Response
from nicegui.testing import Screen

# This import is necessary so pytest can discover the @ui.page decorator
from build.niceGUI.main import main_page_entry

# Marks all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@respx.mock
async def test_successful_login_and_logout(nicegui_client: Screen, mock_api_url: str):
    """
    Tests the full user journey for a successful admin login and logout.
    """
    screen = nicegui_client  # Rename for convenience

    # Arrange: Mock API calls for the 'sumate' (admin) user
    respx.get(f"{mock_api_url}/usuarios?alias=eq.sumate").mock(
        return_value=Response(200, json=[{"id": 1, "alias": "sumate"}])
    )
    respx.get(f"{mock_api_url}/usuario_credenciales?usuario_id=eq.1").mock(
        return_value=Response(
            200,
            json=[
                {
                    "password_hash": "$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6"
                }
            ],
        )
    )
    respx.get(f"{mock_api_url}/usuario_roles?usuario_id=eq.1").mock(
        return_value=Response(200, json=[{"role_id": 1}])
    )
    respx.get(f"{mock_api_url}/roles?id=in.(1)").mock(
        return_value=Response(200, json=[{"id": 1, "nombre": "admin"}])
    )

    # Act & Assert: Login process
    await screen.open("/login")
    await screen.input("Username", "sumate")
    await screen.input("Password", "12345678")
    await screen.click("Log in")

    # Verify home page content
    await screen.should_contain("Bienvenido al Sistema de Gestión")
    await screen.should_contain("User: sumate (admin)")
    await screen.should_contain("Admin BBDD")

    # Act & Assert: Logout process
    await screen.click("logout")
    await screen.should_contain("Log in")
    assert "login" in screen.page.url


@respx.mock
async def test_failed_login_with_wrong_password(
    nicegui_client: Screen, mock_api_url: str
):
    screen = nicegui_client
    """
    Tests for an error notification on failed login.
    """
    # Arrange
    respx.get(f"{mock_api_url}/usuarios?alias=eq.sumate").mock(
        return_value=Response(200, json=[{"id": 1, "alias": "sumate"}])
    )
    respx.get(f"{mock_api_url}/usuario_credenciales?usuario_id=eq.1").mock(
        return_value=Response(
            200,
            json=[
                {
                    "password_hash": "$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6"
                }
            ],
        )
    )

    # Act
    await screen.open("/login")
    await screen.input("Username", "sumate")
    await screen.input("Password", "wrong_password")
    await screen.click("Log in")

    # Assert
    await screen.should_contain("Wrong username or password")
    assert "login" in screen.page.url


@respx.mock
async def test_role_based_access_for_actas_user(
    nicegui_client: Screen, mock_api_url: str
):
    screen = nicegui_client
    """
    Tests that a user with a limited role ('actas') only sees permitted UI elements.
    """
    # Arrange: Mock login sequence for the 'actas' user
    respx.get(f"{mock_api_url}/usuarios?alias=eq.actas").mock(
        return_value=Response(200, json=[{"id": 3, "alias": "actas"}])
    )
    respx.get(f"{mock_api_url}/usuario_credenciales?usuario_id=eq.3").mock(
        return_value=Response(
            200,
            json=[
                {
                    "password_hash": "$2b$12$.2k0jdsNjg6J/lcZL1WBkej85pFdSTq2NWdFBjPgfZ7EXjAbjoSei"
                }
            ],
        )
    )
    respx.get(f"{mock_api_url}/usuario_roles?usuario_id=eq.3").mock(
        return_value=Response(200, json=[{"role_id": 3}])
    )
    respx.get(f"{mock_api_url}/roles?id=in.(3)").mock(
        return_value=Response(200, json=[{"id": 3, "nombre": "actas"}])
    )

    # Act
    await screen.open("/login")
    await screen.input("Username", "actas")
    await screen.input("Password", "12345678")
    await screen.click("Log in")

    # Assert
    await screen.should_contain("Bienvenido al Sistema de Gestión")
    await screen.should_contain("User: actas (actas)")
    await screen.should_contain("Conflictos")
    await screen.should_not_contain("Admin BBDD")
    await screen.should_not_contain("Vistas")
