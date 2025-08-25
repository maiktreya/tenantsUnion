# sindicato_app/views/login.py

from typing import Optional
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from passlib.context import CryptContext
from api.client import APIClient

# Initialize the password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_login_page(api_client: APIClient):
    """Factory function to create the login page, giving it access to the API client."""

    @ui.page('/login')
    async def login_page(redirect_to: str = '/') -> Optional[RedirectResponse]:
        """Login page that authenticates against the database."""

        async def try_login() -> None:
            if not username.value or not password.value:
                ui.notify('Username and password are required', color='negative')
                return

            # This now uses the 'api_client' from the factory's scope
            user_records = await api_client.get_records('usuarios', {'alias': f'eq.{username.value}'})
            if not user_records:
                ui.notify('Wrong username or password', color='negative')
                return

            user = user_records[0]
            user_id = user['id']

            cred_records = await api_client.get_records('usuario_credenciales', {'usuario_id': f'eq.{user_id}'})
            if not cred_records:
                ui.notify('Authentication not set up for this user', color='negative')
                return

            stored_hash = cred_records[0]['password_hash']

            if pwd_context.verify(password.value, stored_hash):
                app.storage.user.update({
                    'username': user['email'],
                    'user_id': user_id,
                    'authenticated': True,
                    'roles': user.get('roles', '').split(',')
                })
                ui.navigate.to(redirect_to)
            else:
                ui.notify('Wrong username or password', color='negative')

        if app.storage.user.get('authenticated', False):
            return RedirectResponse('/')

        with ui.card().classes('absolute-center'):
            ui.label('Gestión Sindicato INQ').classes('text-h6 self-center')
            username = ui.input('Username').on('keydown.enter', try_login)
            password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login)
            ui.button('Log in', on_click=try_login)

        return None