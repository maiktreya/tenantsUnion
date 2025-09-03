# /build/niceGUI/views/views_explorer.py

from typing import Dict, Any
from nicegui import ui
from api.client import APIClient
from state.views_state import ViewsState
from components.data_table import DataTable
from components.filters import FilterPanel
from components.exporter import export_to_csv
from components.relationship_explorer import (
    RelationshipExplorer,
)  # IMPORT THE NEW COMPONENT
from config import VIEW_INFO, TABLE_INFO


class ViewsExplorerView:
    """Views explorer with enhanced client-side filtering and multi-sorting."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = ViewsState()
        self.data_table = None
        self.filter_panel = None
        self.detail_container = None
        self.relationship_explorer = None  # ADD INSTANCE VARIABLE

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
                on_row_click=self._on_row_click,
            )
            self.data_table.create()

            ui.separator().classes("my-4")
            self.detail_container = ui.column().classes("w-full")

            # INITIALIZE THE COMPONENT
            self.relationship_explorer = RelationshipExplorer(
                self.api, self.detail_container
            )

        return container

    async def _on_row_click(self, record: Dict):
        """Handles a row click by invoking the RelationshipExplorer component."""
        view_name = self.state.selected_view.value
        await self.relationship_explorer.show_details(record, view_name, is_view=True)

    # ... (the rest of the file remains the same)

    async def _load_view_data(self, view_name: str = None):
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
        await self._load_view_data()

    def _export_data(self):
        if self.state.selected_view.value:
            export_to_csv(
                self.state.filtered_records,
                f"{self.state.selected_view.value}_export.csv",
            )
