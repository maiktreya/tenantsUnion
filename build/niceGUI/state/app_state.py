# /build/niceGUI/state/app_state.py

from typing import List, Dict
from .base import BaseTableState, ReactiveValue


class GenericViewState(BaseTableState):
    """
    A centralized, generic state manager for views that display lists of records.
    This replaces the need for separate AdminState and ViewsState classes,
    promoting code reuse and a single source of truth for table logic.
    """

    def __init__(self):
        super().__init__()
        # A reactive value to hold the name of the currently selected entity (e.g., table or view name)
        self.selected_entity_name = ReactiveValue()

    def set_records(self, records: List[Dict]):
        """
        Sets the records for the view and resets all filters, sorting, and pagination.
        This combines the logic previously duplicated in AdminState and ViewsState.
        """
        self.records = records
        # apply_filters_and_sort will be called to generate the initial filtered list
        # and reset the page number.
        self.filters.clear()
        self.sort_criteria = []
        self.apply_filters_and_sort()
