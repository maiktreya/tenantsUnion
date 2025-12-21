# build/niceGUI/views/afiliadas_importer.py

import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Callable, Awaitable
from nicegui import ui, events, app

from api.client import APIClient
from api.validate import validator
from state.app_state import GenericViewState
from services.import_service import AfiliadasImportService, ImportResult
from components.importer_panels import render_preview_tabs
from components.exporter import export_to_csv
from components.importer_normalization import normalize_for_sorting
from components.upload_event_utils import read_upload_event_bytes
from config import FAILED_EXPORT_FIELD_MAP

log = logging.getLogger(__name__)


class AfiliadasImporterView:
    """
    A lightweight view that orchestrates the UI for importing afiliadas.
    Business logic is delegated to AfiliadasImportService.
    """

    def __init__(self, api_client: APIClient):
        self.api = api_client
        # Persist state per-client tab
        if "afiliadas_importer_state" not in app.storage.client:
            app.storage.client["afiliadas_importer_state"] = GenericViewState()
        self.state: GenericViewState = app.storage.client["afiliadas_importer_state"]
        
        # Instantiate the service
        self.service = AfiliadasImportService(api_client)

        # UI elements
        self.panels: Dict[str, Optional[ui.column]] = {
            "afiliadas": None,
            "pisos": None,
            "bloques": None,
            "facturacion": None,
        }
        self.import_button: Optional[ui.button] = None
        self._suggestion_task: Optional[asyncio.Task] = None
        
        # Result caching for UI dialogs
        self._failed_records: List[Dict[str, Any]] = []
        self._last_import_log: List[str] = []

        # Reusable dialogs
        self._failed_preview_dialog: Optional[ui.dialog] = None
        self._failed_preview_container: Optional[ui.column] = None

    def create(self) -> ui.column:
        """Create the main UI for the CSV importer view."""
        with ui.column().classes("w-full p-4 gap-4") as container:
            ui.label("Importar Nuevas Afiliadas desde CSV").classes("text-h6 font-italic")
            ui.markdown(
                "Sube un archivo CSV. Los datos se validarán y se mostrarán para revisión antes de la importación final."
            )

            with ui.row().classes("w-full gap-4 items-center"):
                ui.upload(
                    on_upload=self._handle_upload,
                    auto_upload=True,
                    label="Subir archivo CSV",
                ).props('accept=".csv"')
                
                self.import_button = ui.button(
                    "Iniciar Importación", icon="upload", on_click=self._start_import
                ).props("color=orange-600")

            with ui.tabs().props('align="left"') as tabs:
                for key in self.panels:
                    ui.tab(key, label=key.replace("_", " ").title())

            with ui.tab_panels(tabs, value="afiliadas").classes("w-full border rounded-md"):
                for key in self.panels:
                    with ui.tab_panel(key):
                        self.panels[key] = ui.column().classes("w-full")

            # Initialize reusable dialogs
            if not self._failed_preview_dialog:
                self._failed_preview_dialog = ui.dialog()
                with self._failed_preview_dialog, ui.card().classes("w-[90vw] max-w-[1200px]"):
                    ui.label("Registros Fallidos").classes("text-h6")
                    self._failed_preview_container = ui.column().classes("w-full gap-2")
                    ui.button("Cerrar", on_click=self._failed_preview_dialog.close).classes("self-end mt-2")

        # If revisiting tab, re-render state
        if self.state.records:
            self._render_all_panels()

        return container

    # ====================================================================
    # UI Orchestration (Upload & Import)
    # ====================================================================

    async def _handle_upload(self, e: events.UploadEventArguments):
        """Passes file bytes to the service and updates state."""
        self._failed_records = []
        try:
            csv_bytes = await read_upload_event_bytes(e)
            
            # Delegate parsing and preparation to service
            prepared_records = await self.service.prepare_records_from_csv(csv_bytes)
            
            self.state.set_records(prepared_records)
            self._render_all_panels()
            ui.notify(
                f"{len(prepared_records)} registros han sido procesados.", type="positive"
            )
        except Exception as ex:
            log.error("Error processing CSV file.", exc_info=True)
            ui.notify(f"Error al procesar el archivo: {ex}", type="negative")
            self.state.set_records([])
            self._render_all_panels()

    async def _start_import(self):
        """Consumes the service's async generator to drive the import UI."""
        if not self.all_records_valid:
            ui.notify("Hay registros con errores. Corríjalos antes de importar.", type="negative")
            return

        # Prepare progress UI
        with ui.dialog() as progress_dialog, ui.card().classes("min-w-[700px]"):
            ui.label("Proceso de Importación").classes("text-h6")
            status_label = ui.label(f"Iniciando importación...")
            log_area = ui.log(max_lines=15).classes("w-full h-64 bg-gray-100 p-2 rounded")
        
        progress_dialog.open()

        import_result: Optional[ImportResult] = None

        # --- THE CORE ASYNC GENERATOR LOOP ---
        try:
            async for update in self.service.execute_import_process(self.state.records):
                if isinstance(update, str):
                    # It's a status message
                    status_label.set_text(update.split("\n")[-1])
                    log_area.push(update)
                elif isinstance(update, ImportResult):
                    # It's the final result
                    import_result = update
        except Exception as e:
            ui.notify(f"Error crítico durante la importación: {e}", type="negative")
            log.exception("Critical import error")
        # -------------------------------------

        progress_dialog.close()

        if import_result:
            self._failed_records = import_result.failed_snapshots
            self._last_import_log = import_result.log
            self._show_summary_dialog(import_result)
            
            # Clear state on success (or partial success) to prevent re-importing duplicates
            self.state.set_records([])
            self._render_all_panels()

    # ====================================================================
    # UI Rendering & Interaction Helpers
    # ====================================================================

    def _show_summary_dialog(self, result: ImportResult):
        """Displays the post-import summary."""
        with ui.dialog() as summary_dialog, ui.card().classes("w-[90vw] max-w-[1200px]"):
            ui.label("Resultado de la Importación").classes("text-h6 mb-2")
            with ui.column().classes("w-full gap-4"):
                with ui.card().classes("w-full"):
                    if result.success_count > 0:
                        ui.markdown(f"✅ **Se importaron {result.success_count} de {result.total_records} registros exitosamente.**").classes("text-positive")
                    if result.failed_imports:
                        ui.markdown(f"❌ **Fallaron {len(result.failed_imports)} de {result.total_records} registros.**").classes("text-negative")

                with ui.card().classes("w-full"):
                    ui.label("Errores").classes("text-subtitle2 mb-1")
                    if result.failed_imports:
                        ui.table(
                            columns=[{"name": "afiliada", "label": "Afiliada", "field": "afiliada"},
                                     {"name": "error", "label": "Error", "field": "error"}],
                            rows=result.failed_imports,
                            row_key="afiliada",
                        ).classes("w-full")
                    else:
                        ui.label("Sin errores.").classes("text-gray-500")

                with ui.card().classes("w-full"):
                    ui.label("Registro Completo").classes("text-subtitle2 mb-1")
                    ui.textarea(value="\n".join(result.log)).props("readonly outlined").classes("w-full h-[40vh]")
                    with ui.row().classes("w-full justify-end mt-2"):
                        ui.button("Exportar registro", on_click=self._export_import_log).props("color=secondary")

            if self._failed_records:
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button("Ver Registros Fallidos", on_click=self._open_failed_records_preview).props("color=warning")
                    ui.button("Exportar CSV de Fallidos", on_click=self._export_failed_records_csv).props("color=primary")

            ui.button("Cerrar", on_click=summary_dialog.close).classes("mt-4 self-end")
        summary_dialog.open()

    @property
    def all_records_valid(self) -> bool:
        if not self.state.records:
            return False
        return all(r.get("validation", {}).get("is_valid", False) for r in self.state.records)

    def _render_all_panels(self):
        render_preview_tabs(
            state=self.state,
            panels=self.panels,
            on_sort=self._sort_by_column,
            on_drop=self._drop_record,
            on_revalidate=self._revalidate_record,
            on_bloque_change=self._handle_bloque_assignment_change,
            on_apply_suggestion=self._apply_suggested_bloque,
            on_clear_assignment=self._clear_bloque_assignment,
            on_score_limit_change=self._on_score_limit_change,
            get_bloque_score_limit=lambda: self.service.bloque_score_limit,
            on_reset_bloques=self._reset_bloques_entries,
        )
        self._update_import_button_state()

    def _update_import_button_state(self):
        if self.import_button:
            self.import_button.set_enabled(self.all_records_valid)

    # --- Interaction Handlers (Delegating to service or local state logic) ---

    async def _on_score_limit_change(self, new_limit: float):
        if new_limit is not None and abs(new_limit - self.service.bloque_score_limit) > 0.001:
            self.service.set_score_limit(new_limit)
            await self._schedule_refresh()

    async def _schedule_refresh(self):
        # Debounce/Cancel previous task
        if self._suggestion_task and not self._suggestion_task.done():
            self._suggestion_task.cancel()
            try:
                await self._suggestion_task
            except asyncio.CancelledError:
                pass

        async def refresh_task():
            await self.service.apply_batch_bloque_suggestions(self.state.records)
            self._render_all_panels()

        self._suggestion_task = asyncio.create_task(refresh_task())
        try:
            await self._suggestion_task
        except asyncio.CancelledError:
            pass
        finally:
            self._suggestion_task = None

    def _revalidate_record(self, record: Dict):
        # Validate locally using the shared validator
        af_data, p_data, b_data, f_data = (
            record.get("afiliada", {}), record.get("piso", {}), record.get("bloque", {}), record.get("facturacion", {})
        )
        if cif_val := af_data.get("cif"):
            af_data["cif"] = str(cif_val).strip().upper()

        is_valid_af, err_af = validator.validate_record("afiliadas", af_data, "create")
        is_valid_p, err_p = validator.validate_record("pisos", p_data, "create")
        is_valid_b, err_b = validator.validate_record("bloques", b_data, "create")
        is_valid_f, err_f = validator.validate_record("facturacion", f_data, "create")

        validation = record.setdefault("validation", {})
        validation["is_valid"] = (is_valid_af and is_valid_p and is_valid_b and is_valid_f)
        validation["errors"] = err_af + err_p + err_b + err_f

        # Async duplicate check via service
        self._schedule_background_task(lambda: self._refresh_record_statuses(record))

        # UI updates
        for updater in record.get("ui_updaters", {}).values():
            updater()
        self._update_import_button_state()

    async def _refresh_record_statuses(self, record: Dict):
        """Asks service to check if CIF/Address exists, then updates UI."""
        # This reuses logic from the service components
        self.service._sync_metadata_from_status_cache(record)
        # Force UI repaint of specific row elements
        for updater in record.get("ui_updaters", {}).values():
            updater()

    # --- Standard UI Event Handlers (Sorting, Dropping, Dialogs) ---

    def _sort_by_column(self, column: str):
        if self.state.sort_criteria and self.state.sort_criteria[0][0] == column:
            is_reverse = self.state.sort_criteria[0][1]
        else:
            is_reverse = False

        self.state.records.sort(
            key=lambda r: normalize_for_sorting(
                r["validation"]["is_valid"]
                if column == "is_valid"
                else next(
                    (r[key].get(column) for key in ["afiliada", "piso", "facturacion", "bloque"] if column in r.get(key, {})),
                    None,
                )
            ),
            reverse=is_reverse,
        )
        self.state.sort_criteria = [(column, not is_reverse)]
        self._render_all_panels()

    def _drop_record(self, record_to_drop: Dict):
        self.state.records.remove(record_to_drop)
        self._render_all_panels()

    def _handle_bloque_assignment_change(self, record: Dict):
        # We need to hydrate the manual block if an ID was typed
        self._schedule_background_task(lambda: self._hydrate_assigned_bloque(record))
        self._revalidate_record(record)

    async def _hydrate_assigned_bloque(self, record: Dict):
        # Helper to fetch block details if user manually entered an ID
        bloque_id = (
            int(record.get("piso", {}).get("bloque_id"))
            if str(record.get("piso", {}).get("bloque_id")).isdigit()
            else None
        )
        record["piso"]["bloque_id"] = bloque_id
        if bloque_id:
            bloques = await self.api.get_records("bloques", {"id": f"eq.{bloque_id}"})
            if bloques:
                # Update metadata for UI display
                record["meta"]["bloque_manual"] = bloques[0]
        self._revalidate_record(record)

    def _apply_suggested_bloque(self, record: Dict):
        suggestion = record.get("meta", {}).get("bloque")
        if suggestion and suggestion.get("id"):
            record["piso"]["bloque_id"] = suggestion["id"]
            record.setdefault("bloque", {})["direccion"] = suggestion.get("direccion")
            self._handle_bloque_assignment_change(record)
        else:
            ui.notify("No hay sugerencia disponible.", type="warning")

    def _clear_bloque_assignment(self, record: Dict):
        from components.importer_utils import short_address
        record["piso"]["bloque_id"] = None
        record.setdefault("bloque", {})["direccion"] = short_address(
            record.get("piso", {}).get("direccion", "")
        )
        self._handle_bloque_assignment_change(record)

    def _reset_bloques_entries(self):
        if not self.state.records:
            return
        for record in self.state.records:
            self._clear_bloque_assignment(record)
        self._render_all_panels()

    def _schedule_background_task(self, coro_factory: Callable[[], Awaitable[Any]]):
        try:
            asyncio.get_running_loop().create_task(coro_factory())
        except RuntimeError:
            pass

    def _open_failed_records_preview(self):
        if not self._failed_preview_dialog or not self._failed_preview_container:
            ui.notify("Vista no disponible.", type="warning")
            return
        
        if not self._failed_records:
            ui.notify("No hay registros fallidos.", type="info")
            return

        columns, rows = self._get_failed_records_table_data()
        self._failed_preview_container.clear()
        with self._failed_preview_container:
            ui.table(columns=columns, rows=rows, row_key="__index").classes("w-full")
        self._failed_preview_dialog.open()

    def _get_failed_records_table_data(self) -> Tuple[List[Dict], List[Dict]]:
        # Map snapshots to table rows
        rows = []
        for idx, snapshot in enumerate(self._failed_records, start=1):
            row = {"__index": idx}
            for section, fields in FAILED_EXPORT_FIELD_MAP.items():
                data = snapshot.get(section, {}) or {}
                for field in fields:
                    row[f"{section}_{field}"] = data.get(field, "")
            row["error"] = snapshot.get("error", "")
            rows.append(row)
            
        columns = [{"name": "__index", "label": "#", "field": "__index", "align": "left"}]
        for section, fields in FAILED_EXPORT_FIELD_MAP.items():
            for field in fields:
                columns.append({
                    "name": f"{section}_{field}",
                    "label": f"{section.title()} - {field}",
                    "field": f"{section}_{field}"
                })
        columns.append({"name": "error", "label": "Error", "field": "error"})
        return columns, rows

    def _export_failed_records_csv(self):
        _, rows = self._get_failed_records_table_data()
        if rows:
            export_to_csv(rows, "afiliadas_import_fallidos.csv")

    def _export_import_log(self):
        if self._last_import_log:
            ui.download("\n".join(self._last_import_log).encode("utf-8"), "afiliadas_import_log.txt")