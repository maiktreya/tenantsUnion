# build/niceGUI/views/views_explorer.py (Enhanced for Client-Side State)

from typing import Dict, Any
from nicegui import ui, app

from api.client import APIClient
from state.app_state import GenericViewState  # We still use the class for its logic
from components.data_table import DataTable
from components.filters import FilterPanel
from components.exporter import export_to_csv
from components.relationship_explorer import RelationshipExplorer
from components.base_view import BaseView
from config import VIEW_INFO, TABLE_INFO, VIEW_ORDER


class ViewsExplorerView(BaseView):
    """Views explorer with client-side (per-tab) state."""

    def __init__(self, api_client: APIClient):
        self.api = api_client

        # --- STATE REFACTOR ---
        # Get or create the state from the client's (per-tab) storage.
        if "views_explorer_state" not in app.storage.client:
            app.storage.client["views_explorer_state"] = GenericViewState()
        self.state: GenericViewState = app.storage.client["views_explorer_state"]
        # --- END REFACTOR ---

        self.select_view = None
        self.data_table_container = None
        self.detail_container = None
        self.filter_panel = None
        self.relationship_explorer = None
        self.filter_container = None
        self.data_table_instance = None

    def create(self) -> ui.column:
        """Create the views explorer UI."""
        container = ui.column().classes("w-full p-4 gap-4")
        with container:
            ui.label("Explorador de Vistas").classes("text-h6 font-italic")
            with ui.row().classes("w-full gap-4 items-center"):
                # Create a dictionary mapping view names to their display names, in the desired order
                view_options = {
                    view_name: VIEW_INFO.get(view_name, {}).get(
                        "display_name", view_name
                    )
                    for view_name in VIEW_ORDER
                }

                self.select_view = ui.select(
                    options=view_options,
                    label="Seleccionar Vista",
                    value=self.state.selected_entity_name.value,
                    on_change=lambda e: ui.timer(
                        0.1, lambda: self._load_view_data(e.value), once=True
                    ),
                ).classes("w-64")

                ui.button(
                    "Limpiar Selección", icon="clear_all", on_click=self._clear_view
                ).props("color=grey-6")
                ui.button(
                    "Refrescar", icon="refresh", on_click=self._refresh_data
                ).props("color=orange-600")
                ui.button(
                    "Limpiar Filtros",
                    icon="filter_alt_off",
                    on_click=self._clear_filters,
                ).props("color=orange-600")
                if self.has_role("admin", "sistemas", "gestor"):
                    ui.button(
                        "Exportar CSV", icon="download", on_click=self._export_data
                    ).props("color=orange-600")

            self.filter_container = ui.column().classes("w-full")
            self.data_table_container = ui.column().classes("w-full")
            ui.separator().classes("my-4")
            self.detail_container = ui.column().classes("w-full")
            self.relationship_explorer = RelationshipExplorer(
                self.api, self.detail_container
            )

        # If a view was already selected in this tab, reload its data
        if self.state.selected_entity_name.value:
            ui.timer(0.1, self._refresh_data, once=True)

        return container

    def _clear_view(self):
        """Clears the current view state and UI elements."""
        self.state.clear_selection()
        if self.select_view:
            self.select_view.set_value(None)
        if self.data_table_container:
            self.data_table_container.clear()
        if self.filter_container:
            self.filter_container.clear()
        if self.detail_container:
            self.detail_container.clear()

    async def _load_view_data(self, view_name: str = None):
        """Loads data for the selected view and dynamically creates the data table."""
        self.state.selected_entity_name.set(view_name)

        self.data_table_container.clear()
        self.filter_container.clear()
        if self.detail_container:
            self.detail_container.clear()

        view = view_name or self.state.selected_entity_name.value
        if not view:
            self.state.set_records([])
            return

        with self.data_table_container:
            spinner = ui.spinner(size="lg", color="orange-600").classes(
                "absolute-center"
            )
            try:
                records = await self.api.get_records(view, limit=5000)

                view_config = VIEW_INFO.get(view, {})
                base_table_name = view_config.get("base_table")
                if not base_table_name:
                    ui.notify(
                        f"Error: No se ha configurado 'base_table' para la vista '{view}'",
                        type="negative",
                    )
                    spinner.delete()
                    return

                base_table_config = TABLE_INFO.get(base_table_name, {})

                self.state.set_records(records, base_table_config)

                self._setup_filters(base_table_config)

                view_config = VIEW_INFO.get(view, {})
                hidden_fields = view_config.get("hidden_fields", [])

                table_instance = DataTable(
                    state=self.state,
                    show_actions=False,
                    on_row_click=self._on_row_click,
                    hidden_columns=hidden_fields,
                )
                table_instance.create()
                self.data_table_instance = table_instance

                if records:
                    ui.notify(
                        f"Se cargaron {len(records)} registros de la vista",
                        type="positive",
                    )
            except Exception as e:
                ui.notify(
                    f"Error al cargar datos de la vista: {str(e)}", type="negative"
                )
            finally:
                spinner.delete()

    async def _on_row_click(self, record: Dict):
        view_name = self.state.selected_entity_name.value
        if view_name:
            await self.relationship_explorer.show_details(record, view_name, "views")

    def _setup_filters(self, base_table_config: Dict):
        self.filter_container.clear()
        with self.filter_container:
            self.filter_panel = FilterPanel(
                records=self.state.records,
                on_filter_change=self._update_filter,
                table_config=base_table_config,
            )
            self.filter_panel.create()

    def _update_filter(self, column: str, value: Any):
        self.state.filters[column] = value
        self.state.apply_filters_and_sort()
        if self.data_table_instance:
            self.data_table_instance.refresh()

    def _clear_filters(self):
        self.state.filters.clear()
        if self.filter_panel:
            self.filter_panel.clear()
        self.state.apply_filters_and_sort()
        if self.data_table_instance:
            self.data_table_instance.refresh()

    async def _refresh_data(self):
        if self.state.selected_entity_name.value:
            await self.load_view_data(self.state.selected_entity_name.value)

    def _export_data(self):
        if self.state.selected_entity_name.value:
            export_to_csv(
                self.state.filtered_records,
                f"{self.state.selected_entity_name.value}_export.csv",
            )
