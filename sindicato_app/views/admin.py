from nicegui import ui
from components.data_table_component import DataTableComponent
from api.client import APIClient

class AdminView:
    """Admin view using self-contained components"""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.table_component = None
        self.container = None

    def create(self):
        """Create the admin view"""
        self.container = ui.column().classes('w-full p-4')

        with self.container:
            ui.label('Table Administration').classes('text-h4 mb-4')

            # Table selector
            ui.select(
                options=['empresas', 'usuarios', 'conflictos', 'facturacion'],
                label='Select Table',
                on_change=self._on_table_change
            ).classes('w-64')

            # Table component container
            self.table_container = ui.column().classes('w-full mt-4')

    def _on_table_change(self, e):
        """Handle table selection change"""
        if not e.value:
            return

        self.table_container.clear()

        with self.table_container:
            # Create and mount table component with API client
            self.table_component = DataTableComponent(
                api_client=self.api_client,
                endpoint=f'/{e.value}',
                editable=True
            )
            self.table_component.mount()