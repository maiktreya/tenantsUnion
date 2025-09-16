# /build/niceGUI/views/admin.py

from typing import Dict, Any
from nicegui import ui
from api.client import APIClient

# --- CHANGE: Import the new generic state from the central app_state module ---
from state.app_state import GenericViewState
from components.data_table import DataTable
from components.dialogs import EnhancedRecordDialog
from components.exporter import export_to_csv
from components.importer import CSVImporterDialog
from components.filters import FilterPanel
from components.relationship_explorer import RelationshipExplorer
from config import TABLE_INFO


class AdminView:
    """Enhanced admin view for table management with client-side UX."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        # --- CHANGE: Instantiate the new GenericViewState ---
        self.state = GenericViewState()
        self.data_table = None
        self.detail_container = None
        self.filter_panel = None
        self.relationship_explorer = None

    def create(self) -> ui.column:
        """Create the enhanced CRUD view UI."""
        container = ui.column().classes("w-full p-4 gap-4")

        with container:
            ui.label("Administración de Tablas y Registros BBDD").classes(
                "text-h6 font-italic"
            )

            with ui.row().classes("w-full gap-4 items-center"):
                # --- CHANGE: Bind the select component to the new 'selected_entity_name' property ---
                ui.select(
                    options=list(TABLE_INFO.keys()),
                    label="Seleccionar Tabla",
                    on_change=lambda e: ui.timer(
                        0.1, lambda: self._load_table_data(e.value), once=True
                    ),
                ).classes("w-64").bind_value_to(self.state.selected_entity_name)

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

            self.state.filter_container = ui.column().classes("w-full")

            self.data_table = DataTable(
                state=self.state,
                on_edit=self._edit_record,
                on_delete=self._delete_record,
                on_row_click=self._on_row_click,
            )
            self.data_table.create()

            ui.separator().classes("my-4")
            self.detail_container = ui.column().classes("w-full")

            self.relationship_explorer = RelationshipExplorer(
                self.api, self.detail_container
            )

        return container

    async def _on_row_click(self, record: Dict):
        """Handles a row click by invoking the RelationshipExplorer."""
        # --- CHANGE: Get the table name from the new 'selected_entity_name' property ---
        table_name = self.state.selected_entity_name.value
        await self.relationship_explorer.show_details(
            record, table_name, calling_view="admin"
        )

    async def _load_table_data(self, table_name: str = None):
        if self.detail_container:
            self.detail_container.clear()

        # --- CHANGE: Get the table name from the new 'selected_entity_name' property ---
        table = table_name or self.state.selected_entity_name.value
        if not table:
            return

        spinner = ui.spinner(size="lg", color="orange-600").classes("absolute-center")
        try:
            records = await self.api.get_records(table, limit=5000)
            self.state.set_records(records)
            self._setup_filters()
            self.data_table.refresh()
            ui.notify(f"Se cargaron {len(records)} registros", type="positive")
        except Exception as e:
            ui.notify(f"Error al cargar datos: {str(e)}", type="negative")
        finally:
            spinner.delete()

    def _setup_filters(self):
        if not self.state.filter_container or not self.state.records:
            if self.state.filter_container:
                self.state.filter_container.clear()
            return
        self.state.filter_container.clear()
        with self.state.filter_container:
            self.filter_panel = FilterPanel(
                records=self.state.records, on_filter_change=self._update_filter
            )
            self.filter_panel.create()

    def _update_filter(self, column: str, value: Any):
        self.state.filters[column] = value
        self.state.apply_filters_and_sort()
        self.data_table.refresh()

    def _clear_filters(self):
        self.state.filters.clear()
        if self.filter_panel:
            self.filter_panel.clear()
        self.state.apply_filters_and_sort()
        self.data_table.refresh()

    async def _refresh_data(self):
        await self._load_table_data()

    def _open_import_dialog(self):
        # --- CHANGE: Use the new 'selected_entity_name' property ---
        if not self.state.selected_entity_name.value:
            ui.notify("Por favor, seleccione una tabla primero", type="warning")
            return
        dialog = CSVImporterDialog(
            api=self.api,
            table_name=self.state.selected_entity_name.value,
            on_success=self._refresh_data,
        )
        dialog.open()

    async def _create_record(self):
        # --- CHANGE: Use the new 'selected_entity_name' property ---
        if not self.state.selected_entity_name.value:
            ui.notify("Por favor, seleccione una tabla primero", type="warning")
            return
        dialog = EnhancedRecordDialog(
            api=self.api,
            table=self.state.selected_entity_name.value,
            mode="create",
            on_success=lambda: ui.timer(0.1, self._refresh_data, once=True),
        )
        await dialog.open()

    async def _edit_record(self, record: Dict):
        # --- CHANGE: Use the new 'selected_entity_name' property ---
        dialog = EnhancedRecordDialog(
            api=self.api,
            table=self.state.selected_entity_name.value,
            record=record,
            mode="edit",
            on_success=lambda: ui.timer(0.1, self._refresh_data, once=True),
        )
        await dialog.open()

    async def _delete_record(self, record: Dict):
        record_id = record.get("id")
        with ui.dialog() as dialog, ui.card():
            ui.label(f"¿Eliminar registro #{record_id}?").classes("text-h6")
            ui.label("Esta acción no se puede deshacer.").classes(
                "text-body2 text-gray-600"
            )
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=dialog.close).props("flat")

                async def confirm():
                    # --- CHANGE: Use the new 'selected_entity_name' property ---
                    success = await self.api.delete_record(
                        self.state.selected_entity_name.value, record_id
                    )
                    if success:
                        ui.notify("Registro eliminado con éxito", type="positive")
                        dialog.close()
                        await self._refresh_data()

                ui.button("Eliminar", on_click=confirm).props("color=negative")
        dialog.open()

    def _export_data(self):
        # --- CHANGE: Use the new 'selected_entity_name' property ---
        export_to_csv(
            self.state.filtered_records,
            f"{self.state.selected_entity_name.value}_export.csv",
        )
