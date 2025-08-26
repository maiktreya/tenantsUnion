#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

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

# ---------------------------------------------------------------------
# LOGGING CONFIGURATION
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            logger.info(f"Unauthenticated access attempt to {request.url.path}")
            return RedirectResponse(f'/login?redirect_to={request.url.path}')

        return await call_next(request)

app.add_middleware(AuthMiddleware)

# ---------------------------------------------------------------------
# 2. ENHANCED APPLICATION CLASS
# ---------------------------------------------------------------------

class Application:
    """Main application class with role-based access control."""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.current_view = "home"
        self.view_containers: Dict[str, ui.column] = {}
        self.views: Dict[str, Any] = {}
        self.navigation_buttons: Dict[str, ui.button] = {}
        self.setup_static_files()
        self.log_user_info()

    def setup_static_files(self):
        """Setup static file directories for assets."""
        try:
            base_dir = Path(__file__).parent
            assets_dir = base_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            (assets_dir / "images").mkdir(exist_ok=True)
            app.add_static_files("/assets", str(assets_dir))
            logger.info(f"Static files configured at {assets_dir}")
        except Exception as e:
            logger.error(f"Error setting up static files: {e}")

    def log_user_info(self):
        """Log current user information for debugging."""
        username = app.storage.user.get('username', 'Unknown')
        roles = app.storage.user.get('roles', [])
        logger.info(f"User '{username}' logged in with roles: {roles}")

    def get_user_roles(self) -> List[str]:
        """Get the current user's roles."""
        return app.storage.user.get('roles', [])

    def has_role(self, required_role: str) -> bool:
        """
        Checks if the current user has a specific role (case-insensitive).

        Args:
            required_role: The role to check for

        Returns:
            bool: True if user has the role, False otherwise
        """
        user_roles = self.get_user_roles()
        has_access = any(role.lower() == required_role.lower() for role in user_roles)

        # Debug logging
        logger.debug(f"Role check: '{required_role}' in {user_roles} = {has_access}")

        return has_access

    def has_any_role(self, *required_roles: str) -> bool:
        """
        Checks if the user has any of the specified roles.

        Args:
            *required_roles: Variable number of roles to check

        Returns:
            bool: True if user has any of the roles
        """
        return any(self.has_role(role) for role in required_roles)

    def show_view(self, view_name: str) -> None:
        """
        Controls which view is displayed with proper error handling.

        Args:
            view_name: The name of the view to display
        """
        if view_name not in self.views:
            logger.warning(f"Attempted to access non-existent or unauthorized view: {view_name}")
            ui.notify('No tiene permisos para acceder a esta sección.', type='warning')
            return

        logger.info(f"Switching to view: {view_name}")
        self.current_view = view_name

        # Update view visibility
        for name, container in self.view_containers.items():
            container.visible = (name == view_name)

        # Update navigation button states
        for btn_name, button in self.navigation_buttons.items():
            if btn_name == view_name:
                button.props('unelevated')
            else:
                button.props('flat')

    def create_header(self) -> None:
        """Creates the header with role-based navigation."""
        with ui.header().classes("bg-white shadow-lg"):
            with ui.row().classes("w-full items-center p-2 gap-4"):
                # Logo and branding
                with ui.element("div").classes("w-1/5 min-w-[200px] max-w-[280px] cursor-pointer"):
                    logo_container = ui.element("div")
                    logo_container.on("click", lambda: self.show_view("home"))
                    with logo_container:
                        # Check if logo exists, otherwise show placeholder
                        logo_path = Path(__file__).parent / "assets" / "images" / "logo.png"
                        if logo_path.exists():
                            ui.image("/assets/images/logo.png")
                        else:
                            ui.label("LOGO").classes("text-xl font-bold text-red-600")

                ui.element("div").classes("h-10 w-px bg-gray-300")
                ui.label("Sistema de Gestión").classes("text-xl font-italic text-gray-400")
                ui.space()

                # Navigation buttons
                with ui.row().classes("gap-2"):
                    # Home button (always visible)
                    self.navigation_buttons["home"] = ui.button(
                        "Inicio",
                        on_click=lambda: self.show_view("home")
                    ).props("flat color=red-600")

                    # Admin BBDD button (admin or Sistemas roles)
                    if self.has_any_role('admin', 'sistemas'):
                        self.navigation_buttons["admin"] = ui.button(
                            "Admin BBDD",
                            on_click=lambda: self.show_view("admin")
                        ).props("flat color=red-600")
                        logger.info("Admin button added to navigation")

                    # Views button (always visible)
                    self.navigation_buttons["views"] = ui.button(
                        "Vistas",
                        on_click=lambda: self.show_view("views")
                    ).props("flat color=red-600")

                    # Conflicts button (admin, gestor, or Sistemas roles)
                    if self.has_any_role('admin', 'gestor', 'sistemas'):
                        self.navigation_buttons["conflicts"] = ui.button(
                            "Conflictos",
                            on_click=lambda: self.show_view("conflicts")
                        ).props("flat color=red-600")
                        logger.info("Conflicts button added to navigation")

                ui.space()

                # User info and logout
                with ui.row().classes('items-center'):
                    username = app.storage.user.get('username', 'Usuario')
                    roles = self.get_user_roles()
                    roles_display = ", ".join(roles) if roles else "Sin roles"

                    with ui.column().classes('items-end'):
                        ui.label(f"{username}").classes('text-sm font-semibold text-gray-700')
                        ui.label(f"Roles: {roles_display}").classes('text-xs text-gray-500')

                    def logout():
                        logger.info(f"User {username} logging out")
                        app.storage.user.clear()
                        ui.navigate.to('/login')

                    ui.button(icon='logout', on_click=logout).props(
                        'flat dense round color=red-600'
                    ).tooltip('Cerrar sesión')

    def create_views(self) -> None:
        """Creates only the application views authorized for the current user's role."""

        logger.info("Creating views based on user roles...")

        try:
            # Always create the basic views
            self.views["home"] = HomeView(self.show_view)
            self.views["views"] = ViewsExplorerView(self.api_client)
            logger.info("Basic views created: home, views")

            # Conditionally create views based on roles
            if self.has_any_role('admin', 'sistemas'):
                self.views["admin"] = AdminView(self.api_client)
                logger.info("Admin view created")

            if self.has_any_role('admin', 'gestor', 'sistemas'):
                self.views["conflicts"] = ConflictsView(self.api_client)
                logger.info("Conflicts view created")

            # Create view containers with proper visibility management
            with ui.column().classes("w-full min-h-screen bg-gray-50"):
                for name, view in self.views.items():
                    container = ui.column().classes("w-full")
                    container.visible = False  # Initially hide all views
                    self.view_containers[name] = container

                    with container:
                        try:
                            view.create()
                            logger.info(f"View '{name}' rendered successfully")
                        except Exception as e:
                            logger.error(f"Error creating view '{name}': {e}")
                            ui.notify(f"Error al cargar la vista {name}", type='negative')

            # Show the initial view
            self.show_view("home")

        except Exception as e:
            logger.error(f"Critical error in create_views: {e}")
            ui.notify("Error al inicializar la aplicación", type='negative')

    def refresh_views(self) -> None:
        """Refresh the current view (useful for data updates)."""
        if self.current_view in self.views:
            view = self.views[self.current_view]
            if hasattr(view, 'refresh'):
                try:
                    view.refresh()
                    logger.info(f"View '{self.current_view}' refreshed")
                except Exception as e:
                    logger.error(f"Error refreshing view '{self.current_view}': {e}")
                    ui.notify("Error al actualizar la vista", type='warning')

    async def cleanup(self) -> None:
        """Cleanup resources on application shutdown."""
        try:
            logger.info("Starting application cleanup...")

            # Cleanup views if they have cleanup methods
            for name, view in self.views.items():
                if hasattr(view, 'cleanup'):
                    try:
                        await view.cleanup()
                        logger.info(f"View '{name}' cleaned up")
                    except Exception as e:
                        logger.error(f"Error cleaning up view '{name}': {e}")

            # Close API client
            await self.api_client.close()
            logger.info("API client closed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# ---------------------------------------------------------------------
# 3. APPLICATION ENTRY POINTS AND LIFECYCLE MANAGEMENT
# ---------------------------------------------------------------------

app_instance: Optional[Application] = None
api_singleton = APIClient(config.API_BASE_URL)

@ui.page('/')
async def main_page_entry():
    """Main entry point for authenticated users."""
    global app_instance

    try:
        # Log entry
        username = app.storage.user.get('username', 'Unknown')
        logger.info(f"Main page accessed by user: {username}")

        # Create application instance
        app_instance = Application(api_client=api_singleton)

        # Build UI components
        app_instance.create_header()
        app_instance.create_views()

        # Note: Keyboard shortcuts can be added to specific views if needed

    except Exception as e:
        logger.error(f"Error initializing main page: {e}")
        ui.notify("Error al inicializar la aplicación", type='negative')

        # Show error page
        with ui.column().classes("w-full h-screen items-center justify-center"):
            ui.icon("error", size="5em", color="red")
            ui.label("Error al cargar la aplicación").classes("text-xl mt-4")
            ui.label(str(e)).classes("text-gray-600 mt-2")
            ui.button("Volver a intentar", on_click=lambda: ui.navigate.to('/')).props("color=red-600")
# Create login page
create_login_page(api_client=api_singleton)

# ---------------------------------------------------------------------
# 4. ERROR HANDLERS
# ---------------------------------------------------------------------

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.url.path}")
    return RedirectResponse('/')

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(f"500 error: {exc}")
    return RedirectResponse('/login')

# ---------------------------------------------------------------------
# 5. SHUTDOWN HANDLER
# ---------------------------------------------------------------------

async def shutdown_handler():
    """Handle application shutdown gracefully."""
    global app_instance

    logger.info("Application shutdown initiated...")

    if app_instance:
        await app_instance.cleanup()
    elif api_singleton.client is not None:
        await api_singleton.close()

    logger.info("Application shutdown complete")

app.on_shutdown(shutdown_handler)

# ---------------------------------------------------------------------
# 6. MAIN ENTRY POINT
# ---------------------------------------------------------------------

if __name__ in {"__main__", "__mp_main__"}:
    # Get configuration
    storage_secret = os.environ.get(
        'NICEGUI_STORAGE_SECRET',
        'Qv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXfs2E4Y0Q5W'
    )

    # Log startup information
    logger.info(f"Starting application on {config.APP_HOST}:{config.APP_PORT}")
    logger.info(f"API endpoint: {config.API_BASE_URL}")

    # Run the application
    ui.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        title=config.APP_TITLE,
        storage_secret=storage_secret,
        reload=False,  # Set to True for development
        show=False,    # Set to True to auto-open browser
        favicon='🎯'
    )