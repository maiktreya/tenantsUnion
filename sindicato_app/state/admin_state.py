from typing import List, Dict
from state.base import BaseTableState, ReactiveValue

class AdminState(BaseTableState):
    """State management for admin view"""

    def __init__(self):
        super().__init__()
        self.selected_table = ReactiveValue()

    def set_records(self, records: List[Dict]):
        """Set records and reset filters"""
        self.records = records
        self.filtered_records = records.copy()
        self.filters.clear()
        self.sort_column = None
        self.sort_ascending = True
        self.current_page.set(1)