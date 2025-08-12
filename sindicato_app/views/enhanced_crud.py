from typing import Dict
from nicegui import ui
from api.client import APIClient
from state.admin_state import AdminState
from components.data_table import DataTable
from components.dialogs import EnhancedRecordDialog
from utils.export import export_to_csv
from config import config, TABLE_INFO


class EnhancedCrudView:
    """Enhanced admin view for table management with dropdowns for foreign keys."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = AdminState()
        self.data_table = None
        self.detail_container = None  # Placeholder for the detail section

    def create(self) -> ui.column:
        """Create the enhanced CRUD view UI."""
        container = ui.column().classes("w-full p-4 gap-4")

        with container:
            ui.label("Administración de Tablas (Mejorada)").classes("text-h4")

            # Toolbar
            with ui.row().classes("w-full gap-4 items-center"):
                ui.select(
                    options=list(TABLE_INFO.keys()),
                    label="Seleccionar Tabla",
                    on_change=lambda e: ui.timer(
                        0.1, lambda: self._load_table_data(e.value), once=True
                    ),
                ).classes("w-64").bind_value_to(self.state.selected_table)

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

            # Filters
            with ui.expansion("Filtros y Búsqueda", icon="filter_list").classes(
                "w-full"
            ).props("default-opened"):
                self.state.filter_container = ui.column().classes("w-full")

            # Data table with the new row click handler
            self.data_table = DataTable(
                state=self.state,
                on_edit=self._edit_record,
                on_delete=self._delete_record,
                on_row_click=self._on_row_click,  # Pass the handler
            )
            self.data_table.create()

            # Separator and container for the dependency details
            ui.separator().classes("my-4")
            self.detail_container = ui.column().classes("w-full")

        return container

    # REPLACE the existing _on_row_click method with this one.
    async def _on_row_click(self, record: Dict):
        """Handles a click on a row to show related 'child' records."""
        self.detail_container.clear()
        selected_table_name = self.state.selected_table.value
        table_info = TABLE_INFO.get(selected_table_name, {})
        child_relation = table_info.get("child_relations")

        if not child_relation:
            return

        child_table = child_relation["table"]
        foreign_key = child_relation["foreign_key"]
        record_id = record.get("id")

        if record_id is None:
            return

        with self.detail_container:
            ui.label(
                f"Registros de '{child_table}' relacionados con '{selected_table_name}' (ID: {record_id})"
            ).classes("text-h6 mb-2")

            try:
                filters = {foreign_key: f"eq.{record_id}"}
                related_records = await self.api.get_records(
                    child_table, filters=filters
                )

                if not related_records:
                    ui.label("No se encontraron registros relacionados.").classes(
                        "text-gray-500"
                    )
                    return

                # NEW FORMATTING LOGIC STARTS HERE
                # Use a grid layout to nicely arrange the cards.
                with ui.grid(columns=2).classes("w-full gap-4"):
                    for rel_record in related_records:
                        # Create a separate card for each related record.
                        with ui.card().classes("w-full"):
                            # Display each key-value pair on its own row for clarity.
                            for key, value in rel_record.items():
                                with ui.row().classes("w-full"):
                                    ui.label(f"{key}:").classes("font-semibold w-32")
                                    ui.label(str(value)).classes("flex-grow")
                # NEW FORMATTING LOGIC ENDS HERE

            except Exception as e:
                ui.notify(
                    f"Error al cargar registros relacionados: {str(e)}", type="negative"
                )

    async def _load_table_data(self, table_name: str = None):
        """Load data for the selected table and clear the detail view."""
        if self.detail_container:
            self.detail_container.clear()

        table = table_name or self.state.selected_table.value
        if not table:
            return

        try:
            records = await self.api.get_records(table)
            self.state.set_records(records)
            self._setup_filters()
            self.data_table.refresh()
            ui.notify(f"Se cargaron {len(records)} registros", type="positive")
        except Exception as e:
            ui.notify(f"Error al cargar datos: {str(e)}", type="negative")

    def _setup_filters(self):
        """Setup filter inputs"""
        if not self.state.filter_container or not self.state.records:
            return

        self.state.filter_container.clear()
        columns = list(self.state.records[0].keys())

        with self.state.filter_container:
            ui.label("Filtros").classes("text-h6 mb-2")
            with ui.row().classes("w-full gap-2 flex-wrap"):
                for column in columns:
                    ui.input(
                        label=f"Filtrar {column}",
                        on_change=lambda e, col=column: self._update_filter(
                            col, e.value
                        ),
                    ).classes("w-48").props("dense clearable")

    def _update_filter(self, column: str, value: str):
        """Update filter for a column"""
        self.state.filters[column] = value
        self.state.apply_filters()
        self.data_table.refresh()

    def _clear_filters(self):
        """Clear all filters"""
        self.state.clear_filters()
        self._setup_filters()
        self.data_table.refresh()

    async def _refresh_data(self):
        """Refresh current table data"""
        await self._load_table_data()

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
            ui.label("Esta acción no se puede deshacer.").classes(
                "text-body2 text-gray-600"
            )

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=dialog.close).props("flat")

                async def confirm():
                    success = await self.api.delete_record(
                        self.state.selected_table.value, record_id
                    )
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
