from nicegui import ui
from components.data_table_component import DataTableComponent

class ViewsExplorerView:
    """Simplified views explorer using self-contained components"""

    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.views = [
            'vista_conflictos_completa',
            'vista_facturacion_resumen',
            'vista_usuarios_activos'
        ]
        self.container = None

    def create(self):
        """Create the views explorer"""
        self.container = ui.column().classes('w-full p-4')

        with self.container:
            ui.label('Database Views Explorer').classes('text-h4 mb-4')

            # View selector
            ui.select(
                options=self.views,
                label='Select View',
                on_change=self._on_view_change
            ).classes('w-64')

            # View container
            self.view_container = ui.column().classes('w-full mt-4')

    def _on_view_change(self, e):
        """Handle view selection change"""
        if not e.value:
            return

        self.view_container.clear()

        with self.view_container:
            # Create and mount table component for view
            table = DataTableComponent(
                api_endpoint=f'{self.api_base_url}/{e.value}',
                editable=False  # Views are read-only
            )
            table.mount()