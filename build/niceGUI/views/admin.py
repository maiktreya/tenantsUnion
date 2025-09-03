from typing import Dict, List, Union, Any
from nicegui import ui
from api.client import APIClient
from state.admin_state import AdminState
from components.data_table import DataTable
from components.dialogs import EnhancedRecordDialog
from components.exporter import export_to_csv
from components.importer import CSVImporterDialog
from components.filters import FilterPanel
from config import config, TABLE_INFO

class AdminView:
    """Enhanced admin view for table management with client-side UX."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = AdminState()
        self.data_table = None
        self.detail_container = None
        self.filter_panel = None

    def create(self) -> ui.column:
        """Create the enhanced CRUD view UI."""
        container = ui.column().classes("w-full p-4 gap-4")

        with container:
            ui.label("Administración de Tablas y Registros BBDD").classes("text-h6 font-italic")

            with ui.row().classes("w-full gap-4 items-center"):
                ui.select(
                    options=list(TABLE_INFO.keys()),
                    label="Seleccionar Tabla",
                    on_change=lambda e: ui.timer(0.1, lambda: self._load_table_data(e.value), once=True)
                ).classes("w-64").bind_value_to(self.state.selected_table)
                ui.button("Refrescar", icon="refresh", on_click=self._refresh_data).props("color=orange-600")
                ui.button("Crear Nuevo", icon="add", on_click=self._create_record).props("color=orange-600")
                ui.button("Limpiar Filtros", icon="filter_alt_off", on_click=self._clear_filters).props("color=orange-600")
                ui.button("Exportar CSV", icon="download", on_click=self._export_data).props("color=orange-600")
                ui.button("Importar CSV", icon="upload", on_click=self._open_import_dialog).props("color=orange-600")

            self.state.filter_container = ui.column().classes("w-full")

            self.data_table = DataTable(
                state=self.state,
                on_edit=self._edit_record,
                on_delete=self._delete_record,
                on_row_click=self._show_record_details, # MODIFIED: Changed to the new enhanced function
            )
            self.data_table.create()

            ui.separator().classes("my-4")
            self.detail_container = ui.column().classes("w-full")

        return container

    async def _load_table_data(self, table_name: str = None):
        """Load data with robust spinner handling."""
        if self.detail_container:
            self.detail_container.clear()

        table = table_name or self.state.selected_table.value
        if not table:
            return

        spinner = ui.spinner(size='lg', color='orange-600').classes('absolute-center')
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
        """Setup the dynamic filter panel."""
        if not self.state.filter_container or not self.state.records:
            if self.state.filter_container:
                self.state.filter_container.clear()
            return

        self.state.filter_container.clear()
        with self.state.filter_container:
            self.filter_panel = FilterPanel(
                records=self.state.records,
                on_filter_change=self._update_filter
            )
            self.filter_panel.create()

    def _update_filter(self, column: str, value: Any):
        """Callback from FilterPanel to update state and refresh the table."""
        self.state.filters[column] = value
        self.state.apply_filters_and_sort()
        self.data_table.refresh()

    def _clear_filters(self):
        """Clear filters in the state and the UI panel."""
        self.state.filters.clear()
        if self.filter_panel:
            self.filter_panel.clear()
        self.state.apply_filters_and_sort()
        self.data_table.refresh()

    async def _refresh_data(self):
        """Refresh current table data."""
        await self._load_table_data()

    def _open_import_dialog(self):
        """Opens the CSV import dialog."""
        if not self.state.selected_table.value:
            ui.notify("Por favor, seleccione una tabla primero", type="warning")
            return
        dialog = CSVImporterDialog(
            api=self.api,
            table_name=self.state.selected_table.value,
            on_success=self._refresh_data,
        )
        dialog.open()

    # =================================================================================
    # NEW: ENHANCED BIDIRECTIONAL RELATIONSHIP EXPLORER
    # =================================================================================
    async def _show_record_details(self, record: Dict):
        """
        Handles a click on a row to show both parent and child related records.
        """
        self.detail_container.clear()
        selected_table_name = self.state.selected_table.value
        table_info = TABLE_INFO.get(selected_table_name, {})
        record_id = record.get("id")

        if record_id is None:
            return

        with self.detail_container:
            ui.label(f"Relaciones para '{selected_table_name}' (ID: {record_id})").classes("text-h5 mb-2")

            with ui.row().classes("w-full gap-4"):
                # --- Parent Relationships ---
                with ui.column().classes("w-1/2"):
                    await self._display_parent_relations(record, table_info)

                # --- Child Relationships ---
                with ui.column().classes("w-1/2"):
                    await self._display_child_relations(record_id, table_info)

    async def _display_parent_relations(self, record: Dict, table_info: Dict):
        """Fetches and displays parent records."""
        parent_relations = table_info.get("relations")
        if not parent_relations:
            return

        ui.label("Registros Padre (Este registro pertenece a):").classes("text-h6")
        with ui.card().classes("w-full"):
            for fk_field, relation_info in parent_relations.items():
                parent_id = record.get(fk_field)
                if parent_id is None:
                    continue

                parent_table = relation_info["view"]
                try:
                    parent_records = await self.api.get_records(parent_table, filters={"id": f"eq.{parent_id}"})
                    if not parent_records:
                        ui.label(f"No se encontró el padre en '{parent_table}' con ID {parent_id}").classes("text-red-500")
                        continue

                    parent_record = parent_records[0]
                    with ui.expansion(f"Padre en '{parent_table}' (ID: {parent_id})", icon="arrow_upward").classes("w-full"):
                        for key, value in parent_record.items():
                            with ui.row():
                                ui.label(f"{key}:").classes("font-semibold w-32")
                                ui.label(str(value))
                except Exception as e:
                    ui.notify(f"Error al cargar padre de '{parent_table}': {str(e)}", type="negative")

    async def _display_child_relations(self, record_id: int, table_info: Dict):
        """Fetches and displays child records."""
        child_relations = table_info.get("child_relations")
        if not child_relations:
            return

        if isinstance(child_relations, dict):
            child_relations = [child_relations]

        ui.label("Registros Hijos (Registros que pertenecen a este):").classes("text-h6")
        with ui.card().classes("w-full"):
            for relation in child_relations:
                child_table = relation["table"]
                foreign_key = relation["foreign_key"]
                try:
                    filters = {foreign_key: f"eq.{record_id}"}
                    related_records = await self.api.get_records(child_table, filters=filters)

                    with ui.expansion(f"Hijos en '{child_table}' ({len(related_records)})", icon="arrow_downward").classes("w-full"):
                        if not related_records:
                            ui.label("No se encontraron registros relacionados.").classes("text-gray-500 p-2")
                            continue

                        for rel_record in related_records:
                            with ui.card().classes("w-full my-1"):
                                for key, value in rel_record.items():
                                    with ui.row():
                                        ui.label(f"{key}:").classes("font-semibold w-32")
                                        ui.label(str(value))
                except Exception as e:
                    ui.notify(f"Error al cargar hijos de '{child_table}': {str(e)}", type="negative")

    # =================================================================================
    # END OF ENHANCEMENTS
    # =================================================================================

    async def _create_record(self):
        """Create a new record using the enhanced dialog."""
        if not self.state.selected_table.value:
            ui.notify("Por favor, seleccione una tabla primero", type="warning")
            return
        dialog = EnhancedRecordDialog(
            api=self.api,
            table=self.state.selected_table.value,
            mode="create",
            on_success=lambda: ui.timer(0.1, self._refresh_data, once=True),
        )
        await dialog.open()

    async def _edit_record(self, record: Dict):
        """Edit an existing record using the enhanced dialog."""
        dialog = EnhancedRecordDialog(
            api=self.api,
            table=self.state.selected_table.value,
            record=record,
            mode="edit",
            on_success=lambda: ui.timer(0.1, self._refresh_data, once=True),
        )
        await dialog.open()

    async def _delete_record(self, record: Dict):
        """Delete a record with confirmation"""
        record_id = record.get("id")
        with ui.dialog() as dialog, ui.card():
            ui.label(f"¿Eliminar registro #{record_id}?").classes("text-h6")
            ui.label("Esta acción no se puede deshacer.").classes("text-body2 text-gray-600")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=dialog.close).props("flat")
                async def confirm():
                    success = await self.api.delete_record(self.state.selected_table.value, record_id)
                    if success:
                        ui.notify("Registro eliminado con éxito", type="positive")
                        dialog.close()
                        await self._refresh_data()
                ui.button("Eliminar", on_click=confirm).props("color=negative")
        dialog.open()

    def _export_data(self):
        """Export filtered data to CSV"""
        export_to_csv(
            self.state.filtered_records, f"{self.state.selected_table.value}_export.csv"
        )