from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from nicegui import ui

@dataclass
class ReactiveValue:
    """Wrapper for reactive values"""
    value: Any = None
    _observers: List[Callable] = field(default_factory=list)

    def set(self, value: Any):
        self.value = value
        for observer in self._observers:
            observer(value)

    def subscribe(self, callback: Callable):
        self._observers.append(callback)

    def unsubscribe(self, callback: Callable):
        if callback in self._observers:
            self._observers.remove(callback)

class BaseTableState:
    """Base state for table-based views"""

    def __init__(self):
        self.selected_item = ReactiveValue()
        self.records = []
        self.filtered_records = []
        self.filters = {}
        self.sort_column = None
        self.sort_ascending = True
        self.current_page = ReactiveValue(1)
        self.page_size = ReactiveValue(5)

        # UI element references
        self.filter_container = None
        self.table_container = None
        self.pagination_container = None

    def apply_filters(self):
        """Apply filters to records"""
        filtered = self.records.copy()

        for column, filter_value in self.filters.items():
            if filter_value:
                filtered = [
                    record for record in filtered
                    if str(filter_value).lower() in str(record.get(column, '')).lower()
                ]

        self.filtered_records = filtered
        self.apply_sort()

    def apply_sort(self):
        """Apply sorting to filtered records"""
        if self.sort_column:
            self.filtered_records.sort(
                key=lambda x: x.get(self.sort_column, ''),
                reverse=not self.sort_ascending
            )
        self.current_page.set(1)

    def clear_filters(self):
        """Clear all filters"""
        self.filters.clear()
        self.filtered_records = self.records.copy()
        self.current_page.set(1)

    def get_paginated_records(self) -> List[Dict]:
        """Get records for current page"""
        start = (self.current_page.value - 1) * self.page_size.value
        end = start + self.page_size.value
        return self.filtered_records[start:end]

    def get_total_pages(self) -> int:
        """Calculate total pages"""
        if not self.filtered_records:
            return 1
        return max(1, (len(self.filtered_records) - 1) // self.page_size.value + 1)