from typing import Dict
from nicegui import ui
from api.client import APIClient
from state.views_state import ViewsState
from components.data_table import DataTable
from components.filters import FilterPanel
from utils.export import export_to_csv
from config import VIEW_INFO

class ViewsExplorerView:
    """Views explorer for materialized views"""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = ViewsState()
        self.data_table = None
        self.filter_panel = None

    def create(self) -> ui.column:
        """Create the views explorer UI"""
        container = ui.column().classes('w-full p-4 gap-4')

        with container:
            ui.label('Explorador de Vistas').classes('text-h4')

            # Toolbar
            with ui.row().classes('w-full gap-4 items-center'):
                ui.select(
                    options=list(VIEW_INFO.keys()),
                    label='Seleccionar Vista',
                    on_change=lambda e: ui.timer(0.1, lambda: self._load_view_data(e.value), once=True)
                ).classes('w-64').bind_value_to(self.state.selected_view)

                ui.button(
                    'Refrescar',
                    icon='refresh',
                    on_click=self._refresh_data
                ).props('color=orange-600')

                ui.button(
                    'Limpiar Filtros',
                    icon='filter_alt_off',
                    on_click=self._clear_filters
                ).props('color=orange-600')

                ui.button(
                    'Exportar CSV',
                    icon='download',
                    on_click=self._export_data
                ).props('color=orange-600')

            # Filters
            with ui.expansion('Filtros y Búsqueda', icon='filter_list').classes('w-full').props('default-opened'):
                self.state.filter_container = ui.column().classes('w-full')

            # Data table (without edit/delete actions for views)
            self.data_table = DataTable(
                state=self.state,
                show_actions=False
            )
            self.data_table.create()

        return container

    async def _load_view_data(self, view_name: str = None):
        """Load data for the selected view"""
        view = view_name or self.state.selected_view.value
        if not view:
            return

        try:
            records = await self.api.get_records(view)
            self.state.set_records(records)
            self._setup_filters()
            self.data_table.refresh()
            ui.notify(f'Se cargaron {len(records)} registros de la vista', type='positive')
        except Exception as e:
            ui.notify(f'Error al cargar datos de la vista: {str(e)}', type='negative')

    def _setup_filters(self):
        """Setup filter panel"""
        if not self.state.filter_container or not self.state.records:
            return

        self.state.filter_container.clear()
        columns = list(self.state.records[0].keys())

        with self.state.filter_container:
            self.filter_panel = FilterPanel(
                columns=columns,
                on_filter_change=self._update_filter,
                on_clear=self._clear_filters
            )
            self.filter_panel.create()

    def _update_filter(self, column: str, value: str):
        """Update filter for a column"""
        self.state.filters[column] = value
        self.state.apply_filters()
        self.data_table.refresh()

    def _clear_filters(self):
        """Clear all filters"""
        self.state.clear_filters()
        if self.filter_panel:
            self.filter_panel.clear()
        self.data_table.refresh()

    async def _refresh_data(self):
        """Refresh current view data"""
        await self._load_view_data()

    def _export_data(self):
        """Export filtered data to CSV"""
        if self.state.selected_view.value:
            export_to_csv(
                self.state.filtered_records,
                f'{self.state.selected_view.value}_export.csv'
            )