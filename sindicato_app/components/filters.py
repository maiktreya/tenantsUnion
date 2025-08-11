from typing import Dict, List, Callable
from nicegui import ui

class FilterPanel:
    """Reusable filter panel component"""

    def __init__(
        self,
        columns: List[str],
        on_filter_change: Callable[[str, str], None],
        on_clear: Callable[[], None]
    ):
        self.columns = columns
        self.on_filter_change = on_filter_change
        self.on_clear = on_clear
        self.container = None
        self.inputs = {}

    def create(self) -> ui.column:
        """Create the filter panel UI"""
        self.container = ui.column().classes('w-full')
        self.refresh()
        return self.container

    def refresh(self):
        """Refresh filter inputs"""
        if not self.container:
            return

        self.container.clear()
        self.inputs.clear()

        with self.container:
            ui.label('Filtros').classes('text-h6 mb-2')

            with ui.row().classes('w-full gap-2 flex-wrap'):
                for column in self.columns:
                    self.inputs[column] = ui.input(
                        label=f'Filtrar {column}',
                        on_change=lambda e, col=column: self.on_filter_change(col, e.value)
                    ).classes('w-48').props('dense clearable')

    def clear(self):
        """Clear all filter inputs"""
        for input_field in self.inputs.values():
            input_field.value = ''
        if self.on_clear:
            self.on_clear()