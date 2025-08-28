from typing import List, Dict, Optional, Callable
from nicegui import ui, events  # Correctly import 'events' here
from state.base import BaseTableState

class DataTable:
    """Reusable data table with client-side multi-sort, filtering, and pagination."""

    def __init__(
        self,
        state: BaseTableState,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        on_row_click: Optional[Callable] = None,
        show_actions: bool = True,
    ):
        self.state = state
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_row_click = on_row_click
        self.show_actions = show_actions
        self.container = None

    def create(self) -> ui.column:
        """Create the table UI."""
        self.container = ui.column().classes("w-full")
        self.refresh()

        self.state.current_page.subscribe(lambda _: self.refresh())
        self.state.page_size.subscribe(lambda _: self.refresh())

        return self.container

    def refresh(self):
        """Refresh the table display."""
        if not self.container:
            return

        self.container.clear()

        with self.container:
            records = self.state.get_paginated_records()

            if not self.state.records:
                ui.label("No se encontraron registros").classes("text-gray-500")
                return

            ui.label(
                f"Mostrando {len(self.state.filtered_records)} de {len(self.state.records)} registros"
            ).classes("text-caption text-gray-600 mb-2")

            if not records:
                ui.label("Ningún registro coincide con los filtros actuales.").classes("text-gray-500")

            if records:
                columns = list(records[0].keys())
                with ui.card().classes("w-full"):
                    # Header
                    with ui.row().classes("w-full bg-gray-100 p-2"):
                        for column in columns:
                            with ui.row().classes("flex-1 items-center cursor-pointer gap-1").on(
                                "click", lambda c=column: self._sort_by_column(c), ['shiftKey'] # Pass event implicitly
                            ):
                                ui.label(column).classes("font-bold")
                                # Display sort indicator
                                sort_info = next((c for c in self.state.sort_criteria if c[0] == column), None)
                                if sort_info:
                                    icon = "arrow_upward" if sort_info[1] else "arrow_downward"
                                    ui.icon(icon, size="sm")
                                    # Show sort order for multi-sort
                                    if len(self.state.sort_criteria) > 1:
                                        sort_index = self.state.sort_criteria.index(sort_info) + 1
                                        ui.label(f'({sort_index})').classes('text-xs')

                        if self.show_actions:
                            ui.label("Acciones").classes("font-bold w-32")

                    # Rows
                    for record in records:
                        row_classes = "w-full border-b p-2 hover:bg-gray-50 items-center"
                        if self.on_row_click:
                            row_classes += " cursor-pointer"

                        with ui.row().classes(row_classes) as row:
                            for column in columns:
                                value = record.get(column, "")
                                display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                                ui.label(display_value).classes("flex-1").tooltip(str(value))

                            if self.show_actions:
                                with ui.row().classes("w-32 gap-1"):
                                    if self.on_edit:
                                        ui.button(icon="edit", on_click=lambda r=record: self.on_edit(r)).props("size=sm flat dense")
                                    if self.on_delete:
                                        ui.button(icon="delete", on_click=lambda r=record: self.on_delete(r)).props("size=sm flat dense color=negative")

                        if self.on_row_click:
                            row.on("click", lambda r=record: self.on_row_click(r))

            # Pagination
            if self.state.get_total_pages() > 1:
                self._create_pagination()

    # FIX: Corrected the function signature and event handling
    def _sort_by_column(self, e: events.GenericEventArguments):
        """Handle multi-column sorting with shift key."""
        column = e.sender.parent.default_slot.children[0].text
        is_shift_key = e.args.get('shiftKey', False)

        existing_criterion = next((c for c in self.state.sort_criteria if c[0] == column), None)

        if not is_shift_key:
            new_direction = not existing_criterion[1] if existing_criterion else True
            self.state.sort_criteria = [(column, new_direction)]
        else:
            if existing_criterion:
                idx = self.state.sort_criteria.index(existing_criterion)
                self.state.sort_criteria[idx] = (column, not existing_criterion[1])
            else:
                self.state.sort_criteria.append((column, True))

        self.state.apply_filters_and_sort()
        self.refresh()

    def _create_pagination(self):
        """Create pagination controls."""
        total_pages = self.state.get_total_pages()
        current = self.state.current_page.value

        with ui.row().classes("w-full justify-center items-center gap-2 p-2"):
            ui.button(icon="first_page", on_click=lambda: self._go_to_page(1)).props("flat dense").set_enabled(current > 1)
            ui.button(icon="chevron_left", on_click=lambda: self._go_to_page(current - 1)).props("flat dense").set_enabled(current > 1)

            with ui.row().classes("items-center gap-2"):
                ui.label("Página")
                ui.number(value=current, min=1, max=total_pages, on_change=lambda e: self._go_to_page(int(e.value) if e.value else None)).props("dense outlined").classes("w-16")
                ui.label(f"de {total_pages}")

            ui.button(icon="chevron_right", on_click=lambda: self._go_to_page(current + 1)).props("flat dense").set_enabled(current < total_pages)
            ui.button(icon="last_page", on_click=lambda: self._go_to_page(total_pages)).props("flat dense").set_enabled(current < total_pages)

            with ui.row().classes("items-center gap-2 ml-4"):
                ui.label("Mostrar:")
                ui.select(options=[5, 10, 25, 50, 100], value=self.state.page_size.value, on_change=lambda e: self.state.page_size.set(e.value)).props("dense").classes("w-20")
                ui.label("por página")

    def _go_to_page(self, page: int):
        """Navigate to a specific page."""
        total_pages = self.state.get_total_pages()
        if 1 <= page <= total_pages:
            self.state.current_page.set(page)