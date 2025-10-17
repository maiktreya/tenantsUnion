from typing import List, Optional, Callable
from nicegui import ui, events
from state.base import BaseTableState
from .utils import format_date_es  # Import the date formatting function


class DataTable:
    """Reusable data table with client-side multi-sort, filtering, and pagination."""

    def __init__(
        self,
        state: BaseTableState,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        on_row_click: Optional[Callable] = None,
        show_actions: bool = True,
        hidden_columns: Optional[List[str]] = None,
    ):
        self.state = state
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_row_click = on_row_click
        self.show_actions = show_actions
        self.hidden_columns = hidden_columns or []
        self.container = None

    def create(self) -> ui.column:
        """Create the table UI's container and initial render."""
        self.container = ui.column().classes("w-full")
        self.refresh()
        return self.container

    def refresh(self):
        """Re-renders the entire table display based on the current state."""
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

            if not records and self.state.records:
                ui.label("Ningún registro coincide con los filtros actuales.").classes(
                    "text-gray-500"
                )
                self._create_pagination()
                return

            if records:
                all_columns = list(records[0].keys())
                columns = [col for col in all_columns if col not in self.hidden_columns]

                with ui.card().classes("w-full"):
                    with ui.row().classes("w-full bg-gray-100 p-2 items-center"):
                        for column in columns:
                            with ui.row().classes(
                                "flex-1 items-center cursor-pointer gap-1"
                            ).on(
                                "click",
                                lambda e, c=column: self._sort_by_column(c, e),
                                ["shiftKey"],
                            ):
                                ui.label(column).classes("font-bold")
                                sort_info = next(
                                    (
                                        crit
                                        for crit in self.state.sort_criteria
                                        if crit[0] == column
                                    ),
                                    None,
                                )
                                if sort_info:
                                    icon = (
                                        "arrow_upward"
                                        if sort_info[1]
                                        else "arrow_downward"
                                    )
                                    ui.icon(icon, size="sm")
                                    if len(self.state.sort_criteria) > 1:
                                        sort_index = (
                                            self.state.sort_criteria.index(sort_info)
                                            + 1
                                        )
                                        ui.label(f"({sort_index})").classes("text-xs")

                        if self.show_actions:
                            ui.label("Acciones").classes("font-bold w-32 text-center")

                    for record in records:
                        row_classes = (
                            "w-full border-b p-2 hover:bg-gray-50 items-center"
                        )
                        if self.on_row_click:
                            row_classes += " cursor-pointer"

                        with ui.row().classes(row_classes) as row:
                            for column in columns:
                                value = record.get(column, "")

                                # If the column is a date, format it
                                if "fecha" in column.lower() and isinstance(value, str):
                                    display_value = format_date_es(value)
                                else:
                                    display_value = (
                                        value
                                        if value is not None and value != ""
                                        else "-"
                                    )

                                display_value_str = (
                                    str(display_value)[:75] + "..."
                                    if len(str(display_value)) > 75
                                    else str(display_value)
                                )
                                ui.label(display_value_str).classes("flex-1").tooltip(
                                    str(value)
                                )

                            if self.show_actions:
                                with ui.row().classes("w-32 gap-1 justify-center"):
                                    if self.on_edit:
                                        ui.button(
                                            icon="edit",
                                            on_click=lambda r=record: self.on_edit(r),
                                        ).props("size=sm flat dense color=orange-600")
                                    if self.on_delete:
                                        ui.button(
                                            icon="delete",
                                            on_click=lambda r=record: self.on_delete(r),
                                        ).props("size=sm flat dense color=negative")

                        if self.on_row_click:
                            row.on("click", lambda r=record: self.on_row_click(r))

            if self.state.get_total_pages() > 1:
                self._create_pagination()

    def _sort_by_column(self, column: str, e: events.GenericEventArguments):
        """Handle multi-column sorting with shift key."""
        is_shift_key = e.args.get("shiftKey", False)
        existing_criterion = next(
            (c for c in self.state.sort_criteria if c[0] == column), None
        )

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
            ui.button(icon="first_page", on_click=lambda: self._go_to_page(1)).props(
                "flat dense"
            ).set_enabled(current > 1)
            ui.button(
                icon="chevron_left", on_click=lambda: self._go_to_page(current - 1)
            ).props("flat dense").set_enabled(current > 1)

            with ui.row().classes("items-center gap-2"):
                ui.label("Página")
                ui.number(
                    value=current,
                    min=1,
                    max=total_pages,
                    on_change=lambda e: self._go_to_page(
                        int(e.value) if e.value else 1
                    ),
                ).props("dense outlined").classes("w-16")
                ui.label(f"de {total_pages}")

            ui.button(
                icon="chevron_right", on_click=lambda: self._go_to_page(current + 1)
            ).props("flat dense").set_enabled(current < total_pages)
            ui.button(
                icon="last_page", on_click=lambda: self._go_to_page(total_pages)
            ).props("flat dense").set_enabled(current < total_pages)

            with ui.row().classes("items-center gap-2 ml-4"):
                ui.label("Mostrar:")
                ui.select(
                    options=[5, 10, 25, 50, 100],
                    value=self.state.page_size.value,
                    on_change=lambda e: self._change_page_size(e.value),
                ).props("dense").classes("w-20")
                ui.label("por página")

    def _go_to_page(self, page_num: int):
        """Navigate to a specific page."""
        total_pages = self.state.get_total_pages()
        if page_num and 1 <= page_num <= total_pages:
            self.state.current_page.set(page_num)
        self.refresh()

    def _change_page_size(self, new_size: int):
        """Updates the page size, resets to page 1, and refreshes the table."""
        self.state.page_size.set(new_size)
        self.state.current_page.set(1)  # Reset to the first page
        self.refresh()
