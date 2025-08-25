#!/usr/bin/env python3
"""
Clean Authentication Integration - No API Duplication
Extends your existing main.py with minimal changes
"""
import os
import hashlib
import secrets
from typing import Optional, Dict, List
from nicegui import ui, app
from config import config
from api.client import APIClient

# =====================================================================
# AUTHENTICATION SERVICE (EXTENDS YOUR EXISTING API CLIENT)
# =====================================================================

class AuthService:
    """Handles authentication logic using your existing API client"""

    def __init__(self, api_client: APIClient):
        self.api = api_client

    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """Hash password with salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_hex(32)

        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return password_hash.hex(), salt

    def _verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash"""
        computed_hash, _ = self._hash_password(password, salt)
        return computed_hash == stored_hash

    async def authenticate_user(self, alias: str, password: str) -> Optional[Dict]:
        """Authenticate user against database using existing API client"""
        try:
            # Get user from database
            users = await self.api.get_records(
                'usuarios',
                {'alias': f'eq.{alias}', 'is_active': 'eq.true'}
            )

            if not users:
                return None

            user = users[0]

            # Get user credentials
            credentials = await self.api.get_records(
                'usuario_credenciales',
                {'usuario_id': f'eq.{user["id"]}'}
            )

            if not credentials:
                return None

            cred = credentials[0]

            # Verify password
            if self._verify_password(password, cred['password_hash'], cred['salt']):
                # Get user roles
                user_roles = await self.get_user_roles(user['id'])
                user['roles'] = user_roles
                return user

            return None

        except Exception as e:
            ui.notify(f'Error de autenticación: {str(e)}', type='negative')
            return None

    async def get_user_roles(self, user_id: int) -> List[str]:
        """Get user roles using existing API client"""
        try:
            user_role_records = await self.api.get_records(
                'usuario_roles',
                {'usuario_id': f'eq.{user_id}'}
            )

            roles = []
            for ur in user_role_records:
                role_records = await self.api.get_records(
                    'auth_roles',
                    {'id': f'eq.{ur["role_id"]}'}
                )
                if role_records:
                    roles.append(role_records[0]['nombre'])

            return roles

        except Exception:
            return []

# =====================================================================
# ENHANCE YOUR EXISTING APPLICATION CLASS
# =====================================================================

