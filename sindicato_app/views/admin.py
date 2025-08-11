from typing import Dict
from nicegui import ui
from api.client import APIClient
from state.admin_state import AdminState
from components.data_table import DataTable
from components.dialogs import RecordDialog
from utils.export import export_to_csv
from config import config, TABLE_INFO

class AdminView:
    """Admin view for table management"""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = AdminState()
        self.data_table = None

    def create(self) -> ui.column:
        """Create the admin view UI"""
        container = ui.column().classes('w-full p-4 gap-4')

        with container:
            ui.label('Administración de Tablas').classes('text-h4')

            # Toolbar
            with ui.row().classes('w-full gap-4 items-center'):
                ui.select(
                    options=list(TABLE_INFO.keys()),
                    label='Seleccionar Tabla',
                    on_change=lambda e: ui.timer(0.1, lambda: self._load_table_data(e.value), once=True)
                ).classes('w-64').bind_value_to(self.state.selected_table)

                ui.button(
                    'Refrescar',
                    icon='refresh',
                    on_click=self._refresh_data
                ).props('color=orange-600')

                ui.button(
                    'Crear Nuevo',
                    icon='add',
                    on_click=self._create_record
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

            # Data table
            self.data_table = DataTable(
                state=self.state,
                on_edit=self._edit_record,
                on_delete=self._delete_record
            )
            self.data_table.create()

        return container

    async def _load_table_data(self, table_name: str = None):
        """Load data for the selected table"""
        table = table_name or self.state.selected_table.value
        if not table:
            return

        try:
            records = await self.api.get_records(table)
            self.state.set_records(records)
            self._setup_filters()
            self.data_table.refresh()
            ui.notify(f'Se cargaron {len(records)} registros', type='positive')
        except Exception as e:
            ui.notify(f'Error al cargar datos: {str(e)}', type='negative')

    def _setup_filters(self):
        """Setup filter inputs"""
        if not self.state.filter_container or not self.state.records:
            return

        self.state.filter_container.clear()
        columns = list(self.state.records[0].keys())

        with self.state.filter_container:
            ui.label('Filtros').classes('text-h6 mb-2')
            with ui.row().classes('w-full gap-2 flex-wrap'):
                for column in columns:
                    ui.input(
                        label=f'Filtrar {column}',
                        on_change=lambda e, col=column: self._update_filter(col, e.value)
                    ).classes('w-48').props('dense clearable')

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
        """Create a new record"""
        if not self.state.selected_table.value:
            ui.notify('Por favor, seleccione una tabla primero', type='warning')
            return

        dialog = RecordDialog(
            api=self.api,
            table=self.state.selected_table.value,
            mode='create',
            on_success=lambda: ui.timer(0.1, self._refresh_data, once=True)
        )
        dialog.open()

    async def _edit_record(self, record: Dict):
        """Edit an existing record"""
        dialog = RecordDialog(
            api=self.api,
            table=self.state.selected_table.value,
            record=record,
            mode='edit',
            on_success=lambda: ui.timer(0.1, self._refresh_data, once=True)
        )
        dialog.open()

    async def _delete_record(self, record: Dict):
        """Delete a record with confirmation"""
        record_id = record.get('id')

        with ui.dialog() as dialog, ui.card():
            ui.label(f'¿Eliminar registro #{record_id}?').classes('text-h6')
            ui.label('Esta acción no se puede deshacer.').classes('text-body2 text-gray-600')

            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')

                async def confirm():
                    success = await self.api.delete_record(
                        self.state.selected_table.value,
                        record_id
                    )
                    if success:
                        ui.notify('Registro eliminado con éxito', type='positive')
                        dialog.close()
                        await self._refresh_data()

                ui.button('Eliminar', on_click=confirm).props('color=negative')

        dialog.open()

    def _export_data(self):
        """Export filtered data to CSV"""
        export_to_csv(
            self.state.filtered_records,
            f'{self.state.selected_table.value}_export.csv'
        )