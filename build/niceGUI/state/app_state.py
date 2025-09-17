from typing import List, Dict
from .base import BaseTableState, ReactiveValue
from api.client import APIClient


class GenericViewState(BaseTableState):
    """Represents the state for a single, table-based view."""

    def __init__(self):
        super().__init__()
        self.selected_entity_name = ReactiveValue()

    def set_records(self, records: List[Dict]):
        self.records = records
        self.filters.clear()
        self.sort_criteria = []
        self.apply_filters_and_sort()

    def clear_selection(self):
        """Resets the state for the current view."""
        self.selected_entity_name.set(None)
        self.set_records([])


class AppState:
    """The centralized singleton state manager for the application."""

    def __init__(self, api_client: APIClient):
        self.api: APIClient = api_client
        self.admin = GenericViewState()
        self.views_explorer = GenericViewState()
        self.conflicts = GenericViewState()
        self.afiliadas_importer = GenericViewState()
        self.user_management = GenericViewState()
        self.all_nodos: List[Dict] = []
        self.all_afiliadas_options: Dict[int, str] = {}
        self.all_users: List[Dict] = []

    async def initialize_global_data(self):
        """Fetches and caches data used across multiple views."""
        try:
            self.all_nodos = await self.api.get_records("nodos", order="nombre.asc")
            records = await self.api.get_records("v_afiliadas_detalle", limit=5000)
            self.all_afiliadas_options = {
                r[
                    "id"
                ]: f'{r.get("Nombre", "")} {r.get("Apellidos", "")} (ID: {r.get("id")})'
                for r in records
            }
        except Exception as e:
            print(f"FATAL: Could not initialize global state. Error: {e}")
