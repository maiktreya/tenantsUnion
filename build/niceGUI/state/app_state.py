from typing import List, Dict, Optional
from .base import BaseTableState, ReactiveValue


class GenericViewState(BaseTableState):
    """Represents the state for a single, table-based view."""

    def __init__(self):
        super().__init__()
        self.selected_entity_name = ReactiveValue()

    def set_records(self, records: List[Dict], table_config: Optional[Dict] = None):
        """Set the base records and initialize the filtered view."""
        super().set_records(records, table_config)
        self.filters.clear()
        self.sort_criteria = []
        self.apply_filters_and_sort()

    def clear_selection(self):
        """Resets the state for the current view."""
        self.selected_entity_name.set(None)
        self.set_records([])


class AppState:
    """The centralized singleton state manager for the application. Now a pure data store."""

    def __init__(self):
        self.admin = GenericViewState()
        self.views_explorer = GenericViewState()
        self.conflicts = GenericViewState()
        self.afiliadas_importer = GenericViewState()
        self.user_management = GenericViewState()
        self.all_nodos: List[Dict] = []
        self.all_afiliadas_options: Dict[int, str] = {}
        self.all_users: List[Dict] = []
