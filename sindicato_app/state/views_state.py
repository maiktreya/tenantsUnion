from typing import List, Dict
from state.base import BaseTableState, ReactiveValue

class ViewsState(BaseTableState):
    """State management for views explorer"""

    def __init__(self):
        super().__init__()
        self.selected_view = ReactiveValue()

    def set_records(self, records: List[Dict]):
        """Set records from view and reset filters"""
        self.records = records
        self.filtered_records = records.copy()
        self.filters.clear()
        self.sort_column = None
        self.sort_ascending = True
        self.current_page.set(1)