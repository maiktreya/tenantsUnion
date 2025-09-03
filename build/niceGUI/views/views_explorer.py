from typing import Dict, Any
from nicegui import ui
from api.client import APIClient
from state.views_state import ViewsState
from components.data_table import DataTable
from components.filters import FilterPanel
from components.exporter import export_to_csv
from config import VIEW_INFO, TABLE_INFO


class ViewsExplorerView:
    """Views explorer with enhanced client-side filtering and multi-sorting."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = ViewsState()
        self.data_table = None
        self.filter_panel = None
        self.detail_container = None

    def create(self) -> ui.column:
        """Create the views explorer UI."""
        container = ui.column().classes("w-full p-4 gap-4")

        with container:
            ui.label("Explorador de Vistas").classes("text-h4")

            with ui.row().classes("w-full gap-4 items-center"):
                ui.select(
                    options=list(VIEW_INFO.keys()),
                    label="Seleccionar Vista",
                    on_change=lambda e: ui.timer(
                        0.1, lambda: self._load_view_data(e.value), once=True
                    ),
                ).classes("w-64").bind_value_to(self.state.selected_view)

                ui.button(
                    "Refrescar", icon="refresh", on_click=self._refresh_data
                ).props("color=orange-600")
                ui.button(
                    "Limpiar Filtros",
                    icon="filter_alt_off",
                    on_click=self._clear_filters,
                ).props("color=orange-600")
                ui.button(
                    "Exportar CSV", icon="download", on_click=self._export_data
                ).props("color=orange-600")

            self.state.filter_container = ui.column().classes("w-full")

            self.data_table = DataTable(
                state=self.state,
                show_actions=False,
                on_row_click=self._show_record_details,
            )
            self.data_table.create()

            ui.separator().classes("my-4")
            self.detail_container = ui.column().classes("w-full")

        return container

    async def _load_view_data(self, view_name: str = None):
        """Load data, then set up the client-side filters and table."""
        if self.detail_container:
            self.detail_container.clear()

        view = view_name or self.state.selected_view.value
        if not view:
            return

        spinner = ui.spinner(size="lg", color="orange-600").classes("absolute-center")
        try:
            records = await self.api.get_records(view, limit=5000)
            self.state.set_records(records)
            self._setup_filters()
            self.data_table.refresh()
            ui.notify(
                f"Se cargaron {len(records)} registros de la vista", type="positive"
            )
        except Exception as e:
            ui.notify(f"Error al cargar datos de la vista: {str(e)}", type="negative")
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
                records=self.state.records, on_filter_change=self._update_filter
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
        """Refresh current view data."""
        await self._load_view_data()

    def _export_data(self):
        """Export filtered data to CSV."""
        if self.state.selected_view.value:
            export_to_csv(
                self.state.filtered_records,
                f"{self.state.selected_view.value}_export.csv",
            )

    # =================================================================================
    # NEW: ROBUST BIDIRECTIONAL RELATIONSHIP EXPLORER
    # =================================================================================
    async def _show_record_details(self, record: Dict):
        """Handles a click on a row to show related records."""
        self.detail_container.clear()
        view_name = self.state.selected_view.value
        if not view_name:
            return

        base_table_name = view_name[2:] if view_name.startswith("v_") else view_name
        table_info = TABLE_INFO.get(base_table_name, {})

        # New robust ID finding logic
        primary_key_name = table_info.get("id_field", "id")
        record_id = record.get(primary_key_name)
        if record_id is None:
            record_id = record.get("id")

        if record_id is None:
            ui.notify(
                f"La vista '{view_name}' no contiene un campo '{primary_key_name}' o 'id' para buscar relaciones.",
                type="warning",
            )
            return

        with self.detail_container:
            ui.label(
                f"Relaciones para el registro de '{view_name}' (ID: {record_id})"
            ).classes("text-h5 mb-2")
            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("w-1/2"):
                    await self._display_parent_relations(record, table_info)
                with ui.column().classes("w-1/2"):
                    await self._display_child_relations(record_id, table_info)

    async def _display_parent_relations(self, record: Dict, table_info: Dict):
        """Fetches and displays parent records."""
        parent_relations = table_info.get("relations")
        if not parent_relations:
            return

        ui.label("Registros Padre:").classes("text-h6")
        with ui.card().classes("w-full"):
            for fk_field, rel_info in parent_relations.items():
                parent_id = record.get(fk_field)
                if parent_id is None:
                    continue
                parent_table = rel_info["view"]
                try:
                    parents = await self.api.get_records(
                        parent_table, filters={"id": f"eq.{parent_id}"}
                    )
                    if not parents:
                        continue
                    with ui.expansion(
                        f"Padre en '{parent_table}' (ID: {parent_id})",
                        icon="arrow_upward",
                    ).classes("w-full"):
                        for key, value in parents[0].items():
                            with ui.row():
                                ui.label(f"{key}:").classes("font-semibold w-32")
                                ui.label(str(value))
                except Exception as e:
                    ui.notify(
                        f"Error al cargar padre de '{parent_table}': {str(e)}",
                        type="negative",
                    )

    async def _display_child_relations(self, record_id: int, table_info: Dict):
        """Fetches and displays child records."""
        child_relations = table_info.get("child_relations", [])
        child_relations = (
            [child_relations] if isinstance(child_relations, dict) else child_relations
        )
        if not child_relations:
            return

        ui.label("Registros Hijos:").classes("text-h6")
        with ui.card().classes("w-full"):
            for relation in child_relations:
                child_table, fk = relation["table"], relation["foreign_key"]
                try:
                    children = await self.api.get_records(
                        child_table, filters={fk: f"eq.{record_id}"}
                    )
                    with ui.expansion(
                        f"Hijos en '{child_table}' ({len(children)})",
                        icon="arrow_downward",
                    ).classes("w-full"):
                        if not children:
                            ui.label("No se encontraron registros.").classes(
                                "text-gray-500 p-2"
                            )
                            continue
                        for child in children:
                            with ui.card().classes("w-full my-1"):
                                for key, value in child.items():
                                    with ui.row():
                                        ui.label(f"{key}:").classes(
                                            "font-semibold w-32"
                                        )
                                        ui.label(str(value))
                except Exception as e:
                    ui.notify(
                        f"Error al cargar hijos de '{child_table}': {str(e)}",
                        type="negative",
                    )