class Application:
    """Enhanced version of your existing Application class"""

    def __init__(self):
        self.api_client = APIClient(config.API_BASE_URL)
        self.auth_service = AuthService(self.api_client)  # Add auth service
        self.current_view = "home"
        self.view_containers = {}
        self.views = {}
        self.setup_static_files()

        # Set secure storage secret
        self._setup_secure_storage()

    def _setup_secure_storage(self):
        """Setup secure session storage"""
        storage_secret = os.environ.get('NICEGUI_STORAGE_SECRET', 'CHANGE_THIS_IN_PRODUCTION')
        if storage_secret == 'CHANGE_THIS_IN_PRODUCTION':
            ui.notify('WARNING: Using default storage secret. Set NICEGUI_STORAGE_SECRET.',
                     type='warning')
        # NiceGUI will use this automatically when you call ui.run(storage_secret=...)

    def setup_static_files(self):
        # Your existing setup_static_files method unchanged
        from pathlib import Path
        base_dir = Path(__file__).parent
        assets_dir = base_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        (assets_dir / "images").mkdir(exist_ok=True)
        app.add_static_files("/assets", str(assets_dir))

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return app.storage.user.get('authenticated', False)

    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user"""
        if self.is_authenticated():
            return {
                'id': app.storage.user.get('user_id'),
                'alias': app.storage.user.get('username'),
                'nombre': app.storage.user.get('nombre', ''),
                'roles': app.storage.user.get('roles', [])
            }
        return None

    def has_role(self, required_role: str) -> bool:
        """Check if current user has specific role"""
        user_roles = app.storage.user.get('roles', [])
        return required_role in user_roles

    def require_auth(self):
        """Redirect to login if not authenticated"""
        if not self.is_authenticated():
            ui.navigate.to('/login')
            return False
        return True

    def show_view(self, view_name: str):
        """Show a specific view with authentication check"""
        if not self.require_auth():
            return

        # Optional: Add role-based view restrictions here
        role_restrictions = {
            'enhanced_crud': ['admin', 'coordinator'],
            'conflicts': ['admin', 'coordinator', 'technician']
        }

        required_roles = role_restrictions.get(view_name, [])
        if required_roles and not any(self.has_role(role) for role in required_roles):
            ui.notify('No tiene permisos para acceder a esta sección', type='warning')
            return

        # Your existing show_view logic
        self.current_view = view_name
        for name, container in self.view_containers.items():
            container.set_visibility(name == view_name)

    def create_header(self):
        """Enhanced header with authentication info"""
        with ui.header().classes("bg-white shadow-lg"):
            with ui.row().classes("w-full items-center p-2 gap-4"):
                # Your existing logo section
                with ui.element("div").classes(
                    "w-1/5 min-w-[200px] max-w-[280px] cursor-pointer"
                ).on("click", lambda: self.show_view("home")):
                    ui.image("/assets/images/logo.png")

                ui.element("div").classes("h-10 w-px bg-gray-300")
                ui.label("Sistema de Gestión").classes("text-xl font-italic text-gray-400")
                ui.space()

                # Enhanced navigation with role-based visibility
                with ui.row().classes("gap-2"):
                    ui.button("Inicio", on_click=lambda: self.show_view("home")).props("flat color=red-600")

                    # Role-based button visibility
                    if self.has_role('admin') or self.has_role('coordinator'):
                        ui.button(
                            "administración BBDD",
                            on_click=lambda: self.show_view("enhanced_crud"),
                        ).props("flat color=red-600")

                    ui.button("Vistas", on_click=lambda: self.show_view("views")).props("flat color=red-600")

                    if (self.has_role('admin') or self.has_role('coordinator') or
                        self.has_role('technician')):
                        ui.button(
                            "Conflictos", on_click=lambda: self.show_view("conflicts")
                        ).props("flat color=red-600")

                # User info and logout
                current_user = self.get_current_user()
                if current_user:
                    with ui.row().classes("gap-2 items-center"):
                        ui.label(f"Usuario: {current_user['alias']}").classes("text-sm text-gray-600")
                        ui.label(f"Roles: {', '.join(current_user['roles'])}").classes("text-xs text-gray-500")
                        ui.button(
                            icon="logout",
                            on_click=self.logout
                        ).props("flat round").tooltip("Cerrar Sesión")

    def logout(self):
        """Logout user"""
        app.storage.user.clear()
        ui.navigate.to('/login')

    def create_views(self):
        """Your existing create_views method with auth check"""
        if not self.require_auth():
            return

        # Your existing view creation logic
        from views.home import HomeView
        from views.admin import AdminView
        from views.enhanced_crud import EnhancedCrudView
        from views.views_explorer import ViewsExplorerView
        from views.conflicts import ConflictsView

        self.views["home"] = HomeView(self.show_view)
        self.views["admin"] = AdminView(self.api_client)
        self.views["enhanced_crud"] = EnhancedCrudView(self.api_client)
        self.views["views"] = ViewsExplorerView(self.api_client)
        self.views["conflicts"] = ConflictsView(self.api_client)

        with ui.column().classes("w-full min-h-screen bg-gray-50"):
            for name, view in self.views.items():
                self.view_containers[name] = ui.column().classes("w-full")
                with self.view_containers[name]:
                    view.create()

        self.show_view("home")

    async def cleanup(self):
        """Your existing cleanup method"""
        await self.api_client.close()

# =====================================================================
# AUTHENTICATION PAGES (SIMPLE, NO FASTAPI NEEDED)
# =====================================================================

@ui.page('/login')
async def login_page(redirect_to: str = '/'):
    """Login page using your existing API client"""

    # If already authenticated, redirect
    if app.storage.user.get('authenticated', False):
        ui.navigate.to('/')
        return

    # Create auth service using existing API pattern
    api_client = APIClient(config.API_BASE_URL)
    auth_service = AuthService(api_client)

    async def try_login():
        if not username.value or not password.value:
            ui.notify('Por favor, ingrese usuario y contraseña', color='negative')
            return

        user = await auth_service.authenticate_user(username.value, password.value)

        if user:
            app.storage.user.update({
                'username': user['alias'],
                'user_id': user['id'],
                'nombre': user.get('nombre', ''),
                'authenticated': True,
                'roles': user.get('roles', [])
            })

            ui.notify(f'Bienvenido, {user["alias"]}!', type='positive')
            ui.navigate.to(redirect_to)
        else:
            ui.notify('Usuario o contraseña incorrectos', color='negative')

    # Simple login UI
    with ui.column().classes('absolute-center items-center gap-4'):
        ui.label('Sindicato INQ - Acceso al Sistema').classes('text-h4 text-center')

        with ui.card().classes('p-6'):
            ui.label('Iniciar Sesión').classes('text-h6 mb-4')

            username = ui.input('Usuario').classes('w-64').on('keydown.enter', try_login)
            password = ui.input(
                'Contraseña',
                password=True,
                password_toggle_button=True
            ).classes('w-64').on('keydown.enter', try_login)

            ui.button('Acceder', on_click=try_login).classes('w-full').props('color=orange-600')

# =====================================================================
# MODIFIED MAIN PAGE (MINIMAL CHANGES TO YOUR EXISTING CODE)
# =====================================================================

app_instance = None

@ui.page("/")
async def main_page():
    """Enhanced main page with authentication"""
    global app_instance

    # Check authentication first
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return

    # Use your enhanced Application class
    app_instance = Application()
    app_instance.create_header()
    app_instance.create_views()

async def shutdown_handler():
    """Your existing shutdown handler"""
    global app_instance
    if app_instance:
        await app_instance.cleanup()

app.on_shutdown(shutdown_handler)

if __name__ in {"__main__", "__mp_main__"}:
    # Add storage secret for secure sessions
    storage_secret = os.environ.get('NICEGUI_STORAGE_SECRET', 'CHANGE_THIS_IN_PRODUCTION')

    ui.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        title=config.APP_TITLE,
        storage_secret=storage_secret
    )