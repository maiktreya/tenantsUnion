from typing import List, Optional, Callable
from datetime import datetime
from nicegui import ui, events
from state.base import BaseTableState
from .utils import format_date_es


def _format_cell_value(column: str, value: any) -> str:
    """Format a cell value: dates/timestamps get parsed and localized, blanks become '-'."""
    if value and isinstance(value, str) and any(k in column.lower() for k in ["fecha", "updated", "_at"]):
        try:
            clean_str = value.replace("T", " ").replace("Z", "").split(".")[0]
            dt = datetime.fromisoformat(clean_str)
            return dt.strftime("%d/%m/%Y" if dt.hour == 0 and dt.minute == 0 else "%d/%m/%Y %H:%M")
        except Exception:
            return format_date_es(value)  # Fallback parser for non-ISO date strings
    return value if value is not None and value != "" else "-"

def _format_cell_value(column: str, value: any) -> str:
    """Format a cell value: coordinates get unpushed from GeoJSON, dates get localized, blanks become '-'."""
    # 1. GeoJSON PostGIS Geometry Formatter
    # Catches the dictionary response passed down by PostgREST spatial types
    if isinstance(value, dict) and value.get("type") == "Point" and isinstance(value.get("coordinates"), list):
        coords = value["coordinates"]
        if len(coords) >= 2:
            # GeoJSON spec sets coordinates array as [Longitude, Latitude]
            # We invert them here to render human-readable "Latitude, Longitude"
            return f"{coords[1]}, {coords[0]}"

    # 2. Date and Timestamp Formatter
    if value and isinstance(value, str) and any(k in column.lower() for k in ["fecha", "updated", "_at"]):
        try:
            clean_str = value.replace("T", " ").replace("Z", "").split(".")[0]
            dt = datetime.fromisoformat(clean_str)
            return dt.strftime("%d/%m/%Y" if dt.hour == 0 and dt.minute == 0 else "%d/%m/%Y %H:%M")
        except Exception:
            return format_date_es(value)  # Fallback parser for non-ISO date strings
            
    return value if value is not None and value != "" else "-"

