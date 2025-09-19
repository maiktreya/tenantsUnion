# build/niceGUI/components/filters.py (Corrected)

from typing import Dict, List, Callable, Any, Optional
from nicegui import ui
import unicodedata
import re


def _is_numeric_string(value: str) -> bool:
    """Check if a string represents a number (integer or float)."""
    if not value:
        return False
    return bool(re.match(r"^-?(?:\d+\.?\d*|\.\d+)$", value.strip()))


def _normalize_for_sorting(value) -> str:
    """Normalize a value for proper sorting."""
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


class FilterPanel:
    """Reusable client-side filter panel with dynamic control generation."""

    def __init__(
        self,
        records: List[Dict],
        on_filter_change: Callable[[str, Any], None],
        table_config: Optional[Dict] = None,
    ):
        self.records = records
        self.on_filter_change = on_filter_change
        self.table_config = table_config or {}
        self.container = None
        self.inputs: Dict[str, ui.element] = {}
        self.date_range_filters: Dict[str, Dict[str, str | None]] = {}

    def create(self) -> ui.column:
        """Create the filter panel UI."""
        self.container = ui.column().classes("w-full")
        self.refresh()
        return self.container

    def _get_sorted_unique_values(self, column: str) -> List[Any]:
        """Get unique values for a column, properly sorted."""
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
        self.date_range_filters.clear()

        columns = list(self.records[0].keys()) if self.records else []

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
                    .classes("w-64")
                    .props("dense clearable outlined")
                )

                for column in columns:
                    unique_values = [
                        r.get(column) for r in self.records if r.get(column) is not None
                    ]
                    unique_count = len(set(unique_values))
                    is_date_column = any(
                        substr in column.lower() for substr in ["fecha", "date"]
                    )

                    if column == "cuota":
                        sorted_unique_vals = self._get_sorted_unique_values(column)
                        options = {
                            "__GT_ZERO__": "Con Cuota (> 0)",
                            **{val: str(val) for val in sorted_unique_vals},
                        }
                        self.inputs[column] = (
                            ui.select(
                                options=options,
                                label="Filtrar Cuota",
                                multiple=True,
                                clearable=True,
                                on_change=lambda e, col=column: self.on_filter_change(
                                    col, e.value
                                ),
                            )
                            .classes("w-64")
                            .props("dense outlined")
                        )

                    elif is_date_column:
                        with ui.element("div").classes("flex flex-col gap-1"):
                            ui.label(f"Rango {column}").classes(
                                "text-xs text-gray-500 ml-1"
                            )
                            with ui.row().classes("gap-2 items-center no-wrap"):
                                self.date_range_filters[column] = {
                                    "start": None,
                                    "end": None,
                                }
                                with ui.input(label="Desde").props(
                                    "dense outlined"
                                ).classes("w-32") as start_input:
                                    start_input.on(
                                        "update:model-value",
                                        lambda e, col=column: self._on_date_change(
                                            col, "start", e.value
                                        ),
                                    )
                                    with start_input.add_slot("append"):
                                        with ui.menu() as start_menu:
                                            ui.date().bind_value(start_input)
                                        ui.icon("edit_calendar").on(
                                            "click", start_menu.open
                                        ).classes("cursor-pointer")

                                with ui.input(label="Hasta").props(
                                    "dense outlined"
                                ).classes("w-32") as end_input:
                                    end_input.on(
                                        "update:model-value",
                                        lambda e, col=column: self._on_date_change(
                                            col, "end", e.value
                                        ),
                                    )
                                    with end_input.add_slot("append"):
                                        with ui.menu() as end_menu:
                                            ui.date().bind_value(end_input)
                                        ui.icon("edit_calendar").on(
                                            "click", end_menu.open
                                        ).classes("cursor-pointer")

                                self.inputs[f"date_start_{column}"] = start_input
                                self.inputs[f"date_end_{column}"] = end_input

                    elif (
                        1 < unique_count <= 16
                        and "id" not in column.lower()
                        and unique_count < len(unique_values) * 0.8
                    ):
                        sorted_unique_vals = self._get_sorted_unique_values(column)
                        self.inputs[column] = (
                            ui.select(
                                options=sorted_unique_vals,
                                label=f"Filtrar {column}",
                                multiple=True,
                                clearable=True,
                                on_change=lambda e, col=column: self.on_filter_change(
                                    col, e.value
                                ),
                            )
                            .classes("w-64")
                            .props("dense outlined")
                        )

    def _on_date_change(self, column: str, part: str, value: str):
        """Updates the internal date range state and calls the main filter callback."""
        if column in self.date_range_filters:
            self.date_range_filters[column][part] = value if value else None
            self.on_filter_change(
                f"date_range_{column}", self.date_range_filters[column]
            )

    def clear(self):
        """Clears all filter inputs."""
        for key, element in self.inputs.items():
            if key.startswith("date_"):
                element.value = None
            else:
                element.value = (
                    []
                    if isinstance(element, ui.select) and element.props.get("multiple")
                    else ""
                )
        self.date_range_filters.clear()
