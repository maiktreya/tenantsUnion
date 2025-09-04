from typing import Dict, List, Callable, Any
from nicegui import ui
import unicodedata
import re

def _is_numeric_string(value: str) -> bool:
    """Check if a string represents a number (integer or float)."""
    if not value:
        return False
    value = value.strip()
    # Pattern to match integers, floats, and negative numbers
    numeric_pattern = r'^-?(?:\d+\.?\d*|\.\d+)$'
    return bool(re.match(numeric_pattern, value))

def _normalize_for_sorting(value) -> str:
    """Normalize a value for proper sorting, handling accents, case, and numeric strings."""
    if value is None:
        return ""

    str_value = str(value).strip()

    if _is_numeric_string(str_value):
        try:
            numeric_value = float(str_value)
            # Pad with zeros to ensure correct numeric sorting as strings
            return f"{numeric_value:015.3f}"
        except ValueError:
            pass # Fallback to text sorting

    # For text values: normalize unicode characters (remove accents) and convert to lowercase
    normalized = unicodedata.normalize('NFD', str_value.lower())
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents


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

    def _get_sorted_unique_values(self, column: str) -> List[Any]:
        """Get unique values for a column, properly sorted."""
        unique_values = list(set(r.get(column) for r in self.records if r.get(column) is not None))
        try:
            return sorted(unique_values, key=_normalize_for_sorting)
        except Exception:
            # Fallback to simple string sorting if normalization fails
            return sorted(unique_values, key=lambda x: str(x).lower())

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
                self.inputs['global_search'] = ui.input(
                    label='Búsqueda rápida',
                    on_change=lambda e: self.on_filter_change('global_search', e.value)
                ).classes('w-64').props('dense clearable outlined')

                for column in columns:
                    unique_values = [r.get(column) for r in self.records if r.get(column) is not None]
                    unique_count = len(set(unique_values))

                    if (1 < unique_count <= 16 and
                        'id' not in column.lower() and
                        unique_count < len(unique_values) * 0.8):

                        sorted_unique_vals = self._get_sorted_unique_values(column)
                        self.inputs[column] = ui.select(
                            options=sorted_unique_vals,
                            label=f'Filtrar {column}',
                            multiple=True,
                            clearable=True,
                            on_change=lambda e, col=column: self.on_filter_change(col, e.value)
                        ).classes('w-64').props('dense outlined')

    def clear(self):
        """Clear all filter inputs."""
        for input_field in self.inputs.values():
            if hasattr(input_field, 'value'):
                input_field.value = [] if getattr(input_field, 'multiple', False) else None