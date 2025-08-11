from typing import List, Dict, Optional, Callable
from nicegui import ui
from state.base import BaseTableState

class DataTable:
    """Reusable data table component with sorting, filtering, and pagination"""

    def __init__(
        self,
        state: BaseTableState,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        show_actions: bool = True
    ):
        self.state = state
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.show_actions = show_actions
        self.container = None

    def create(self) -> ui.column:
        """Create the table UI"""
        self.container = ui.column().classes('w-full')
        self.refresh()

        # Subscribe to state changes
        self.state.current_page.subscribe(lambda _: self.refresh())
        self.state.page_size.subscribe(lambda _: self.refresh())

        return self.container

    def refresh(self):
        """Refresh the table display"""
        if not self.container:
            return

        self.container.clear()

        with self.container:
            records = self.state.get_paginated_records()

            if not records:
                ui.label('No se encontraron registros').classes('text-gray-500')
                return

            # Record count
            ui.label(
                f'Mostrando {len(self.state.filtered_records)} de {len(self.state.records)} registros'
            ).classes('text-caption text-gray-600 mb-2')

            # Table
            columns = list(records[0].keys())

            with ui.card().classes('w-full'):
                # Header
                with ui.row().classes('w-full bg-gray-100 p-2'):
                    for column in columns:
                        with ui.row().classes('flex-1 items-center cursor-pointer').on(
                            'click',
                            lambda c=column: self._sort_by_column(c)
                        ):
                            ui.label(column).classes('font-bold')
                            if self.state.sort_column == column:
                                icon = 'arrow_upward' if self.state.sort_ascending else 'arrow_downward'
                                ui.icon(icon, size='sm')

                    if self.show_actions:
                        ui.label('Acciones').classes('font-bold w-32')

                # Rows
                for record in records:
                    with ui.row().classes('w-full border-b p-2 hover:bg-gray-50 items-center'):
                        for column in columns:
                            value = record.get(column, '')
                            display_value = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                            ui.label(display_value).classes('flex-1').tooltip(str(value))

                        if self.show_actions:
                            with ui.row().classes('w-32 gap-1'):
                                if self.on_edit:
                                    ui.button(
                                        icon='edit',
                                        on_click=lambda r=record: self.on_edit(r)
                                    ).props('size=sm flat dense')

                                if self.on_delete:
                                    ui.button(
                                        icon='delete',
                                        on_click=lambda r=record: self.on_delete(r)
                                    ).props('size=sm flat dense color=negative')

            # Pagination
            if self.state.get_total_pages() > 1:
                self._create_pagination()

    def _sort_by_column(self, column: str):
        """Handle column sorting"""
        if self.state.sort_column == column:
            self.state.sort_ascending = not self.state.sort_ascending
        else:
            self.state.sort_column = column
            self.state.sort_ascending = True

        self.state.apply_sort()
        self.refresh()

    def _create_pagination(self):
        """Create pagination controls"""
        total_pages = self.state.get_total_pages()
        current = self.state.current_page.value

        with ui.row().classes('w-full justify-center items-center gap-2 p-2'):
            # First/Previous
            ui.button(
                icon='first_page',
                on_click=lambda: self._go_to_page(1)
            ).props('flat dense').set_enabled(current > 1)

            ui.button(
                icon='chevron_left',
                on_click=lambda: self._go_to_page(current - 1)
            ).props('flat dense').set_enabled(current > 1)

            # Page selector
            with ui.row().classes('items-center gap-2'):
                ui.label('Página')
                ui.number(
                    value=current,
                    min=1,
                    max=total_pages,
                    on_change=lambda e: self._go_to_page(int(e.value)) if e.value else None
                ).props('dense outlined').classes('w-16')
                ui.label(f'de {total_pages}')

            # Next/Last
            ui.button(
                icon='chevron_right',
                on_click=lambda: self._go_to_page(current + 1)
            ).props('flat dense').set_enabled(current < total_pages)

            ui.button(
                icon='last_page',
                on_click=lambda: self._go_to_page(total_pages)
            ).props('flat dense').set_enabled(current < total_pages)

            # Page size selector
            with ui.row().classes('items-center gap-2 ml-4'):
                ui.label('Mostrar:')
                ui.select(
                    options=[5, 10, 25, 50, 100],
                    value=self.state.page_size.value,
                    on_change=lambda e: self.state.page_size.set(e.value)
                ).props('dense').classes('w-20')
                ui.label('por página')

    def _go_to_page(self, page: int):
        """Navigate to specific page"""
        total_pages = self.state.get_total_pages()
        if 1 <= page <= total_pages:
            self.state.current_page.set(page)