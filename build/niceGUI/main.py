import os
import logging
from pathlib import Path
from typing import Optional
from nicegui import ui, app

from logging_config import setup_logging

setup_logging()

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.client import APIClient
from config import config
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
        with ui.header().classes("bg-white shadow-lg"):
            with ui.row().classes("w-full items-center p-2 gap-4"):
                ui.image("/assets/images/logo.png").classes("w-48 cursor-pointer").on(
                    "click", lambda: self.show_view("home")
                )
                ui.space()
                if self.has_role("admin", "sistemas"):
                    ui.button(
                        "Admin BBDD", on_click=lambda: self.show_view("admin")
                    ).props("flat color=orange-600")
                    ui.button(
                        "Admin Usuarios",
                        on_click=lambda: self.show_view("user_management"),
                    ).props("flat color=orange-600")
                if self.has_role("admin", "gestor"):
                    ui.button("Vistas", on_click=lambda: self.show_view("views")).props(
                        "flat color=orange-600"
                    )
                    ui.button(
                        "Importar Afiliadas",
                        on_click=lambda: self.show_view("afiliadas_importer"),
                    ).props("flat color=orange-600")
                if self.has_role("admin", "gestor", "actas"):
                    ui.button(
                        "Conflictos", on_click=lambda: self.show_view("conflicts")
                    ).props("flat color=orange-600")
                ui.button(
                    "Mi Perfil", on_click=lambda: self.show_view("user_profile")
                ).props("flat")
                ui.button(
                    "Logout",
                    on_click=lambda: app.storage.user.clear()
                    or ui.navigate.to("/login"),
                    icon="logout",
                ).props("flat dense color=negative")

    def create_views(self):
        try:
            self.views["home"] = HomeView(self.show_view)
            self.views["user_profile"] = UserProfileView(self.api_client)
            if self.has_role("admin", "sistemas"):
                self.views["admin"] = AdminView(self.api_client, self.state)
                self.views["user_management"] = UserManagementView(self.api_client)
            if self.has_role("admin", "gestor"):
                self.views["views"] = ViewsExplorerView(self.api_client, self.state)
                # --- THIS IS THE FIX ---
                # The importer view is now correctly created with its state slice
                self.views["afiliadas_importer"] = AfiliadasImporterView(
                    self.api_client, self.state.afiliadas_importer
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


api_singleton = APIClient(config.API_BASE_URL)
app_state_singleton = AppState(api_singleton)
app_instance: Optional[Application] = None


@ui.page("/")
def main_page_entry():
    global app_instance
    app_instance = Application(api_client=api_singleton, state=app_state_singleton)
    ui.timer(0.2, app_state_singleton.initialize_global_data, once=True)
    app_instance.create_header()
    app_instance.create_views()


create_login_page(api_client=api_singleton)


@app.on_shutdown
async def shutdown_handler():
    if app_instance:
        await app_instance.cleanup()


if __name__ in {"__main__", "__mp_main__"}:
    storage_secret = os.environ.get(
        "NICEGUI_STORAGE_SECRET", "a-secure-secret-key-here"
    )
    ui.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        title=config.APP_TITLE,
        storage_secret=storage_secret,
        favicon="🎯",
    )
