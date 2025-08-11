from nicegui import ui
from components.conflict_manager import ConflictManager
from api.client import APIClient

class ConflictsView:
    """Simplified conflicts view using self-contained component"""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.container = None
        self.conflict_manager = None

    def create(self):
        """Create the conflicts view"""
        self.container = ui.column().classes('w-full')

        with self.container:
            # Mount the conflict manager component
            self.conflict_manager = ConflictManager(self.api_client)
            self.conflict_manager.mount()