class DataTable:
    """Reusable data table with sorting, filtering, pagination, resizable columns, and themeable colors."""

    def __init__(
        self,
        state: BaseTableState,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        on_row_click: Optional[Callable] = None,
        show_actions: bool = True,
        hidden_columns: Optional[List[str]] = None,
        # Branding/style parameters — defaults anchored to the brand red (#dc2626 = Tailwind red-600).
        bg_header: str = "bg-red-50/40",
        text_header: str = "text-red-700",
        border_style: str = "border-red-100",
        handle_color: str = "hover:bg-red-600 active:bg-red-700",
        row_stripe: str = "bg-red-50/25",
        row_hover: str = "hover:bg-red-50/50",
        min_col_width: str = "140px",
        max_col_width: str = "320px",
    ):
        self.state = state
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_row_click = on_row_click
        self.show_actions = show_actions
        self.hidden_columns = hidden_columns or []
        self.container = None

        self.bg_header = bg_header
        self.text_header = text_header
        self.border_style = border_style
        self.handle_color = handle_color
        self.row_stripe = row_stripe
        self.row_hover = row_hover
        self.min_col_width = min_col_width
        self.max_col_width = max_col_width

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

                # Shrink-wraps to content width (no dead space on narrow tables) but caps
                # at max-w-full and scrolls horizontally on wide ones.
                with ui.card().classes("w-fit max-w-full overflow-x-auto p-0 rounded-xl shadow-sm border bg-white").classes(self.border_style):

                    table_id = f"data_table_grid_{id(self)}"
                    # Each column gets a flexible width band instead of a fixed size,
                    # so narrow and wide tables both render sensibly.
                    col_width = f"minmax({self.min_col_width}, {self.max_col_width})"
                    init_widths = " ".join([col_width for _ in columns])
                    if self.show_actions:
                        init_widths += " 120px"

                    grid_canvas = ui.element('div').props(f'id="{table_id}"').style(
                        f"display: grid; grid-template-columns: {init_widths};"
                    ).classes("w-full text-slate-700 bg-white")

                    with grid_canvas:
                        # Header row: column labels, sort indicators, resize handles.
                        for idx, column in enumerate(columns):
                            header_cell = ui.element('div').classes(
                                f"grid-header-track p-3 font-bold text-xs uppercase tracking-wider "
                                f"relative border-b border-r flex items-center select-none overflow-hidden {self.bg_header} {self.border_style}"
                            )
                            with header_cell:
                                ui.label(column.replace("_", " ")).classes(f"truncate flex-1 cursor-pointer {self.text_header} hover:text-red-900").on(
                                    "click",
                                    lambda e, c=column: self._sort_by_column(c, e),
                                    ["shiftKey"],
                                )

                                # Sort direction icon, plus position badge when multi-sorting.
                                sort_info = next((crit for crit in self.state.sort_criteria if crit[0] == column), None)
                                if sort_info:
                                    icon = "arrow_upward" if sort_info[1] else "arrow_downward"
                                    ui.icon(icon, size="xs").classes(f"{self.text_header} ml-1")
                                    if len(self.state.sort_criteria) > 1:
                                        sort_index = self.state.sort_criteria.index(sort_info) + 1
                                        ui.label(f"({sort_index})").classes(f"text-xs {self.text_header} ml-0.5")

                                # Drag handle for column resizing.
                                ui.element('div').classes(
                                    f"resizer-handle absolute right-0 top-0 bottom-0 w-1.5 "
                                    f"cursor-col-resize transition-colors z-10 {self.handle_color}"
                                ).props(f'data-col-idx="{idx}"')

                        if self.show_actions:
                            with ui.element('div').classes(f"grid-header-track p-3 font-bold text-xs uppercase tracking-wider border-b border-r text-center {self.bg_header} {self.border_style}"):
                                ui.label("Acciones").classes(self.text_header)

                        # Data rows, alternating stripe background.
                        for row_idx, record in enumerate(records):
                            row_bg = self.row_stripe if row_idx % 2 == 1 else "bg-white"

                            for column in columns:
                                value = record.get(column, "")
                                display_value = _format_cell_value(column, value)

                                cell = ui.element('div').classes(
                                    f"p-3 text-sm border-b border-r flex items-center overflow-hidden transition-colors {row_bg} {self.border_style}"
                                )
                                with cell:
                                    ui.label(str(display_value)).classes("truncate w-full").tooltip(str(value))

                                if self.on_row_click:
                                    cell.classes(f"cursor-pointer {self.row_hover}")
                                    cell.on("click", lambda _, r=record: self.on_row_click(r))

                            if self.show_actions:
                                action_cell = ui.element('div').classes(
                                    f"p-1 border-b flex items-center justify-center gap-1 shrink-0 {row_bg} {self.border_style}"
                                )
                                with action_cell:
                                    if self.on_edit:
                                        ui.button(icon="edit", on_click=lambda r=record: self.on_edit(r)).props(
                                            "size=sm flat dense color=red-600"
                                        ).classes("rounded hover:bg-red-50")
                                    if self.on_delete:
                                        ui.button(icon="delete", on_click=lambda r=record: self.on_delete(r)).props(
                                            "size=sm flat dense color=negative"
                                        ).classes("rounded hover:bg-red-50")

                self._inject_resize_handlers(table_id)

            if self.state.get_total_pages() > 1:
                self._create_pagination()

    def _inject_resize_handlers(self, table_id: str):
        """Wire up pointer drag handlers so each column-resize handle resizes its column."""
        js_code = """
        (function() {
            const grid = document.getElementById('TARGET_GRID_ID');
            if (!grid) return;
            
            grid.querySelectorAll('.resizer-handle').forEach(handle => {
                handle.addEventListener('pointerdown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const colIdx = parseInt(e.target.getAttribute('data-col-idx'));
                    const startX = e.clientX;
                    
                    const headerTracks = Array.from(grid.querySelectorAll('.grid-header-track'));
                    const currentWidths = headerTracks.map(cell => cell.getBoundingClientRect().width);
                    const startWidth = currentWidths[colIdx];
                    
                    handle.setPointerCapture(e.pointerId);
                    
                    function onPointerMove(ev) {
                        const deltaX = ev.clientX - startX;
                        currentWidths[colIdx] = Math.max(70, startWidth + deltaX);
                        grid.style.gridTemplateColumns = currentWidths.map(w => w + 'px').join(' ');
                    }
                    
                    function onPointerUp(ev) {
                        handle.releasePointerCapture(ev.pointerId);
                        document.removeEventListener('pointermove', onPointerMove);
                        document.removeEventListener('pointerup', onPointerUp);
                    }
                    
                    document.addEventListener('pointermove', onPointerMove);
                    document.addEventListener('pointerup', onPointerUp);
                });
            });
        })();
        """.replace('TARGET_GRID_ID', table_id)
        ui.run_javascript(js_code)

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
            ui.button(icon="last_page", on_click=lambda: self._go_to_page(total_pages)).props(
                "flat dense"
            ).set_enabled(current < total_pages)

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