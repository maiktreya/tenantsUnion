from typing import Callable
from nicegui import ui


class HomeView:
    """Home page view"""

    def __init__(self, navigate: Callable[[str], None]):
        self.navigate = navigate

    def create(self) -> ui.column:
        """Create the home view UI"""
        container = ui.column().classes("w-full p-8 items-center gap-8")

        with container:
            ui.label(
                "Bienvenido al Sistema de Gestión del Sindicato de Inquilinas de Madrid"
            ).classes("text-h5 font-italic text-center")

            with ui.row().classes("gap-8 flex-wrap justify-center"):
                # Admin card
                self._create_card(
                    icon="storage",
                    title="Administración de Tablas",
                    description="Gestionar todas las tablas de la base de datos con operaciones CRUD completas",
                    on_click=lambda: self.navigate("admin"),
                )

                # Views card
                self._create_card(
                    icon="table_view",
                    title="Explorador de Vistas",
                    description="Explorar datos de vistas materializadas predefinidas",
                    on_click=lambda: self.navigate("views"),
                )

                # Conflicts card
                self._create_card(
                    icon="gavel",
                    title="Gestor de Conflictos",
                    description="Añadir notas y seguir el historial de conflictos",
                    on_click=lambda: self.navigate("conflicts"),
                )

                # New User Management card
                self._create_card(
                    icon="people",
                    title="Gestión de Usuarios",
                    description="Crear usuarios y administrar roles del sistema",
                    on_click=lambda: self.navigate("user_management"),
                )

        return container

    def _create_card(self, icon: str, title: str, description: str, on_click: Callable):
        """Create a navigation card"""
        with ui.card().classes(
            "w-80 cursor-pointer hover:shadow-lg transition-shadow"
        ).on("click", on_click):
            with ui.column().classes("items-center gap-4 p-4"):
                ui.icon(icon, size="4rem").classes("text-orange-600")
                ui.label(title).classes("text-h6")
                ui.label(description).classes("text-center text-gray-600")