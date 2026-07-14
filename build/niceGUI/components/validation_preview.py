# build/niceGUI/components/validation_preview.py
import csv
import io
from typing import Any, Dict, List, Optional

from nicegui import ui

from components.data_table import DataTable
from state.base import BaseTableState


class ValidationPreviewPanel:
    """
    Reusable read-only preview grid for per-row dry-run validation results,
    built on the same `BaseTableState` + `DataTable` pair used everywhere
    else in the app (see `views/views_explorer.py`).

    Expects each result dict shaped like:
        {"row_number": int, "status": "valid" | "error",
         "preview_label": str, "issues": List[str]}
    — which is exactly what
    `services.relational_import_service.MultiTableImportService.validate_relational_import`
    returns, but nothing here depends on that specific caller: any importer
    that can produce this shape can reuse this panel.
    """

    def __init__(self):
        self.state = BaseTableState()
        self.state.page_size.set(10)
        self.table: Optional[DataTable] = None
        self.summary_label: Optional[ui.label] = None
        self._results: List[Dict[str, Any]] = []

    def create(self) -> ui.column:
        with ui.column().classes("w-full gap-2") as container:
            self.summary_label = ui.label("Sube un archivo CSV para ver la vista previa de validación.").classes(
                "text-sm text-gray-600"
            )
            self.table = DataTable(state=self.state, show_actions=False)
            self.table.create()

        return container

    def set_results(self, results: List[Dict[str, Any]]):
        """Feeds a new batch of validation results into the panel and refreshes it."""
        self._results = results

        display_rows = [
            {
                "Fila": r["row_number"],
                "Estado": "✔ Válido" if r["status"] == "valid" else f"✘ {len(r['issues'])} error(es)",
                "Resumen": r["preview_label"],
                "Detalle": "; ".join(r["issues"]) if r["issues"] else "—",
            }
            for r in results
        ]

        self.state.set_records(display_rows)
        if self.table:
            self.table.refresh()
        self._refresh_summary()

    def clear(self):
        self.set_results([])

    def _refresh_summary(self):
        if not self.summary_label:
            return

        total = self.total_count
        errors = self.error_count

        if total == 0:
            self.summary_label.set_text("Sube un archivo CSV para ver la vista previa de validación.")
            return

        if errors == 0:
            self.summary_label.set_text(f"✔ Las {total} filas pasan la validación previa.")
            self.summary_label.classes(replace="text-sm text-green-700")
        else:
            self.summary_label.set_text(
                f"⚠ {total - errors} de {total} filas pasan la validación · {errors} con errores."
            )
            self.summary_label.classes(replace="text-sm text-orange-700")

    @property
    def error_count(self) -> int:
        return sum(1 for r in self._results if r["status"] != "valid")

    @property
    def total_count(self) -> int:
        return len(self._results)

    def to_csv_bytes(self) -> bytes:
        """Renders the current results as a downloadable CSV validation report."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["fila", "estado", "resumen", "detalle_errores"])
        for r in self._results:
            writer.writerow(
                [
                    r["row_number"],
                    "valido" if r["status"] == "valid" else "error",
                    r["preview_label"],
                    "; ".join(r["issues"]),
                ]
            )
        return b"\xef\xbb\xbf" + buffer.getvalue().encode("utf-8")