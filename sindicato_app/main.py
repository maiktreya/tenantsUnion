#!/usr/bin/env python3
from pathlib import Path
from nicegui import ui, app
from config import config
from api.client import APIClient  # Import API client
from views.home import HomeView
from views.admin import AdminView
from views.views_explorer import ViewsExplorerView
from views.conflicts import ConflictsView

class Application:
    """Main application class"""

    def __init__(self):
        self.api_client = APIClient(config.API_BASE_URL)  # Create API client instance
        self.current_view = 'home'
        self.view_containers = {}
        self.views = {}

        # Setup static files serving
        self.setup_static_files()

    def setup_static_files(self):
        """Setup static files serving for assets"""
        base_dir = Path(__file__).parent
        assets_dir = base_dir / 'assets'
        assets_dir.mkdir(exist_ok=True)
        (assets_dir / 'images').mkdir(exist_ok=True)
        app.add_static_files('/assets', str(assets_dir))

    def show_view(self, view_name: str):
        """Show a specific view and hide others"""
        self.current_view = view_name
        for name, container in self.view_containers.items():
            container.set_visibility(name == view_name)

    def create_header(self):
        """Create the application header with logo"""
        with ui.header().classes('bg-white shadow-lg'):
            with ui.row().classes('w-full items-center p-2 gap-4'):
                # Logo container
                with ui.element('div').classes(
                    'w-1/5 min-w-[200px] max-w-[280px] cursor-pointer'
                ).on('click', lambda: self.show_view('home')):
                    ui.image('/assets/images/logo.png').classes(
                        'h-12 w-auto object-contain'
                    )

                ui.element('div').classes('h-10 w-px bg-gray-300')
                ui.label('Sistema de Gestión').classes('text-xl font-semibold text-gray-800')
                ui.space()

                # Navigation buttons
                with ui.row().classes('gap-2'):
                    ui.button('Inicio', on_click=lambda: self.show_view('home')).props('flat color=red-600')
                    ui.button('Tablas', on_click=lambda: self.show_view('admin')).props('flat color=red-600')
                    ui.button('Vistas', on_click=lambda: self.show_view('views')).props('flat color=red-600')
                    ui.button('Conflictos', on_click=lambda: self.show_view('conflicts')).props('flat color=red-600')

    def create_views(self):
        """Create all application views"""
        # Initialize views - passing API client to each view
        self.views['home'] = HomeView(self.show_view)
        self.views['admin'] = AdminView(self.api_client)
        self.views['views'] = ViewsExplorerView(self.api_client)
        self.views['conflicts'] = ConflictsView(self.api_client)  # Pass API client

        # Create view containers
        with ui.column().classes('w-full min-h-screen bg-gray-50'):
            for name, view in self.views.items():
                self.view_containers[name] = ui.column().classes('w-full')
                with self.view_containers[name]:
                    view.create()

        # Show home by default
        self.show_view('home')

    async def cleanup(self):
        """Cleanup resources on shutdown"""
        await self.api_client.close()

# Global application instance
app_instance = None

@ui.page('/')
async def main_page():
    """Main application page"""
    global app_instance
    app_instance = Application()
    app_instance.create_header()
    app_instance.create_views()

# Shutdown handler
async def shutdown_handler():
    """Handle application shutdown"""
    global app_instance
    if app_instance:
        await app_instance.cleanup()

# Register shutdown handler
app.on_shutdown(shutdown_handler)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        title=config.APP_TITLE
    )