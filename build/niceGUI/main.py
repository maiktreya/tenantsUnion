# build/niceGUI/main.py (Corrected)

import os
import logging
import locale
from pathlib import Path
from typing import Optional
from nicegui import ui, app

from logging_config import setup_logging
from config import config

setup_logging()

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.client import APIClient

from state.app_state import AppState

from views.home import HomeView
from views.admin import AdminView
from views.views_explorer import ViewsExplorerView
from views.conflicts import ConflictsView
from views.afiliadas_importer import AfiliadasImporterView

from auth.login import create_login_page
from auth.user_management import UserManagementView
from auth.user_profile import UserProfileView

log = logging.getLogger(__name__)
unrestricted_page_routes = {"/login"}


# =====================================================================
# AUTHENTICATION MIDDLEWARE
# =====================================================================


class AuthMiddleware(BaseHTTPMiddleware):
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

# =====================================================================
# MAIN APPLICATION CLASS
# =====================================================================


class Application:
    def __init__(self, api_client: APIClient, state: AppState):
        self.api_client = api_client
        self.state = state
        self.current_view = "home"
        self.view_containers = {}
        self.views = {}
        self.setup_static_files()

    def setup_static_files(self):
        assets_dir = Path(__file__).parent / "assets"
        app.add_static_files("/assets", str(assets_dir))

    async def initialize_global_data(self):
        """Fetches and caches data used across multiple views."""
        try:
            self.state.all_nodos = await self.api_client.get_records(
                "nodos", order="nombre.asc"
            )
            records = await self.api_client.get_records(
                "v_afiliadas_detalle", limit=5000
            )
            self.state.all_afiliadas_options = {
                r[
                    "id"
                ]: f'{r.get("Nombre", "")} {r.get("Apellidos", "")} (ID: {r.get("id")})'
                for r in records
            }
            log.info("Global application state initialized successfully.")
        except Exception as e:
            ui.notify(
                f"FATAL: Could not initialize global state. Error: {e}", type="negative"
            )
            log.exception("Failed to initialize global state")

    def has_role(self, *roles: str) -> bool:
        user_roles = {role.lower() for role in app.storage.user.get("roles", [])}
        return not {role.lower() for role in roles}.isdisjoint(user_roles)

    def show_view(self, view_name: str):
        if view_name not in self.views:
            ui.notify("Acceso no autorizado.", type="negative")
            return
        self.current_view = view_name
        for name, container in self.view_containers.items():
            container.visible = name == view_name

    def create_header(self):
        with ui.header().classes("bg-white shadow-lg").props("id=main-header"):
            with ui.row().classes("w-full items-center p-2 gap-4"):
                ui.image("/assets/images/logo.png").classes("w-48 cursor-pointer").on(
                    "click", lambda: self.show_view("home")
                )
                ui.element("div").classes("h-10 w-px bg-gray-300")
                ui.label("Sistema de Gestión").classes(
                    "text-xl font-italic text-gray-400"
                )
                ui.space()

                with ui.row().classes("gap-2"):
                    if self.has_role("admin", "sistemas"):
                        ui.button(
                            "Admin BBDD", on_click=lambda: self.show_view("admin")
                        ).props("flat color=red-600")
                        ui.button(
                            "Admin Usuarios",
                            on_click=lambda: self.show_view("user_management"),
                        ).props("flat color=red-600")
                    if self.has_role("admin", "gestor"):
                        ui.button(
                            "Vistas", on_click=lambda: self.show_view("views")
                        ).props("flat color=red-600")
                        ui.button(
                            "Importar Afiliadas",
                            on_click=lambda: self.show_view("afiliadas_importer"),
                        ).props("flat color=red-600")
                    if self.has_role("admin", "gestor", "actas"):
                        ui.button(
                            "Conflictos", on_click=lambda: self.show_view("conflicts")
                        ).props("flat color=red-600")

                ui.space()

                with ui.row().classes("items-center"):
                    username = app.storage.user.get("username", "...")
                    roles = ", ".join(app.storage.user.get("roles", []))
                    with ui.element().classes(
                        "cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
                    ).on("click", lambda: self.show_view("user_profile")):
                        ui.label(f"User: {username} ({roles})").classes(
                            "mr-2 text-gray-600 text-xs"
                        )
                        ui.icon("person", size="sm").classes("text-gray-500").tooltip(
                            "Ver mi perfil"
                        )

                    def logout():
                        app.storage.user.clear()
                        ui.navigate.to("/login")

                    ui.button(on_click=logout, icon="logout").props(
                        "flat dense round color=red-600"
                    ).tooltip("Cerrar sesión")

        ui.add_head_html(
            """
            <style>
                #main-header {
                    transition: transform 0.3s cubic-bezier(0.4,0,0.2,1);
                    z-index: 100;
                    position: sticky;
                    top: 0;
                }
                .hide-on-scroll {
                    transform: translateY(-100%);
                }
            </style>
        """
        )
        ui.run_javascript(
            """
            let lastScroll = 0;
            const header = document.getElementById('main-header');
            window.addEventListener('scroll', function() {
                const currScroll = window.scrollY;
                if (currScroll > lastScroll && currScroll > 50) {
                    header.classList.add('hide-on-scroll');
                } else {
                    header.classList.remove('hide-on-scroll');
                }
                lastScroll = currScroll;
            });
        """
        )

    def create_views(self):
        try:
            self.views["home"] = HomeView(self.show_view)
            self.views["user_profile"] = UserProfileView(self.api_client)
            if self.has_role("admin", "sistemas"):
                self.views["admin"] = AdminView(self.api_client)
                self.views["user_management"] = UserManagementView(self.api_client)
            if self.has_role("admin", "gestor"):
                self.views["views"] = ViewsExplorerView(self.api_client)
                self.views["afiliadas_importer"] = AfiliadasImporterView(
                    self.api_client
                )
            if self.has_role("admin", "gestor", "actas"):
                self.views["conflicts"] = ConflictsView(self.api_client, self.state)
            with ui.column().classes("w-full min-h-screen bg-gray-50"):
                for name, view in self.views.items():
                    self.view_containers[name] = container = ui.column().classes(
                        "w-full"
                    )
                    container.visible = False
                    with container:
                        view.create()
            self.show_view("home")
        except Exception as e:
            ui.notify(f"Error fatal al crear las vistas: {e}", type="negative")
            log.exception("Failed to create views")

    async def cleanup(self):
        if self.api_client:
            await self.api_client.close()


# =====================================================================
# INITIALIZATION OF GLOBAL INSTANCES
# =====================================================================

api_singleton = APIClient(config.API_BASE_URL)
app_state_init = AppState()
app_instance: Optional[Application] = None


# =====================================================================
# MAIN APP ENTRY POINT
# =====================================================================


@ui.page("/")
def main_page_entry():
    global app_instance
    app_instance = Application(api_client=api_singleton, state=app_state_init)

    ui.timer(0.2, app_instance.initialize_global_data, once=True)

    app_instance.create_header()
    app_instance.create_views()


create_login_page(api_client=api_singleton)


@app.on_shutdown
async def shutdown_handler():
    if app_instance:
        await app_instance.cleanup()


if __name__ in {"__main__", "__mp_main__"}:
    # Set the locale for the entire application to Spanish
    try:
        locale.setlocale(locale.LC_ALL, "es_ES.UTF-8")  # <-- ADD THIS LINE
    except locale.Error:
        print("Spanish locale not found, falling back to default.")

    storage_secret = os.environ.get("NICEGUI_STORAGE_SECRET")
    ui.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        title=config.APP_TITLE,
        storage_secret=storage_secret,
        favicon="🎯",
    )
