# build/niceGUI/views/views_explorer.py (Refactored & Secure)

from typing import Dict, Any, Optional
from nicegui import ui, app

from api.client import APIClient
from state.app_state import GenericViewState
from components.data_table import DataTable
from components.filters import FilterPanel
from components.exporter import export_to_csv
from components.relationship_explorer import RelationshipExplorer
from components.base_view import BaseView
from config import VIEW_INFO, TABLE_INFO, VIEW_ORDER


class ViewsExplorerView(BaseView):
    """Views explorer with client-side (per-tab) state and role-based filtering."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        # Get or create the client-side state from the per-tab storage safely
        if "views_explorer_state" not in app.storage.client:
            app.storage.client["views_explorer_state"] = GenericViewState()
        self.state: GenericViewState = app.storage.client["views_explorer_state"]
        
        # UI Element References
        self.select_view = None
        self.data_table_container = None
        self.filter_container = None
        self.detail_container = None
        self.filter_panel = None
        self.relationship_explorer = None
        self.data_table_instance = None

    def create(self) -> ui.column:
        """Create the views explorer UI."""
        container = ui.column().classes("w-full p-4 gap-4")
        with container:
            ui.label("Explorador de Vistas").classes("text-h6 font-italic")
            
            with ui.row().classes("w-full gap-4 items-center"):
                # Build view options filtering out views restricted for the user's role
                view_options = {}
                for view_name in VIEW_ORDER:
                    view_config = VIEW_INFO.get(view_name, {})
                    excluded = view_config.get("excluded_roles", [])
                    if excluded and any(self.has_role(role) for role in excluded):
                        continue
                    view_options[view_name] = view_config.get("display_name", view_name)

                self.select_view = ui.select(
                    options=view_options,
                    label="Seleccionar Vista",
                    value=self.state.selected_entity_name.value,
                    on_change=lambda e: self._load_view_data(e.value),
                ).classes("w-64")

                ui.button("Limpiar Selección", icon="clear_all", on_click=self._clear_view).props("color=grey-6")
                ui.button("Refrescar", icon="refresh", on_click=self._refresh_data).props("color=orange-600")
                ui.button("Limpiar Filtros", icon="filter_alt_off", on_click=self._clear_filters).props("color=orange-600")
                
                if self.has_role("admin", "sistemas", "gestor"):
                    ui.button("Exportar CSV", icon="download", on_click=self._export_data).props("color=orange-600")

            # Layout structural placeholders
            self.filter_container = ui.column().classes("w-full")
            self.data_table_container = ui.column().classes("w-full")
            ui.separator().classes("my-4")
            self.detail_container = ui.column().classes("w-full")
            self.relationship_explorer = RelationshipExplorer(self.api, self.detail_container)

        # Trigger automatic reload if a view was already selected in this specific tab context
        if self.state.selected_entity_name.value:
            ui.timer(0.1, self._refresh_data, once=True)

        return container

    def _clear_ui_containers(self):
        """Helper to clear all active dynamic layout containers."""
        for container in [self.data_table_container, self.filter_container, self.detail_container]:
            if container:
                container.clear()

    def _clear_view(self):
        """Clears the active view state selection and completely flushes UI panels."""
        self.state.clear_selection()
        if self.select_view:
            self.select_view.set_value(None)
        self._clear_ui_containers()

    async def _load_view_data(self, view_name: Optional[str] = None):
        """Loads data for the selected view and dynamically initializes data filters and tables."""
        view = view_name or self.state.selected_entity_name.value
        self.state.selected_entity_name.set(view)
        self._clear_ui_containers()

        if not view:
            self.state.set_records([])
            return

        # Defensive security check: Prevent manual client state injection/tampering
        view_config = VIEW_INFO.get(view, {})
        excluded = view_config.get("excluded_roles", [])
        if excluded and any(self.has_role(role) for role in excluded):
            ui.notify("Acceso denegado: No posees permisos para visualizar esta vista.", type="negative")
            self._clear_view()
            return

        base_table_name = view_config.get("base_table")
        if not base_table_name:
            ui.notify(f"Error: No se ha configurado 'base_table' para la vista '{view}'", type="negative")
            return

        with self.data_table_container:
            spinner = ui.spinner(size="lg", color="orange-600").classes("absolute-center")
            try:
                records = await self.api.get_records(view, limit=20000)
                base_table_config = TABLE_INFO.get(base_table_name, {})
                
                self.state.set_records(records, base_table_config)
                self._setup_filters(base_table_config)

                # Render dynamic data table instance
                self.data_table_instance = DataTable(
                    state=self.state,
                    show_actions=False,
                    on_row_click=self._on_row_click,
                    hidden_columns=view_config.get("hidden_fields", []),
                )
                self.data_table_instance.create()

                if records:
                    ui.notify(f"Se cargaron {len(records)} registros de la vista", type="positive")
            except Exception as e:
                ui.notify(f"Error al cargar datos de la vista: {str(e)}", type="negative")
            finally:
                spinner.delete()

    async def _on_row_click(self, record: Dict[str, Any]):
        """Delegated action handler when a table row receives a click event."""
        view_name = self.state.selected_entity_name.value
        if view_name:
            await self.relationship_explorer.show_details(record, view_name, "views")

    def _setup_filters(self, base_table_config: Dict[str, Any]):
        """Builds and wires the filter panel container."""
        with self.filter_container:
            self.filter_panel = FilterPanel(
                records=self.state.records,
                on_filter_change=self._update_filter,
                table_config=base_table_config,
            )
            self.filter_panel.create()

    def _apply_and_refresh_table(self):
        """Internal helper to centralize filter applications and UI re-renders."""
        self.state.apply_filters_and_sort()
        if self.data_table_instance:
            self.data_table_instance.refresh()

    def _update_filter(self, column: str, value: Any):
        """Callback event handler triggered whenever a filter criteria changes."""
        self.state.filters[column] = value
        self._apply_and_refresh_table()

    def _clear_filters(self):
        """Flushes all input filter models and forces a visual reset."""
        self.state.filters.clear()
        if self.filter_panel:
            self.filter_panel.clear()
        self._apply_and_refresh_table()

    async def _refresh_data(self):
        """Refreshes the data layer for the currently loaded view context."""
        if self.state.selected_entity_name.value:
            await self._load_view_data(self.state.selected_entity_name.value)

    def _export_data(self):
        """Dispatches data generation for CSV exports based on currently filtered records."""
        view_name = self.state.selected_entity_name.value
        if view_name:
            export_to_csv(self.state.filtered_records, f"{view_name}_export.csv")