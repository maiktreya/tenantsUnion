from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from nicegui import ui
import operator
from functools import reduce

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
    """Base state for table-based views with client-side filtering and sorting."""

    def __init__(self):
        self.selected_item = ReactiveValue()
        self.records: List[Dict] = []
        self.filtered_records: List[Dict] = []
        self.filters: Dict[str, Any] = {}
        # A list of tuples: (column_name, ascending_boolean)
        self.sort_criteria: List[Tuple[str, bool]] = []
        self.current_page = ReactiveValue(1)
        self.page_size = ReactiveValue(10)

        # UI element references
        self.filter_container = None
        self.table_container = None
        self.pagination_container = None

    def set_records(self, records: List[Dict]):
        """Set the base records and initialize the filtered view."""
        self.records = records
        self.apply_filters_and_sort()

    def apply_filters_and_sort(self):
        """
        Apply all current filters and sorting criteria to the base records.
        This is the core client-side logic.
        """
        filtered = self.records.copy()

        # Apply filters
        for column, filter_value in self.filters.items():
            if filter_value:
                # Global search logic
                if column == 'global_search':
                    search_term = str(filter_value).lower()
                    filtered = [
                        r for r in filtered
                        if any(search_term in str(v).lower() for v in r.values())
                    ]
                # Multi-select logic for categorical filters
                elif isinstance(filter_value, list):
                    if filter_value: # Only filter if list is not empty
                        filtered = [
                            r for r in filtered
                            if r.get(column) in filter_value
                        ]
                # Standard text filter
                else:
                    filtered = [
                        r for r in filtered
                        if str(filter_value).lower() in str(r.get(column, '')).lower()
                    ]

        self.filtered_records = filtered

        # Apply sorting
        if self.sort_criteria:
            # Sort by each criterion in reverse order of priority
            for column, ascending in reversed(self.sort_criteria):
                self.filtered_records.sort(
                    key=lambda x: (x.get(column) is None, x.get(column, '')),
                    reverse=not ascending
                )

        self.current_page.set(1)

    def get_paginated_records(self) -> List[Dict]:
        """Get records for the current page."""
        start = (self.current_page.value - 1) * self.page_size.value
        end = start + self.page_size.value
        return self.filtered_records[start:end]

    def get_total_pages(self) -> int:
        """Calculate total pages."""
        if not self.filtered_records:
            return 1
        return max(1, (len(self.filtered_records) - 1) // self.page_size.value + 1)