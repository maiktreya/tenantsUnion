from typing import Dict, List, Callable, Any
from nicegui import ui
import collections
import unicodedata
import re

class FilterPanel:
    """Reusable client-side filter panel with dynamic control generation."""

    def __init__(
        self,
        records: List[Dict],
        on_filter_change: Callable[[str, Any], None],
    ):
        self.records = records
        self.on_filter_change = on_filter_change
        self.container = None
        self.inputs = {}

    def create(self) -> ui.column:
        """Create the filter panel UI based on the data provided."""
        self.container = ui.column().classes('w-full')
        self.refresh()
        return self.container

    def _normalize_for_sorting(self, value) -> str:
        """Normalize a value for proper sorting, handling accents, case, and numeric strings."""
        if value is None:
            return ""

        # Convert to string
        str_value = str(value).strip()

        # Check if it's a numeric string (including decimals and negative numbers)
        if self._is_numeric_string(str_value):
            try:
                # Convert to float for proper numeric sorting, then pad with zeros
                # This ensures numeric strings sort correctly (1, 2, 10 instead of 1, 10, 2)
                numeric_value = float(str_value)
                return f"{numeric_value:015.3f}"  # Pad to 15 digits with 3 decimal places
            except ValueError:
                pass

        # For text values: normalize unicode characters (remove accents) and convert to lowercase
        normalized = unicodedata.normalize('NFD', str_value.lower())
        # Remove accent marks (combining characters)
        without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return without_accents

    def _is_numeric_string(self, value: str) -> bool:
        """Check if a string represents a number (integer or float)."""
        if not value:
            return False

        # Remove whitespace
        value = value.strip()

        # Pattern to match integers, floats, and negative numbers
        # Supports formats like: 123, -123, 123.45, -123.45, .45, -.45
        numeric_pattern = r'^-?(?:\d+\.?\d*|\.\d+)$'
        return bool(re.match(numeric_pattern, value))

    def _get_sorted_unique_values(self, column: str) -> List[Any]:
        """Get unique values for a column, properly sorted."""
        # Get all non-None unique values
        unique_values = list(set(r.get(column) for r in self.records if r.get(column) is not None))

        # Sort using the normalization function
        try:
            sorted_values = sorted(unique_values, key=self._normalize_for_sorting)
        except Exception:
            # Fallback to string sorting if there are any issues
            sorted_values = sorted(unique_values, key=lambda x: str(x).lower())

        return sorted_values

    def refresh(self):
        """Create or refresh filter inputs based on data."""
        if not self.container or not self.records:
            return

        self.container.clear()
        self.inputs.clear()
        columns = self.records[0].keys()

        with self.container:
            ui.label('Filtros y Búsqueda').classes('text-h6 mb-2')

            with ui.row().classes('w-full gap-4 flex-wrap items-center'):
                # 1. Global Search
                self.inputs['global_search'] = ui.input(
                    label='Búsqueda rápida',
                    on_change=lambda e: self.on_filter_change('global_search', e.value)
                ).classes('w-64').props('dense clearable outlined')

                # 2. Dynamic Filters for Categorical Data
                for column in columns:
                    # Increased threshold to 16 and improved heuristic
                    unique_values = [r.get(column) for r in self.records if r.get(column) is not None]
                    unique_count = len(set(unique_values))

                    # Create dropdown if:
                    # - More than 1 but less than or equal to 16 unique values
                    # - Column name doesn't contain 'id' (case insensitive)
                    # - Not all values are unique (avoids ID-like columns)
                    if (1 < unique_count <= 16 and
                        'id' not in column.lower() and
                        unique_count < len(unique_values) * 0.8):  # At least 20% repetition

                        sorted_unique_values = self._get_sorted_unique_values(column)

                        self.inputs[column] = ui.select(
                            options=sorted_unique_values,
                            label=f'Filtrar {column}',
                            multiple=True,
                            clearable=True,
                            on_change=lambda e, col=column: self.on_filter_change(col, e.value)
                        ).classes('w-64').props('dense outlined')

    def clear(self):
        """Clear all filter inputs."""
        for input_field in self.inputs.values():
            if hasattr(input_field, 'value'):
                input_field.value = None if not hasattr(input_field, 'multiple') or not input_field.multiple else []
        # The on_change event for each input will trigger the filter update.