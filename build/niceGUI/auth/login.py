# sindicato_app/auth/login.py

from typing import Optional, List
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from passlib.context import CryptContext
from api.client import APIClient

# Initialize the password context (using bcrypt as in the original)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user_roles(api_client: APIClient, user_id: int) -> List[str]:
    """Fetches the role names for a given user ID."""
    try:
        user_role_links = await api_client.get_records(
            "usuario_roles", {"usuario_id": f"eq.{user_id}"}
        )
        if not user_role_links:
            return []

        role_ids = [link["role_id"] for link in user_role_links]
        if not role_ids:
            return []

        roles_records = await api_client.get_records(
            "roles", {"id": f'in.({",".join(map(str, role_ids))})'}
        )
        return [role.get("nombre", "") for role in roles_records]
    except Exception as e:
        print(f"Error fetching roles: {e}")  # Log error for debugging
        return []


def create_login_page(api_client: APIClient):
    """Factory function to create the login page with role-fetching capabilities."""

    @ui.page("/login")
    async def login_page(redirect_to: str = "/") -> Optional[RedirectResponse]:
        """Login page that authenticates and fetches user roles."""

        async def try_login() -> None:
            if not username.value or not password.value:
                ui.notify("Username and password are required", color="negative")
                return

            user_records = await api_client.get_records(
                "usuarios", {"alias": f"eq.{username.value}"}
            )
            if not user_records:
                ui.notify("Wrong username or password", color="negative")
                return

            user = user_records[0]
            user_id = user["id"]

            cred_records = await api_client.get_records(
                "usuario_credenciales", {"usuario_id": f"eq.{user_id}"}
            )
            if not cred_records:
                ui.notify("Authentication not set up for this user", color="negative")
                return

            stored_hash = cred_records[0]["password_hash"]

            # Verify password using the original bcrypt method
            if pwd_context.verify(password.value, stored_hash):
                # --- NEW: Fetch roles after successful login ---
                roles = await get_user_roles(api_client, user_id)

                app.storage.user.update(
                    {
                        "username": user["alias"],
                        "user_id": user_id,
                        "authenticated": True,
                        "roles": roles,  # Store roles in the session
                    }
                )
                ui.navigate.to(redirect_to)
            else:
                ui.notify("Wrong username or password", color="negative")

        if app.storage.user.get("authenticated", False):
            return RedirectResponse("/")

        with ui.card().classes("absolute-center"):
            ui.label("Gestión Sindicato INQ").classes("text-h6 self-center")
            username = ui.input("Username").on("keydown.enter", try_login)
            password = ui.input(
                "Password", password=True, password_toggle_button=True
            ).on("keydown.enter", try_login)
            ui.button("Log in", on_click=try_login)

        return None
