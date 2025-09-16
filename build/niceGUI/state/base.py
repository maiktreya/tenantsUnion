from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from nicegui import ui
import unicodedata
import re
from datetime import datetime


def _normalize_for_sorting(value: Any) -> str:
    """
    Normalizes a value for robust sorting, handling None, numbers as text,
    case sensitivity, and accents.
    """
    if value is None:
        return ''  # Return an empty string for None values

    str_value = str(value).strip()

    # Check if it is a numeric string
    if re.match(r'^-?(?:\d+\.?\d*|\.\d+)$', str_value):
        try:
            numeric_value = float(str_value)
            # Format as a zero-padded string to ensure correct numeric sorting
            return f"{numeric_value:020.6f}"
        except (ValueError, TypeError):
            pass  # Fallback to text sorting if conversion fails

    # For text values, normalize to remove accents and convert to lowercase
    normalized = unicodedata.normalize('NFD', str_value.lower())
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents


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
        self.sort_criteria: List[Tuple[str, bool]] = []
        self.current_page = ReactiveValue(1)
        self.page_size = ReactiveValue(5)
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
        """
        filtered = self.records.copy()

        # Apply filters
        for column, filter_value in self.filters.items():
            if not filter_value:
                continue
            
            if column.startswith('date_range_'):
                actual_column = column.replace('date_range_', '')
                start_date_str = filter_value.get('start')
                end_date_str = filter_value.get('end')

                if not start_date_str and not end_date_str:
                    continue
                
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
                
                temp_filtered = []
                for r in filtered:
                    record_date_str = r.get(actual_column)
                    if not record_date_str:
                        continue
                    
                    try:
                        # Handle potential timezone info (e.g., from ISO 8601 format)
                        if 'T' in record_date_str:
                            record_date = datetime.fromisoformat(record_date_str.replace('Z', '+00:00')).date()
                        else:
                            record_date = datetime.strptime(record_date_str, '%Y-%m-%d').date()
                        
                        # Check if the record date falls within the range
                        if start_date and record_date < start_date:
                            continue
                        if end_date and record_date > end_date:
                            continue
                        temp_filtered.append(r)
                    except (ValueError, TypeError):
                        # Ignore records with invalid date formats
                        continue
                filtered = temp_filtered

            elif column == 'global_search':
                search_term = str(filter_value).lower()
                filtered = [
                    r for r in filtered
                    if any(search_term in str(v).lower() for v in r.values())
                ]
            elif isinstance(filter_value, list):
                if filter_value: # Ensure the list is not empty
                    filtered = [
                        r for r in filtered
                        if r.get(column) in filter_value
                    ]
            else: # General string matching for other filter types
                filtered = [
                    r for r in filtered
                    if str(filter_value).lower() in str(r.get(column, '')).lower()
                ]

        self.filtered_records = filtered

        # Apply sorting
        if self.sort_criteria:
            for column, ascending in reversed(self.sort_criteria):
                self.filtered_records.sort(
                    key=lambda x: (x.get(column) is None, _normalize_for_sorting(x.get(column))),
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
