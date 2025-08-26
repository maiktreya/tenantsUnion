#!/usr/bin/env python3
import os
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from nicegui import ui, app
from config import config
from api.client import APIClient
from views.home import HomeView
from views.admin import AdminView
from views.views_explorer import ViewsExplorerView
from views.conflicts import ConflictsView

# This now points to your revised login module
from auth.login import create_login_page

# ---------------------------------------------------------------------
# 1. AUTHENTICATION MIDDLEWARE (Unchanged)
# ---------------------------------------------------------------------

unrestricted_page_routes = {"/login"}


class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware efficiently checks authentication for every request."""

    async def dispatch(self, request: Request, call_next):
        if (
            request.url.path.startswith("/_nicegui")
            or request.url.path in unrestricted_page_routes
        ):
            return await call_next(request)

        if not app.storage.user.get("authenticated", False):
            return RedirectResponse(f"/login?redirect_to={request.url.path}")

        return await call_next(request)


app.add_middleware(AuthMiddleware)

# ---------------------------------------------------------------------
# 2. UPGRADED APPLICATION CLASS
# ---------------------------------------------------------------------


class Application:
    """Main application class with role-based access control."""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.current_view = "home"
        self.view_containers = {}
        self.views = {}
        self.setup_static_files()

    def setup_static_files(self):
        base_dir = Path(__file__).parent
        assets_dir = base_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        (assets_dir / "images").mkdir(exist_ok=True)
        app.add_static_files("/assets", str(assets_dir))

    def has_role(self, required_role: str) -> bool:
        """Checks if the current user has a specific role."""
        user_roles = app.storage.user.get("roles", [])
        return required_role in user_roles

    def show_view(self, view_name: str):
        self.current_view = view_name
        for name, container in self.view_containers.items():
            container.set_visibility(name == view_name)

    def create_header(self):
        """Creates the header with role-based navigation."""
        with ui.header().classes("bg-white shadow-lg"):
            with ui.row().classes("w-full items-center p-2 gap-4"):
                with ui.element("div").classes(
                    "w-1/5 min-w-[200px] max-w-[280px] cursor-pointer"
                ).on("click", lambda: self.show_view("home")):
                    ui.image("/assets/images/logo.png")

                ui.element("div").classes("h-10 w-px bg-gray-300")
                ui.label("Sistema de Gestión").classes(
                    "text-xl font-italic text-gray-400"
                )
                ui.space()

                # Role-aware navigation buttons
                with ui.row().classes("gap-2"):
                    ui.button("Inicio", on_click=lambda: self.show_view("home")).props(
                        "flat color=red-600"
                    )

                    if self.has_role("admin") or self.has_role("Sistemas"):
                        ui.button(
                            "admin BBDD", on_click=lambda: self.show_view("admin")
                        ).props("flat color=red-600")

                    ui.button("Vistas", on_click=lambda: self.show_view("views")).props(
                        "flat color=red-600"
                    )

                    if (
                        self.has_role("admin")
                        or self.has_role("gestor")
                        or self.has_role("Sistemas")
                    ):
                        ui.button(
                            "Conflictos", on_click=lambda: self.show_view("conflicts")
                        ).props("flat color=red-600")

                ui.space()

                with ui.row().classes("items-center"):
                    username = app.storage.user.get("username", "...")
                    roles = ", ".join(app.storage.user.get("roles", []))
                    ui.label(f"User: {username} ({roles})").classes(
                        "mr-2 text-gray-600 text-xs"
                    )

                    def logout():
                        app.storage.user.clear()
                        ui.navigate.to("/login")

                    ui.button(on_click=logout, icon="logout").props(
                        "flat dense round color=red-600"
                    ).tooltip("Cerrar sesión")

    def create_views(self):
        """Creates all application views."""
        self.views["home"] = HomeView(self.show_view)
        self.views["admin"] = AdminView(self.api_client)
        self.views["views"] = ViewsExplorerView(self.api_client)
        self.views["conflicts"] = ConflictsView(self.api_client)

        with ui.column().classes("w-full min-h-screen bg-gray-50"):
            for name, view in self.views.items():
                self.view_containers[name] = ui.column().classes("w-full")
                with self.view_containers[name]:
                    view.create()
        self.show_view("home")

    async def cleanup(self):
        await self.api_client.close()


# ---------------------------------------------------------------------
# 3. APPLICATION ENTRY POINTS AND SHUTDOWN (Unchanged)
# ---------------------------------------------------------------------

app_instance = None
api_singleton = APIClient(config.API_BASE_URL)


@ui.page("/")
def main_page_entry():
    """Main entry point for authenticated users."""
    global app_instance
    app_instance = Application(api_client=api_singleton)
    app_instance.create_header()
    app_instance.create_views()


create_login_page(api_client=api_singleton)


async def shutdown_handler():
    """Handle application shutdown gracefully."""
    global app_instance
    if app_instance:
        await app_instance.cleanup()
    elif api_singleton.client is not None:
        await api_singleton.close()


app.on_shutdown(shutdown_handler)

if __name__ in {"__main__", "__mp_main__"}:
    storage_secret = os.environ.get(
        "NICEGUI_STORAGE_SECRET", "CHANGE_THIS_TO_A_LONG_AND_RANDOM_SECRET_KEY"
    )

    ui.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        title=config.APP_TITLE,
        storage_secret=storage_secret,
    )
