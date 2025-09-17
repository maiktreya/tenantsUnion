# build/niceGUI/views/admin.py

from typing import Dict, Any
from nicegui import ui

from api.client import APIClient
from state.app_state import AppState
from components.data_table import DataTable
from components.dialogs import EnhancedRecordDialog, ConfirmationDialog
from components.exporter import export_to_csv
from components.importer import CSVImporterDialog
from components.filters import FilterPanel
from components.relationship_explorer import RelationshipExplorer
from components.base_view import BaseView
from config import TABLE_INFO


class AdminView(BaseView):
    """Enhanced admin view for table management with client-side UX."""

    def __init__(self, api_client: APIClient, state: AppState):
        self.api = api_client
        self.state = state.admin
        self.select_table = None
        self.data_table_container = None
        self.detail_container = None
        self.filter_panel = None
        self.relationship_explorer = None
        # --- FIX: The view, not the state, will own the filter container ---
        self.filter_container = None

    def create(self) -> ui.column:
        """Create the enhanced CRUD view UI."""
        container = ui.column().classes("w-full p-4 gap-4")
        with container:
            ui.label("Administración de Tablas y Registros BBDD").classes(
                "text-h6 font-italic"
            )
            with ui.row().classes("w-full gap-4 items-center"):
                self.select_table = ui.select(
                    options=list(TABLE_INFO.keys()),
                    label="Seleccionar Tabla",
                    on_change=lambda e: ui.timer(
                        0.1, lambda: self._load_table_data(e.value), once=True
                    ),
                ).classes("w-64")

                ui.button(
                    "Limpiar Selección",
                    icon="clear_all",
                    on_click=self.clear_view_internals,
                ).props("color=grey-6")

                ui.button(
                    "Refrescar", icon="refresh", on_click=self._refresh_data
                ).props("color=orange-600")
                ui.button(
                    "Crear Nuevo", icon="add", on_click=self._create_record
                ).props("color=orange-600")
                ui.button(
                    "Limpiar Filtros",
                    icon="filter_alt_off",
                    on_click=self._clear_filters,
                ).props("color=orange-600")
                ui.button(
                    "Exportar CSV", icon="download", on_click=self._export_data
                ).props("color=orange-600")
                ui.button(
                    "Importar CSV", icon="upload", on_click=self._open_import_dialog
                ).props("color=orange-600")

            # --- FIX: Assign the UI element to the view's attribute ---
            self.filter_container = ui.column().classes("w-full")
            self.data_table_container = ui.column().classes("w-full")
            ui.separator().classes("my-4")
            self.detail_container = ui.column().classes("w-full")
            self.relationship_explorer = RelationshipExplorer(
                self.api, self.detail_container
            )
        return container

    async def _load_table_data(self, table_name: str = None):
        """Loads data and dynamically creates the data table."""
        self.state.selected_entity_name.set(table_name)

        # --- FIX: Reference the view's container attribute ---
        self.data_table_container.clear()
        self.filter_container.clear()
        if self.detail_container:
            self.detail_container.clear()

        table = table_name or self.state.selected_entity_name.value
        if not table:
            self.state.set_records([])
            return

        with self.data_table_container:
            spinner = ui.spinner(size="lg", color="orange-600").classes(
                "absolute-center"
            )
            try:
                records = await self.api.get_records(table, limit=5000)
                self.state.set_records(records)
                self._setup_filters()
                DataTable(
                    state=self.state,
                    on_edit=self._edit_record,
                    on_delete=self._delete_record,
                    on_row_click=self._on_row_click,
                ).create()
            except Exception as e:
                ui.notify(f"Error al cargar datos: {str(e)}", type="negative")
            finally:
                if not spinner.client.is_deleted:
                    spinner.delete()

    async def _on_row_click(self, record: Dict):
        """Handles a row click by invoking the RelationshipExplorer."""
        await self.relationship_explorer.show_details(
            record, self.state.selected_entity_name.value, "admin"
        )

    def _setup_filters(self):
        """Initializes the filter panel based on the loaded data."""
        # --- FIX: Reference the view's container attribute ---
        self.filter_container.clear()
        with self.filter_container:
            self.filter_panel = FilterPanel(
                records=self.state.records, on_filter_change=self._update_filter
            )
            self.filter_panel.create()

    def _update_filter(self, column: str, value: Any):
        """Callback to update the state when a filter changes."""
        self.state.filters[column] = value
        self.state.apply_filters_and_sort()

    def _clear_filters(self):
        """Clears all active filters and refreshes the view."""
        self.state.filters.clear()
        if self.filter_panel:
            self.filter_panel.clear()
        self.state.apply_filters_and_sort()

    async def _refresh_data(self):
        """Reloads data for the currently selected table."""
        if self.state.selected_entity_name.value:
            await self._load_table_data(self.state.selected_entity_name.value)

    def _open_import_dialog(self):
        """Opens the CSV import dialog."""
        if not self.state.selected_entity_name.value:
            return ui.notify("Por favor, seleccione una tabla primero", type="warning")
        dialog = CSVImporterDialog(
            api=self.api,
            table_name=self.state.selected_entity_name.value,
            on_success=self._refresh_data,
        )
        dialog.open()

    async def _create_record(self):
        """Opens a dialog to create a new record."""
        if not self.state.selected_entity_name.value:
            return ui.notify("Por favor, seleccione una tabla primero", type="warning")
        dialog = EnhancedRecordDialog(
            api=self.api,
            table=self.state.selected_entity_name.value,
            mode="create",
            on_success=lambda: ui.timer(0.1, self._refresh_data, once=True),
        )
        await dialog.open()

    async def _edit_record(self, record: Dict):
        """Opens a dialog to edit an existing record."""
        dialog = EnhancedRecordDialog(
            api=self.api,
            table=self.state.selected_entity_name.value,
            record=record,
            mode="edit",
            on_success=lambda: ui.timer(0.1, self._refresh_data, once=True),
        )
        await dialog.open()

    def _delete_record(self, record: Dict):
        """Shows a confirmation dialog before deleting a record."""
        record_id = record.get(
            TABLE_INFO.get(self.state.selected_entity_name.value, {}).get(
                "id_field", "id"
            )
        )
        ConfirmationDialog(
            title=f"¿Eliminar registro #{record_id}?",
            message="Esta acción no se puede deshacer.",
            on_confirm=lambda: self._confirm_delete(record_id),
            confirm_button_text="Eliminar",
            confirm_button_color="negative",
        )

    async def _confirm_delete(self, record_id: int):
        """Performs the actual deletion after confirmation."""
        if await self.api.delete_record(
            self.state.selected_entity_name.value, record_id
        ):
            ui.notify("Registro eliminado con éxito", type="positive")
            await self._refresh_data()

    def _export_data(self):
        """Exports the currently filtered data to a CSV file."""
        if self.state.selected_entity_name.value:
            export_to_csv(
                self.state.filtered_records,
                f"{self.state.selected_entity_name.value}_export.csv",
            )
