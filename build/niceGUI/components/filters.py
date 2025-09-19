# build/niceGUI/components/filters.py (Refactored with Single Date Filter Pattern)

from typing import Dict, List, Callable, Any, Optional
from nicegui import ui
import unicodedata
import re
from datetime import datetime
import logging

log = logging.getLogger(__name__)


# --- Helper Functions ---
def _is_numeric_string(value: str) -> bool:
    if not value:
        return False
    return bool(re.match(r"^-?(?:\d+\.?\d*|\.\d+)$", value.strip()))


def _normalize_for_sorting(value: Any) -> str:
    if value is None:
        return ""
    str_value = str(value).strip()
    if _is_numeric_string(str_value):
        try:
            return f"{float(str_value):015.3f}"
        except ValueError:
            pass
    normalized = unicodedata.normalize("NFD", str_value.lower())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


# --- Refactored Filter Panel ---
class FilterPanel:
    """
    Reusable client-side filter panel with a consolidated date range filter
    for an improved user experience.
    """

    def __init__(
        self,
        records: List[Dict],
        on_filter_change: Callable[[str, Any], None],
        table_config: Optional[Dict] = None,
    ):
        self.records = records
        self.on_filter_change = on_filter_change
        self.table_config = table_config or {}

        # UI elements
        self.container: Optional[ui.column] = None
        self.inputs: Dict[str, ui.element] = {}
        self.date_field_select: Optional[ui.select] = None
        self.start_date_input: Optional[ui.input] = None
        self.end_date_input: Optional[ui.input] = None

        # Internal state for the single date filter
        self.selected_date_column: Optional[str] = None
        self.date_range_values: Dict[str, str | None] = {"start": None, "end": None}

    def create(self) -> ui.column:
        """Create the filter panel UI."""
        self.container = ui.column().classes("w-full")
        self.refresh()
        return self.container

    def _get_sorted_unique_values(self, column: str) -> List[Any]:
        unique_values = list(
            set(r.get(column) for r in self.records if r.get(column) is not None)
        )
        try:
            return sorted(unique_values, key=_normalize_for_sorting)
        except Exception:
            return sorted(unique_values, key=lambda x: str(x).lower())

    def refresh(self):
        """Create or refresh filter inputs based on data."""
        if not self.container or not self.records:
            return

        self.container.clear()
        self.inputs.clear()

        columns = list(self.records[0].keys()) if self.records else []
        date_columns = [
            col for col in columns if any(s in col.lower() for s in ["fecha", "date"])
        ]
        standard_columns = [col for col in columns if col not in date_columns]

        with self.container:
            ui.label("Filtros y Búsqueda").classes("text-h6 mb-2")
            with ui.row().classes("w-full gap-4 flex-wrap items-center"):
                self.inputs["global_search"] = (
                    ui.input(
                        label="Búsqueda rápida",
                        on_change=lambda e: self.on_filter_change(
                            "global_search", e.value
                        ),
                    )
                    .props("dense clearable outlined")
                    .classes("w-64")
                )

                # ** 1. New, Consolidated Date Filter UI **
                if date_columns:
                    self._create_date_filter_ui(date_columns)

                # ** 2. Standard Column Filters **
                for column in standard_columns:
                    # Your original logic to decide if a dropdown is appropriate
                    if (
                        1
                        < len(
                            set(
                                r.get(column)
                                for r in self.records
                                if r.get(column) is not None
                            )
                        )
                        <= 16
                    ):
                        self.inputs[column] = (
                            ui.select(
                                options=self._get_sorted_unique_values(column),
                                label=f"Filtrar {column}",
                                multiple=True,
                                clearable=True,
                                on_change=lambda e, col=column: self.on_filter_change(
                                    col, e.value
                                ),
                            )
                            .props("dense outlined")
                            .classes("w-64")
                        )

    def _create_date_filter_ui(self, date_columns: List[str]):
        """Creates the consolidated UI for date filtering."""
        with ui.row().classes("gap-2 items-center no-wrap"):
            # This dropdown lets the user choose which date field to filter on
            self.date_field_select = (
                ui.select(
                    options=date_columns,
                    label="Filtrar por Fecha",
                    on_change=self._on_date_field_select,
                    clearable=True,
                )
                .classes("w-48")
                .props("dense outlined")
            )

            # The date range inputs are only visible when a field is selected
            with ui.row().classes("gap-2 no-wrap").bind_visibility_from(
                self.date_field_select, "value"
            ):
                self.start_date_input = (
                    ui.input(label="Desde").props("dense outlined").classes("w-32")
                )
                with self.start_date_input.add_slot("append"):
                    with ui.menu() as menu:
                        ui.date(
                            on_change=lambda e: self._on_date_change("start", e.value)
                        ).bind_value(self.start_date_input)
                    ui.icon("edit_calendar").classes("cursor-pointer").on(
                        "click", menu.open
                    )

                self.end_date_input = (
                    ui.input(label="Hasta").props("dense outlined").classes("w-32")
                )
                with self.end_date_input.add_slot("append"):
                    with ui.menu() as menu:
                        ui.date(
                            on_change=lambda e: self._on_date_change("end", e.value)
                        ).bind_value(self.end_date_input)
                    ui.icon("edit_calendar").classes("cursor-pointer").on(
                        "click", menu.open
                    )

    def _on_date_field_select(self, event: Any):
        """Handles selection of the date column to filter by."""
        new_column = event.value

        # **Crucially, clear the filter for the old column from the main state**
        if self.selected_date_column:
            self.on_filter_change(f"date_range_{self.selected_date_column}", None)

        self.selected_date_column = new_column

        # Reset the input fields and internal state
        self.date_range_values = {"start": None, "end": None}
        if self.start_date_input:
            self.start_date_input.set_value(None)
        if self.end_date_input:
            self.end_date_input.set_value(None)

        # If a new column is selected, trigger an empty filter update to clear results
        if new_column:
            self._on_date_change(None, None)

    def _on_date_change(self, part: Optional[str], value: Optional[str]):
        """Updates internal state and calls the main filter callback for date ranges."""
        if part:
            self.date_range_values[part] = value if value else None

        # Only proceed if a date column has been selected
        if self.selected_date_column:
            self.on_filter_change(
                f"date_range_{self.selected_date_column}",
                self.date_range_values.copy(),
            )

    def clear(self):
        """Clears all filter inputs and resets internal state."""
        for key, element in self.inputs.items():
            if isinstance(element, ui.select) and element.props.get("multiple"):
                element.set_value([])
            else:
                element.set_value("")

        if self.date_field_select:
            self.date_field_select.set_value(None)
