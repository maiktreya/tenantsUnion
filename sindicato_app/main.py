#!/usr/bin/env python3
import os
from pathlib import Path

# These imports are from NiceGUI's underlying framework (Starlette/FastAPI)
# and do not add a separate backend service.
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
# Assumes login.py is in a 'views' folder and has a 'create_login_page' function
from auth.login import create_login_page

# ---------------------------------------------------------------------
# 1. AUTHENTICATION MIDDLEWARE
# This efficiently protects all pages before they are loaded.
# ---------------------------------------------------------------------

# Define routes that do not require a login
unrestricted_page_routes = {'/login'}

class AuthMiddleware(BaseHTTPMiddleware):
    """
    This middleware efficiently checks authentication for every request.
    It runs before any of your page code, preventing unauthorized access
    at the earliest possible moment.
    """
    async def dispatch(self, request: Request, call_next):
        # Allow NiceGUI's internal routes to pass through unrestricted
        if request.url.path.startswith('/_nicegui'):
            return await call_next(request)

        # Allow access to pages specifically marked as unrestricted
        if request.url.path in unrestricted_page_routes:
            return await call_next(request)

        # For all other pages, check if the user is authenticated in their session
        if not app.storage.user.get('authenticated', False):
            # If not authenticated, redirect to the login page
            return RedirectResponse(f'/login?redirect_to={request.url.path}')

        # If authenticated, proceed to the requested page
        return await call_next(request)

# Add the middleware to the NiceGUI application
app.add_middleware(AuthMiddleware)

# ---------------------------------------------------------------------
# 2. YOUR ORIGINAL APPLICATION CLASS
# This remains the same as in your original project.
# ---------------------------------------------------------------------

class Application:
    """Main application class"""
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

    def show_view(self, view_name: str):
        self.current_view = view_name
        for name, container in self.view_containers.items():
            container.set_visibility(name == view_name)

    def create_header(self):
        """Creates the header with navigation and a new logout button."""
        with ui.header().classes("bg-white shadow-lg"):
            with ui.row().classes("w-full items-center p-2 gap-4"):
                with ui.element("div").classes("w-1/5 min-w-[200px] max-w-[280px] cursor-pointer").on("click", lambda: self.show_view("home")):
                    ui.image("/assets/images/logo.png")

                ui.element("div").classes("h-10 w-px bg-gray-300")
                ui.label("Sistema de Gestión").classes("text-xl font-italic text-gray-400")
                ui.space()

                with ui.row().classes("gap-2"):
                    ui.button("Inicio", on_click=lambda: self.show_view("home")).props("flat color=red-600")
                    ui.button("admin BBDD", on_click=lambda: self.show_view("admin")).props("flat color=red-600")
                    ui.button("Vistas", on_click=lambda: self.show_view("views")).props("flat color=red-600")
                    ui.button("Conflictos", on_click=lambda: self.show_view("conflicts")).props("flat color=red-600")

                ui.space()

                with ui.row().classes('items-center'):
                    ui.label(f"User: {app.storage.user.get('username', '...')}").classes('mr-2 text-gray-600')
                    def logout():
                        app.storage.user.clear()
                        ui.navigate.to('/login')
                    ui.button(on_click=logout, icon='logout').props('flat dense round color=red-600').tooltip('Cerrar sesión')

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
# 3. APPLICATION ENTRY POINTS AND SHUTDOWN
# The main UI is now built only *after* authentication is confirmed.
# ---------------------------------------------------------------------

app_instance = None

# Create a single APIClient instance to be shared across the application
api_singleton = APIClient(config.API_BASE_URL)

@ui.page('/')
def main_page_entry():
    """
    This is the main entry point for authenticated users.
    The AuthMiddleware ensures this function only runs if the user is logged in.
    """
    global app_instance
    ui.context.client.clear()
    # Pass the shared API client to the main application
    app_instance = Application(api_client=api_singleton)
    app_instance.create_header()
    app_instance.create_views()

# Use the factory to create and register the login page
create_login_page(api_client=api_singleton)

async def shutdown_handler():
    """Handle application shutdown gracefully."""
    global app_instance
    if app_instance:
        await app_instance.cleanup()
    # The login page's client is the same singleton, so it will be closed by the cleanup above.
    # If the user never logs in, we still need to close it.
    elif not api_singleton.client is None:
         await api_singleton.close()


app.on_shutdown(shutdown_handler)

if __name__ in {"__main__", "__mp_main__"}:
    # IMPORTANT: A storage_secret is required for secure, encrypted user sessions.
    ui.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        title=config.APP_TITLE,
        storage_secret='CHANGE_THIS_TO_A_LONG_AND_RANDOM_SECRET_KEY'
    )