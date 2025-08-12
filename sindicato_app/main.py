#!/usr/bin/env python3
import os
from pathlib import Path
from nicegui import ui, app
from config import config
from api.client import APIClient
from views.home import HomeView
from views.admin import AdminView
from views.views_explorer import ViewsExplorerView
from views.conflicts import ConflictsView
from views.enhanced_crud import EnhancedCrudView  # Make sure this import is present


class Application:
    """Main application class"""

    def __init__(self):
        self.api_client = APIClient(config.API_BASE_URL)
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
        """Show a specific view and hide others"""
        self.current_view = view_name
        for name, container in self.view_containers.items():
            container.set_visibility(name == view_name)

    def create_header(self):
        """Create the application header with logo banner"""
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

                with ui.row().classes("gap-2"):
                    ui.button("Inicio", on_click=lambda: self.show_view("home")).props(
                        "flat color=red-600"
                    )

                    # ui.button("Tablas", on_click=lambda: self.show_view("admin")).props(
                    #    "flat color=red-600"
                    # )

                    ui.button(
                        "administración BBDD",
                        on_click=lambda: self.show_view("enhanced_crud"),
                    ).props("flat color=red-600")

                    ui.button("Vistas", on_click=lambda: self.show_view("views")).props(
                        "flat color=red-600"
                    )

                    ui.button(
                        "Conflictos", on_click=lambda: self.show_view("conflicts")
                    ).props("flat color=red-600")

    def create_views(self):
        """Create all application views"""
        self.views["home"] = HomeView(self.show_view)
        self.views["admin"] = AdminView(self.api_client)
        self.views["enhanced_crud"] = EnhancedCrudView(
            self.api_client
        )  # This line creates the view instance
        self.views["views"] = ViewsExplorerView(self.api_client)
        self.views["conflicts"] = ConflictsView(self.api_client)

        with ui.column().classes("w-full min-h-screen bg-gray-50"):
            for name, view in self.views.items():
                # This loop creates the UI container for each view, including the new one
                self.view_containers[name] = ui.column().classes("w-full")
                with self.view_containers[name]:
                    view.create()

        self.show_view("home")

    async def cleanup(self):
        """Cleanup resources on shutdown"""
        await self.api_client.close()


app_instance = None


@ui.page("/")
async def main_page():
    """Main application page"""
    global app_instance
    app_instance = Application()
    app_instance.create_header()
    app_instance.create_views()


async def shutdown_handler():
    """Handle application shutdown"""
    global app_instance
    if app_instance:
        await app_instance.cleanup()


app.on_shutdown(shutdown_handler)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        title=config.APP_TITLE,
    )
