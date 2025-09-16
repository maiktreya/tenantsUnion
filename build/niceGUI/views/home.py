from typing import Callable
from nicegui import ui, app
from components.base_view import BaseView


class HomeView(BaseView):  # MODIFIED: Inherit from BaseView
    """Home page view with role-based card visibility"""

    def __init__(self, navigate: Callable[[str], None]):
        self.navigate = navigate

    # REMOVED: The redundant 'has_role' method has been deleted from this class.

    def create(self) -> ui.column:
        """Create the home view UI with role-based card visibility"""
        container = ui.column().classes("w-full p-8 items-center gap-8")

        with container:
            # Welcome message with user info
            username = app.storage.user.get("username", "Usuario")
            roles = app.storage.user.get("roles", [])

            ui.label(
                "Bienvenido al Sistema de Gestión del Sindicato de Inquilinas de Madrid"
            ).classes("text-h5 font-italic text-center")

            # Show current user and roles
            if roles:
                ui.label(f"Usuario: {username} | Roles: {', '.join(roles)}").classes(
                    "text-subtitle1 text-gray-600 text-center"
                )
            else:
                ui.label(f"Usuario: {username} | Sin roles asignados").classes(
                    "text-subtitle1 text-gray-600 text-center"
                )

            with ui.row().classes("gap-8 flex-wrap justify-center"):
                # Admin card - only for admin/sistemas roles
                if self.has_role("admin", "sistemas"):
                    self._create_card(
                        icon="storage",
                        title="Administración de Tablas",
                        description="Gestionar todas las tablas de la base de datos con operaciones CRUD completas.",
                        on_click=lambda: self.navigate("admin"),
                        color="text-orange-600",
                    )
                    self._create_card(
                        icon="people",
                        title="Gestión de Usuarios",
                        description="Crear usuarios del sistema y administrar sus roles de acceso.",
                        on_click=lambda: self.navigate("user_management"),
                        color="text-orange-600",
                    )

                # Views and Importer cards - for admin/gestor roles
                if self.has_role("admin", "gestor"):
                    self._create_card(
                        icon="table_view",
                        title="Explorador de Vistas",
                        description="Explorar datos consolidados de solo lectura para análisis.",
                        on_click=lambda: self.navigate("views"),
                        color="text-orange-600",
                    )
                    # Form importer card - for admin/gestor roles
                    self._create_card(
                        icon="upload_file",
                        title="Importar Afiliadas",
                        description="Cargar nuevas afiliadas desde un archivo CSV de WordPress.",
                        on_click=lambda: self.navigate("afiliadas_importer"),
                        color="text-orange-600",
                    )

                # Conflicts card - for admin/gestor/actas roles
                if self.has_role("admin", "gestor", "actas"):
                    self._create_card(
                        icon="gavel",
                        title="Gestor de Conflictos",
                        description="Añadir notas y seguir el historial detallado de los conflictos.",
                        on_click=lambda: self.navigate("conflicts"),
                        color="text-orange-600",
                    )

                # User Profile - available to all authenticated users
                self._create_card(
                    icon="account_circle",
                    title="Mi Perfil",
                    description="Ver y editar mi información personal y cambiar mi contraseña.",
                    on_click=lambda: self.navigate("user_profile"),
                    color="text-orange-600",
                )

            # Show message if user has no accessible features
            if not self.has_role("admin", "gestor", "sistemas", "actas"):
                with ui.card().classes("w-full max-w-2xl mt-8 p-6"):
                    ui.label("Acceso Limitado").classes("text-h6 text-gray-700 mb-2")
                    ui.label(
                        "Tu cuenta tiene acceso limitado. Solo puedes gestionar tu perfil personal. "
                        "Si necesitas acceso adicional, contacta con un administrador del sistema."
                    ).classes("text-gray-600")

        return container

    def _create_card(
        self,
        icon: str,
        title: str,
        description: str,
        on_click: Callable,
        color: str = "text-orange-600",
    ):
        """Create a navigation card with customizable color"""
        with ui.card().classes(
            "w-80 h-64 cursor-pointer hover:shadow-xl transition-shadow flex flex-col justify-center"
        ).on("click", on_click):
            with ui.column().classes("items-center gap-4 p-4"):
                ui.icon(icon, size="4rem").classes(color)
                ui.label(title).classes("text-h6 text-center")
                ui.label(description).classes("text-center text-gray-600")
