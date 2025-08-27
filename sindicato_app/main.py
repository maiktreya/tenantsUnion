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
from auth.login import create_login_page
from auth.user_management import UserManagementView
from auth.user_profile import UserProfileView

# ---------------------------------------------------------------------
# 1. AUTHENTICATION MIDDLEWARE
# ---------------------------------------------------------------------

unrestricted_page_routes = {'/login'}

class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware efficiently checks authentication for every request."""
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith('/_nicegui') or request.url.path in unrestricted_page_routes:
            return await call_next(request)

        if not app.storage.user.get('authenticated', False):
            return RedirectResponse(f'/login?redirect_to={request.url.path}')

        return await call_next(request)

app.add_middleware(AuthMiddleware)

# ---------------------------------------------------------------------
# 2. FINAL, REFINED APPLICATION CLASS
# ---------------------------------------------------------------------

class Application:
    """Main application class with streamlined and corrected role-based access control."""
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.current_view = "home"
        self.view_containers = {}
        self.views = {}
        self.setup_static_files()

    def setup_static_files(self):
        """Setup static file directories for assets."""
        base_dir = Path(__file__).parent
        assets_dir = base_dir / "assets"
        (assets_dir / "images").mkdir(exist_ok=True)
        app.add_static_files("/assets", str(assets_dir))

    def has_role(self, *roles: str) -> bool:
        """Checks if the current user has any of the specified roles (case-insensitive)."""
        user_roles = {role.lower() for role in app.storage.user.get('roles', [])}
        required_roles = {role.lower() for role in roles}
        return not required_roles.isdisjoint(user_roles)

    def show_view(self, view_name: str):
        """Controls which view is displayed."""
        if view_name not in self.views:
            ui.notify('Acceso no autorizado.', type='negative')
            return

        self.current_view = view_name
        for name, container in self.view_containers.items():
            # Using .visible property for directness and clarity
            container.visible = (name == view_name)

    def create_header(self):
        """Creates the header with role-based navigation."""
        with ui.header().classes("bg-white shadow-lg"):
            with ui.row().classes("w-full items-center p-2 gap-4"):
                # Corrected logo rendering with a context manager
                with ui.element("div").classes("w-1/5 min-w-[200px] max-w-[280px] cursor-pointer").on("click", lambda: self.show_view("home")):
                    ui.image("/assets/images/logo.png")

                ui.element("div").classes("h-10 w-px bg-gray-300")
                ui.label("Sistema de Gestión").classes("text-xl font-italic text-gray-400")
                ui.space()

                # Role-aware navigation buttons
                with ui.row().classes("gap-2"):
                    if self.has_role('admin', 'sistemas'):
                        ui.button("admin BBDD", on_click=lambda: self.show_view("admin")).props("flat color=red-600")
                        ui.button("admin Usuarios", on_click=lambda: self.show_view("user_management")).props("flat color=red-600")

                    if self.has_role('admin', 'gestor', 'sistemas'):
                        ui.button("Vistas", on_click=lambda: self.show_view("views")).props("flat color=red-600")
                        ui.button("Conflictos", on_click=lambda: self.show_view("conflicts")).props("flat color=red-600")


                ui.space()

                # User info and logout
                with ui.row().classes('items-center'):
                    username = app.storage.user.get('username', '...')
                    roles = ", ".join(app.storage.user.get('roles', []))

                    with ui.element().classes('cursor-pointer hover:bg-gray-100 px-2 py-1 rounded').on('click', lambda: self.show_view('user_profile')):
                        ui.label(f"User: {username} ({roles})").classes('mr-2 text-gray-600 text-xs')
                        ui.icon('person', size='sm').classes('text-gray-500').tooltip('Ver mi perfil')

                    def logout():
                        app.storage.user.clear()
                        ui.navigate.to('/login')

                    ui.button(on_click=logout, icon='logout').props('flat dense round color=red-600').tooltip('Cerrar sesión')

    def create_views(self):
        """Creates only the application views authorized for the current user's role."""
        try:
            # HomeView constructor takes only one argument, so we don't pass roles here.
            self.views["home"] = HomeView(self.show_view)
            self.views["views"] = ViewsExplorerView(self.api_client)
        # ADD THIS LINE - All users can access their profile
            self.views["user_profile"] = UserProfileView(self.api_client)

            if self.has_role('admin', 'sistemas'):
                self.views["admin"] = AdminView(self.api_client)
                self.views["user_management"] = UserManagementView(self.api_client)

            if self.has_role('admin', 'gestor', 'sistemas'):
                self.views["conflicts"] = ConflictsView(self.api_client)

            with ui.column().classes("w-full min-h-screen bg-gray-50"):
                for name, view in self.views.items():
                    self.view_containers[name] = container = ui.column().classes("w-full")
                    # Initially hide all containers except the one we will show
                    container.visible = False
                    with container:
                        view.create()

            self.show_view("home")
        except Exception as e:
            ui.notify(f"Error fatal al crear las vistas: {e}", type='negative')


    async def cleanup(self):
        """Closes the API client on shutdown."""
        if self.api_client:
            await self.api_client.close()

# ---------------------------------------------------------------------
# 3. APPLICATION LIFECYCLE
# ---------------------------------------------------------------------

app_instance: Application | None = None
api_singleton = APIClient(config.API_BASE_URL)

@ui.page('/')
def main_page_entry():
    """Main entry point for authenticated users."""
    global app_instance
    app_instance = Application(api_client=api_singleton)
    app_instance.create_header()
    app_instance.create_views()

create_login_page(api_client=api_singleton)

# Using the cleaner decorator syntax for the shutdown handler
@app.on_shutdown
async def shutdown_handler():
    """Handle application shutdown gracefully."""
    if app_instance:
        await app_instance.cleanup()
    elif api_singleton and api_singleton.client:
        await api_singleton.close()

# ---------------------------------------------------------------------
# 4. MAIN ENTRY POINT
# ---------------------------------------------------------------------

if __name__ in {"__main__", "__mp_main__"}:
    storage_secret = os.environ.get('NICEGUI_STORAGE_SECRET', 'QTEGUR912430I10U')

    ui.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        title=config.APP_TITLE,
        storage_secret=storage_secret,
        favicon='🎯'
    )