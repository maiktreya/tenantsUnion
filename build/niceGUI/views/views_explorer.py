# /build/niceGUI/views/views_explorer.py
from typing import Dict, Any
from nicegui import ui, app

from api.client import APIClient

from state.app_state import GenericViewState

from components.data_table import DataTable
from components.filters import FilterPanel
from components.exporter import export_to_csv
from components.relationship_explorer import RelationshipExplorer
from components.base_view import BaseView

from config import VIEW_INFO


class ViewsExplorerView(BaseView):  # MODIFIED: Inherit from BaseView
    """Views explorer with enhanced client-side filtering and multi-sorting."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = GenericViewState()
        self.data_table_container = None
        self.filter_panel = None
        self.detail_container = None
        self.relationship_explorer = None

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
                ).classes("w-64").bind_value_to(self.state.selected_entity_name)

                ui.button(
                    "Refrescar", icon="refresh", on_click=self._refresh_data
                ).props("color=orange-600")
                ui.button(
                    "Limpiar Filtros",
                    icon="filter_alt_off",
                    on_click=self._clear_filters,
                ).props("color=orange-600")

                if self.has_role("admin", "sistemas"):
                    ui.button(
                        "Exportar CSV", icon="download", on_click=self._export_data
                    ).props("color=orange-600")

            self.state.filter_container = ui.column().classes("w-full")

            self.data_table_container = ui.column().classes("w-full")

            ui.separator().classes("my-4")
            self.detail_container = ui.column().classes("w-full")

            self.relationship_explorer = RelationshipExplorer(
                self.api, self.detail_container
            )

        return container

    async def _on_row_click(self, record: Dict):
        """Handles a row click by invoking the RelationshipExplorer."""
        view_name = self.state.selected_entity_name.value
        await self.relationship_explorer.show_details(
            record, view_name, calling_view="views"
        )

    async def _load_view_data(self, view_name: str = None):
        """Loads data for the selected view and dynamically creates the data table."""
        if self.detail_container:
            self.detail_container.clear()

        view = view_name or self.state.selected_entity_name.value
        if not view:
            return

        if self.data_table_container:
            self.data_table_container.clear()

        spinner = ui.spinner(size="lg", color="orange-600").classes("absolute-center")
        try:
            records = await self.api.get_records(view, limit=5000)
            self.state.set_records(records)
            self._setup_filters()

            with self.data_table_container:
                view_config = VIEW_INFO.get(view, {})
                hidden_fields = view_config.get("hidden_fields", [])

                data_table = DataTable(
                    state=self.state,
                    show_actions=False,
                    on_row_click=self._on_row_click,
                    hidden_columns=hidden_fields,
                )
                data_table.create()

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
        # The table will auto-refresh due to its subscription to the state.

    def _clear_filters(self):
        self.state.filters.clear()
        if self.filter_panel:
            self.filter_panel.clear()
        self.state.apply_filters_and_sort()
        # The table will auto-refresh due to its subscription to the state.

    async def _refresh_data(self):
        await self._load_view_data()

    def _export_data(self):
        if self.state.selected_entity_name.value:
            export_to_csv(
                self.state.filtered_records,
                f"{self.state.selected_entity_name.value}_export.csv",
            )
