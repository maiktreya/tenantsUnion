from typing import Dict, List, Optional
from nicegui import ui, app
from api.client import APIClient
from passlib.context import CryptContext
from components.base_view import BaseView  # MODIFIED: Import BaseView from components

# Use the same password context as your login system
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserManagementView(BaseView):  # MODIFIED: Inherit from BaseView
    """User management view integrated with existing auth system"""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.users_container = None
        self.users_list = []
        self.roles_list = []

    # REMOVED: The redundant 'has_role' method has been deleted from this class.

    def create(self) -> ui.column:
        """Create the user management view UI"""
        container = ui.column().classes("w-full p-4 gap-4")

        with container:
            ui.label("Gestión de Usuarios y Roles").classes("text-h4")

            # Check permissions
            if not self.has_role("admin", "sistemas"):
                ui.label(
                    "Acceso denegado. Se requieren permisos de administrador."
                ).classes("text-red-600 text-center")
                return container

            # Action buttons
            with ui.row().classes("w-full gap-4 items-center mb-4"):
                ui.button(
                    "Crear Nuevo Usuario",
                    icon="person_add",
                    on_click=self._open_create_user_dialog,
                ).props("color=orange-600")

                ui.button(
                    "Gestionar Roles",
                    icon="admin_panel_settings",
                    on_click=self._open_roles_management,
                ).props("color=blue-600")

                ui.button(
                    "Refrescar",
                    icon="refresh",
                    on_click=lambda: ui.timer(0.1, self._load_data, once=True),
                ).props("color=orange-600")

            # Users list container
            self.users_container = ui.column().classes("w-full gap-2")

        # Load data on startup
        ui.timer(0.5, self._load_data, once=True)

        return container

    async def _load_data(self):
        """Load users and roles from database"""
        try:
            # Load users
            self.users_list = await self.api.get_records("usuarios", order="alias.asc")

            # Load roles
            self.roles_list = await self.api.get_records("roles", order="nombre.asc")

            self._display_users()
        except Exception as e:
            ui.notify(f"Error al cargar datos: {str(e)}", type="negative")

    async def _get_user_roles(self, user_id: int) -> List[str]:
        """Get role names for a user"""
        try:
            user_role_links = await self.api.get_records(
                "usuario_roles", {"usuario_id": f"eq.{user_id}"}
            )
            if not user_role_links:
                return []

            role_ids = [link["role_id"] for link in user_role_links]
            if not role_ids:
                return []

            roles_records = await self.api.get_records(
                "roles", {"id": f'in.({",".join(map(str, role_ids))})'}
            )
            return [role.get("nombre", "") for role in roles_records]
        except Exception:
            return []

    def _display_users(self):
        """Display the users list"""
        if not self.users_container:
            return

        self.users_container.clear()

        if not self.users_list:
            ui.label("No se encontraron usuarios").classes("text-gray-500")
            return

        ui.label(f"Usuarios registrados ({len(self.users_list)})").classes(
            "text-h6 mb-2"
        )

        # Users table
        with ui.card().classes("w-full"):
            # Header
            with ui.row().classes("w-full bg-gray-100 p-3 font-bold"):
                ui.label("Alias").classes("flex-1")
                ui.label("Nombre").classes("flex-2")
                ui.label("Email").classes("flex-2")
                ui.label("Roles").classes("flex-2")
                ui.label("Acciones").classes("w-40")

            # User rows
            for user in self.users_list:
                with ui.row().classes(
                    "w-full border-b p-3 hover:bg-gray-50 items-center"
                ):
                    ui.label(user.get("alias", "")).classes("flex-1")

                    full_name = (
                        f"{user.get('nombre', '')} {user.get('apellidos', '')}".strip()
                    )
                    ui.label(full_name or "Sin nombre").classes("flex-2")

                    ui.label(user.get("email", "Sin email")).classes("flex-2")

                    # Display roles (we'll load these dynamically)
                    roles_label = ui.label("Cargando...").classes(
                        "flex-2 text-gray-500"
                    )
                    ui.timer(
                        0.1,
                        lambda u=user, rl=roles_label: self._load_user_roles_display(
                            u, rl
                        ),
                        once=True,
                    )

                    with ui.row().classes("w-40 gap-1"):
                        ui.button(
                            icon="edit",
                            on_click=lambda u=user: self._open_edit_user_dialog(u),
                        ).props("size=sm flat dense color=orange-600").tooltip(
                            "Editar usuario"
                        )

                        ui.button(
                            icon="security",
                            on_click=lambda u=user: self._open_roles_dialog(u),
                        ).props("size=sm flat dense color=blue-600").tooltip(
                            "Gestionar roles"
                        )

                        ui.button(
                            icon="key",
                            on_click=lambda u=user: self._open_password_dialog(u),
                        ).props("size=sm flat dense color=green-600").tooltip(
                            "Cambiar contraseña"
                        )

    async def _load_user_roles_display(self, user: Dict, roles_label):
        """Load and display user roles in the table"""
        roles = await self._get_user_roles(user["id"])
        if roles:
            roles_label.set_text(", ".join(roles))
            roles_label.classes("flex-2 text-blue-600")
        else:
            roles_label.set_text("Sin roles")
            roles_label.classes("flex-2 text-gray-500")

    def _open_create_user_dialog(self):
        """Open dialog for creating a new user"""
        dialog = ui.dialog()

        with dialog, ui.card().classes("w-96"):
            ui.label("Crear Nuevo Usuario").classes("text-h6 mb-4")

            # Input fields
            alias_input = ui.input("Alias *", placeholder="usuario123").classes(
                "w-full"
            )
            nombre_input = ui.input("Nombre *", placeholder="Juan").classes("w-full")
            apellidos_input = ui.input("Apellidos", placeholder="García López").classes(
                "w-full"
            )
            email_input = ui.input("Email", placeholder="usuario@ejemplo.com").classes(
                "w-full"
            )
            password_input = ui.input(
                "Contraseña *", password=True, password_toggle_button=True
            ).classes("w-full")

            # Roles selection
            ui.label("Roles").classes("text-subtitle2 mt-4")
            roles_options = {role["id"]: role["nombre"] for role in self.roles_list}
            roles_select = ui.select(
                options=roles_options, multiple=True, label="Seleccionar roles"
            ).classes("w-full")

            # Action buttons
            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancelar", on_click=dialog.close).props("flat")

                async def create_user():
                    # Validation
                    if (
                        not alias_input.value
                        or not nombre_input.value
                        or not password_input.value
                    ):
                        ui.notify(
                            "Alias, nombre y contraseña son obligatorios",
                            type="warning",
                        )
                        return

                    try:
                        # Create user
                        user_data = {
                            "alias": alias_input.value.strip(),
                            "nombre": nombre_input.value.strip(),
                            "apellidos": (
                                apellidos_input.value.strip()
                                if apellidos_input.value
                                else ""
                            ),
                            "email": (
                                email_input.value.strip() if email_input.value else None
                            ),
                        }

                        new_user = await self.api.create_record("usuarios", user_data)
                        if not new_user:
                            ui.notify("Error al crear el usuario", type="negative")
                            return

                        user_id = new_user["id"]

                        # Create credentials
                        password_hash = pwd_context.hash(password_input.value)
                        cred_data = {
                            "usuario_id": user_id,
                            "password_hash": password_hash,
                        }

                        await self.api.create_record("usuario_credenciales", cred_data)

                        # Assign roles
                        if roles_select.value:
                            for role_id in roles_select.value:
                                role_data = {"usuario_id": user_id, "role_id": role_id}
                                await self.api.create_record("usuario_roles", role_data)

                        ui.notify("Usuario creado exitosamente", type="positive")
                        dialog.close()
                        await self._load_data()

                    except Exception as e:
                        ui.notify(f"Error al crear usuario: {str(e)}", type="negative")

                ui.button("Crear Usuario", on_click=create_user).props(
                    "color=orange-600"
                )

        dialog.open()

    def _open_edit_user_dialog(self, user: Dict):
        """Open dialog for editing user details"""
        dialog = ui.dialog()

        with dialog, ui.card().classes("w-96"):
            ui.label(f'Editar Usuario: {user.get("alias", "")}').classes("text-h6 mb-4")

            # Pre-filled input fields
            alias_input = ui.input("Alias *", value=user.get("alias", "")).classes(
                "w-full"
            )
            nombre_input = ui.input("Nombre *", value=user.get("nombre", "")).classes(
                "w-full"
            )
            apellidos_input = ui.input(
                "Apellidos", value=user.get("apellidos", "")
            ).classes("w-full")
            email_input = ui.input("Email", value=user.get("email", "")).classes(
                "w-full"
            )

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancelar", on_click=dialog.close).props("flat")

                async def update_user():
                    if not alias_input.value or not nombre_input.value:
                        ui.notify("Alias y nombre son obligatorios", type="warning")
                        return

                    user_data = {
                        "alias": alias_input.value.strip(),
                        "nombre": nombre_input.value.strip(),
                        "apellidos": apellidos_input.value.strip(),
                        "email": (
                            email_input.value.strip() if email_input.value else None
                        ),
                    }

                    try:
                        result = await self.api.update_record(
                            "usuarios", user["id"], user_data
                        )
                        if result:
                            ui.notify(
                                "Usuario actualizado exitosamente", type="positive"
                            )
                            dialog.close()
                            await self._load_data()
                    except Exception as e:
                        ui.notify(
                            f"Error al actualizar usuario: {str(e)}", type="negative"
                        )

                ui.button("Guardar Cambios", on_click=update_user).props(
                    "color=orange-600"
                )

        dialog.open()

    async def _open_roles_dialog(self, user: Dict):
        """Open dialog for managing user roles"""
        dialog = ui.dialog()

        # Get current roles
        current_role_ids = []
        try:
            user_role_links = await self.api.get_records(
                "usuario_roles", {"usuario_id": f"eq.{user['id']}"}
            )
            current_role_ids = [link["role_id"] for link in user_role_links]
        except Exception:
            pass

        with dialog, ui.card().classes("w-96"):
            ui.label(f'Gestionar Roles: {user.get("alias", "")}').classes(
                "text-h6 mb-4"
            )

            # Current roles display
            current_roles = [
                role["nombre"]
                for role in self.roles_list
                if role["id"] in current_role_ids
            ]

            ui.label("Roles actuales:").classes("text-subtitle2")
            if current_roles:
                with ui.row().classes("gap-1 mb-4"):
                    for role in current_roles:
                        ui.chip(role, color="orange").props("dense")
            else:
                ui.label("Sin roles asignados").classes("text-gray-500 mb-4")

            # Roles selection
            ui.label("Actualizar roles:").classes("text-subtitle2")
            roles_options = {role["id"]: role["nombre"] for role in self.roles_list}
            roles_select = ui.select(
                options=roles_options,
                multiple=True,
                value=current_role_ids,
                label="Seleccionar roles",
            ).classes("w-full")

            # Action buttons
            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancelar", on_click=dialog.close).props("flat")

                async def update_roles():
                    try:
                        # Delete existing user-role links
                        existing_links = await self.api.get_records(
                            "usuario_roles", {"usuario_id": f"eq.{user['id']}"}
                        )

                        for link in existing_links:
                            client = self.api._ensure_client()
                            url = f"{self.api.base_url}/usuario_roles?usuario_id=eq.{link['usuario_id']}&role_id=eq.{link['role_id']}"
                            try:
                                response = await client.delete(url)
                                response.raise_for_status()
                            except Exception as e:
                                print(f"Error deleting role link: {e}")

                        # Add new roles
                        if roles_select.value:
                            for role_id in roles_select.value:
                                role_data = {
                                    "usuario_id": user["id"],
                                    "role_id": role_id,
                                }
                                await self.api.create_record("usuario_roles", role_data)

                        ui.notify("Roles actualizados exitosamente", type="positive")
                        dialog.close()
                        await self._load_data()
                    except Exception as e:
                        ui.notify(
                            f"Error al actualizar roles: {str(e)}", type="negative"
                        )

                ui.button("Actualizar Roles", on_click=update_roles).props(
                    "color=orange-600"
                )

        dialog.open()

    def _open_password_dialog(self, user: Dict):
        """Open dialog for changing user password"""
        dialog = ui.dialog()

        with dialog, ui.card().classes("w-96"):
            ui.label(f'Cambiar Contraseña: {user.get("alias", "")}').classes(
                "text-h6 mb-4"
            )

            new_password = ui.input(
                "Nueva Contraseña *", password=True, password_toggle_button=True
            ).classes("w-full")
            confirm_password = ui.input(
                "Confirmar Contraseña *", password=True, password_toggle_button=True
            ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancelar", on_click=dialog.close).props("flat")

                async def change_password():
                    if not new_password.value or not confirm_password.value:
                        ui.notify("Ambos campos son obligatorios", type="warning")
                        return

                    if new_password.value != confirm_password.value:
                        ui.notify("Las contraseñas no coinciden", type="warning")
                        return

                    if len(new_password.value) < 6:
                        ui.notify(
                            "La contraseña debe tener al menos 6 caracteres",
                            type="warning",
                        )
                        return

                    try:
                        password_hash = pwd_context.hash(new_password.value)

                        # Check if credentials exist first
                        cred_records = await self.api.get_records(
                            "usuario_credenciales", {"usuario_id": f'eq.{user["id"]}'}
                        )

                        if cred_records:
                            # Update existing credentials
                            client = self.api._ensure_client()
                            url = f"{self.api.base_url}/usuario_credenciales?usuario_id=eq.{user['id']}"
                            headers = {"Prefer": "return=representation"}

                            response = await client.patch(
                                url,
                                json={"password_hash": password_hash},
                                headers=headers,
                            )
                            response.raise_for_status()

                            ui.notify(
                                "Contraseña actualizada exitosamente", type="positive"
                            )
                            dialog.close()
                        else:
                            # Create credentials if they don't exist
                            cred_data = {
                                "usuario_id": user["id"],
                                "password_hash": password_hash,
                            }
                            result = await self.api.create_record(
                                "usuario_credenciales", cred_data
                            )
                            if result:
                                ui.notify(
                                    "Contraseña creada exitosamente", type="positive"
                                )
                                dialog.close()
                            else:
                                ui.notify(
                                    "Error al crear la contraseña", type="negative"
                                )

                    except Exception as e:
                        ui.notify(
                            f"Error al cambiar contraseña: {str(e)}", type="negative"
                        )
                        print(f"Password change error for user {user['id']}: {str(e)}")

                ui.button("Cambiar Contraseña", on_click=change_password).props(
                    "color=orange-600"
                )

        dialog.open()

    def _open_roles_management(self):
        """Open dialog for managing available roles"""
        dialog = ui.dialog()

        with dialog, ui.card().classes("w-96"):
            ui.label("Gestión de Roles del Sistema").classes("text-h6 mb-4")

            # Current roles
            ui.label("Roles disponibles:").classes("text-subtitle2")
            roles_container = ui.column().classes("w-full gap-2 mb-4")

            async def refresh_roles():
                # Reload roles from database
                self.roles_list = await self.api.get_records(
                    "roles", order="nombre.asc"
                )

                roles_container.clear()
                with roles_container:
                    for role in self.roles_list:
                        with ui.row().classes("w-full items-center justify-between"):
                            ui.label(role["nombre"]).classes("flex-grow")
                            ui.button(
                                icon="delete",
                                on_click=lambda r=role: self._delete_role(
                                    r, refresh_roles
                                ),
                            ).props("size=sm flat dense color=negative")

            # Initial load
            ui.timer(0.1, refresh_roles, once=True)

            # Add new role
            ui.separator()
            ui.label("Crear nuevo rol:").classes("text-subtitle2 mt-4")
            new_role_input = ui.input(
                "Nombre del rol", placeholder="nuevo_rol"
            ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cerrar", on_click=dialog.close).props("flat")

                async def create_role():
                    if not new_role_input.value:
                        ui.notify("El nombre del rol es obligatorio", type="warning")
                        return

                    try:
                        role_data = {"nombre": new_role_input.value.strip().lower()}
                        result = await self.api.create_record("roles", role_data)

                        if result:
                            ui.notify("Rol creado exitosamente", type="positive")
                            new_role_input.value = ""
                            await self._load_data()
                            await refresh_roles()
                    except Exception as e:
                        ui.notify(f"Error al crear rol: {str(e)}", type="negative")

                ui.button("Crear Rol", on_click=create_role).props("color=orange-600")

        dialog.open()

    async def _delete_role(self, role: Dict, refresh_callback):
        """Delete a role with confirmation"""
        with ui.dialog() as confirm_dialog, ui.card():
            ui.label(f'¿Eliminar el rol "{role["nombre"]}"?').classes("text-h6")
            ui.label(
                "Esta acción no se puede deshacer y eliminará todas las asignaciones."
            ).classes("text-body2 text-gray-600")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=confirm_dialog.close).props("flat")

                async def confirm():
                    try:
                        success = await self.api.delete_record("roles", role["id"])
                        if success:
                            ui.notify("Rol eliminado exitosamente", type="positive")
                            await self._load_data()
                            await refresh_callback()
                            confirm_dialog.close()
                    except Exception as e:
                        ui.notify(f"Error al eliminar rol: {str(e)}", type="negative")

                ui.button("Eliminar", on_click=confirm).props("color=negative")

        confirm_dialog.open()
