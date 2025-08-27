from typing import Optional
from nicegui import ui, app
from api.client import APIClient
from passlib.context import CryptContext

# Use the same password context as your login system
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserProfileView:
    """User self-management view for personal info and password changes"""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.current_user = None
        self.user_roles = []

    def create(self) -> ui.column:
        """Create the user profile view UI"""
        container = ui.column().classes('w-full p-6 max-w-2xl mx-auto gap-6')

        with container:
            ui.label('Mi Perfil').classes('text-h4 text-center')

            # Load user data on creation
            ui.timer(0.1, self._load_user_data, once=True)

            # Personal Information Card
            with ui.card().classes('w-full p-6'):
                ui.label('Información Personal').classes('text-h6 mb-4')

                self.info_container = ui.column().classes('w-full gap-4')

            # Password Change Card
            with ui.card().classes('w-full p-6'):
                ui.label('Cambiar Contraseña').classes('text-h6 mb-4')

                self.password_container = ui.column().classes('w-full gap-4')

            # Roles Information (Read-only)
            with ui.card().classes('w-full p-6'):
                ui.label('Mis Roles').classes('text-h6 mb-4')
                ui.label('Los roles son asignados por los administradores del sistema').classes('text-caption text-gray-600 mb-2')

                self.roles_container = ui.row().classes('gap-2')

        return container

    async def _load_user_data(self):
        """Load current user data from database"""
        try:
            user_id = app.storage.user.get('user_id')
            if not user_id:
                ui.notify('Error: Usuario no identificado', type='negative')
                return

            # Load user info
            user_records = await self.api.get_records('usuarios', {'id': f'eq.{user_id}'})
            if not user_records:
                ui.notify('Error: Usuario no encontrado', type='negative')
                return

            self.current_user = user_records[0]

            # Load user roles from session (already loaded during login)
            self.user_roles = app.storage.user.get('roles', [])

            self._display_user_info()
            self._display_password_form()
            self._display_roles()

        except Exception as e:
            ui.notify(f'Error al cargar datos del usuario: {str(e)}', type='negative')

    def _display_user_info(self):
        """Display user information form"""
        if not self.current_user or not self.info_container:
            return

        self.info_container.clear()

        with self.info_container:
            # Personal info form
            self.alias_input = ui.input(
                'Usuario (Alias)',
                value=self.current_user.get('alias', '')
            ).classes('w-full').props('readonly').tooltip('El alias no se puede modificar')

            self.nombre_input = ui.input(
                'Nombre *',
                value=self.current_user.get('nombre', '')
            ).classes('w-full')

            self.apellidos_input = ui.input(
                'Apellidos',
                value=self.current_user.get('apellidos', '')
            ).classes('w-full')

            self.email_input = ui.input(
                'Email',
                value=self.current_user.get('email', '') or ''
            ).classes('w-full')

            # Save button
            ui.button(
                'Guardar Cambios',
                icon='save',
                on_click=self._save_personal_info
            ).props('color=orange-600').classes('mt-4')

    def _display_password_form(self):
        """Display password change form"""
        if not self.password_container:
            return

        self.password_container.clear()

        with self.password_container:
            ui.markdown('**Importante:** Ingresa tu contraseña actual para confirmar los cambios.').classes('text-caption text-gray-600 mb-4')

            self.current_password = ui.input(
                'Contraseña Actual *',
                password=True,
                password_toggle_button=True
            ).classes('w-full')

            self.new_password = ui.input(
                'Nueva Contraseña *',
                password=True,
                password_toggle_button=True
            ).classes('w-full')

            self.confirm_password = ui.input(
                'Confirmar Nueva Contraseña *',
                password=True,
                password_toggle_button=True
            ).classes('w-full')

            # Change password button
            ui.button(
                'Cambiar Contraseña',
                icon='lock',
                on_click=self._change_password
            ).props('color=blue-600').classes('mt-4')

    def _display_roles(self):
        """Display user roles (read-only)"""
        if not self.roles_container:
            return

        self.roles_container.clear()

        with self.roles_container:
            if self.user_roles:
                for role in self.user_roles:
                    ui.chip(role.title(), color='blue').props('dense')
            else:
                ui.label('Sin roles asignados').classes('text-gray-500')

    async def _save_personal_info(self):
        """Save personal information changes"""
        if not self.current_user:
            return

        # Validation
        if not self.nombre_input.value.strip():
            ui.notify('El nombre es obligatorio', type='warning')
            return

        try:
            # Prepare update data
            update_data = {
                'nombre': self.nombre_input.value.strip(),
                'apellidos': self.apellidos_input.value.strip(),
                'email': self.email_input.value.strip() if self.email_input.value.strip() else None
            }

            # Check if there are actual changes
            current_data = {
                'nombre': self.current_user.get('nombre', ''),
                'apellidos': self.current_user.get('apellidos', ''),
                'email': self.current_user.get('email', '') or ''
            }

            has_changes = any(
                str(update_data[key] or '') != str(current_data[key] or '')
                for key in update_data.keys()
            )

            if not has_changes:
                ui.notify('No se realizaron cambios', type='info')
                return

            # Update user info
            result = await self.api.update_record('usuarios', self.current_user['id'], update_data)

            if result:
                # Update local data
                self.current_user.update(update_data)
                # Update session username if name changed
                app.storage.user['username'] = self.current_user['alias']  # Keep alias as username

                ui.notify('Información personal actualizada exitosamente', type='positive')
            else:
                ui.notify('Error al actualizar la información', type='negative')

        except Exception as e:
            ui.notify(f'Error al guardar cambios: {str(e)}', type='negative')

    async def _change_password(self):
        """Change user password"""
        # Validation
        if not all([self.current_password.value, self.new_password.value, self.confirm_password.value]):
            ui.notify('Todos los campos de contraseña son obligatorios', type='warning')
            return

        if self.new_password.value != self.confirm_password.value:
            ui.notify('La nueva contraseña y su confirmación no coinciden', type='warning')
            return

        if len(self.new_password.value) < 6:
            ui.notify('La nueva contraseña debe tener al menos 6 caracteres', type='warning')
            return

        try:
            # Get user_id from session
            user_id = app.storage.user.get('user_id')
            if not user_id:
                ui.notify('Error: Usuario no identificado', type='negative')
                return

            # Fetch current credentials
            cred_records = await self.api.get_records(
                'usuario_credenciales',
                {'usuario_id': f'eq.{user_id}'}
            )

            if not cred_records:
                ui.notify('Error: Credenciales no encontradas', type='negative')
                return

            stored_hash = cred_records[0]['password_hash']

            # Verify current password
            if not pwd_context.verify(self.current_password.value, stored_hash):
                ui.notify('La contraseña actual es incorrecta', type='negative')
                return

            # Hash new password
            new_password_hash = pwd_context.hash(self.new_password.value)

            # Update password - FIXED: using usuario_id as the primary key filter
            # Since usuario_credenciales uses usuario_id as primary key, we update it correctly
            result = await self.api.update_record(
                'usuario_credenciales',
                user_id,  # This is correct since usuario_id is the primary key
                {'password_hash': new_password_hash}
            )

            if result:
                # Clear password fields
                self.current_password.value = ''
                self.new_password.value = ''
                self.confirm_password.value = ''

                ui.notify('Contraseña actualizada exitosamente', type='positive')

                # Optional: Log this password change for security audit
                print(f"Password successfully changed for user_id: {user_id}")
            else:
                ui.notify('Error al actualizar la contraseña', type='negative')

        except Exception as e:
            ui.notify(f'Error al cambiar contraseña: {str(e)}', type='negative')
            print(f"Password change error for user_id {user_id}: {str(e)}")  # Debug log