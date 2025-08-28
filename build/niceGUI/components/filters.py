from typing import Dict, List, Callable, Any
from nicegui import ui
import collections

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
                    # Heuristic: If a column has few unique values, it's likely categorical.
                    # Let's say less than 12 unique values and it's not an ID.
                    unique_values = sorted(list(set(r.get(column) for r in self.records if r.get(column) is not None)))
                    if 1 < len(unique_values) < 12 and 'id' not in column:
                        self.inputs[column] = ui.select(
                            options=unique_values,
                            label=f'Filtrar {column}',
                            multiple=True,
                            clearable=True,
                            on_change=lambda e, col=column: self.on_filter_change(col, e.value)
                        ).classes('w-64').props('dense outlined')

    def clear(self):
        """Clear all filter inputs."""
        for input_field in self.inputs.values():
            input_field.value = None
        # The on_change event for each input will trigger the filter update.