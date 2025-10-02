import pandas as pd
import io
import asyncio
import logging
import copy
from typing import Dict, Any, Optional, List, Tuple, Callable, Awaitable

from nicegui import ui, events
from api.client import APIClient
from api.validate import validator
from state.app_state import GenericViewState
from components.importer_utils import transform_and_validate_row, short_address
from components.importer_panels import render_preview_tabs
from components.exporter import export_to_csv
from components.importer_normalization import (
    normalize_address_key,
    normalize_for_sorting,
)
from components.importer_record_status import ImporterRecordStatusService
from config import FAILED_EXPORT_FIELD_MAP, DUPLICATE_NIF_WARNING

log = logging.getLogger(__name__)


class AfiliadasImporterView:
    """
    A view to import 'afiliadas' by orchestrating data parsing, UI components,
    and the final import process into the database.
    """

    def __init__(self, api_client: APIClient, state: GenericViewState):
        self.api = api_client
        self.state = state
        self.panels: Dict[str, Optional[ui.column]] = {
            "afiliadas": None,
            "pisos": None,
            "bloques": None,
            "facturacion": None,
        }
        self.import_button: Optional[ui.button] = None
        self.bloque_score_limit: float = 0.88
        self._suggestion_task: Optional[asyncio.Task] = None
        self._bloque_details_cache: Dict[int, Dict[str, Any]] = {}
        self._failed_records: List[Dict[str, Any]] = []
        self._failed_preview_dialog: Optional[ui.dialog] = None
        self._failed_preview_container: Optional[ui.column] = None
        self._last_import_log: List[str] = []
        self.status_service = ImporterRecordStatusService(api_client)

    def _schedule_background_task(
        self, coro_factory: Callable[[], Awaitable[Any]]
    ) -> None:
        """Run a coroutine immediately when no loop is active, otherwise schedule it."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.run(coro_factory())
            except Exception:
                log.exception("Background task failed during synchronous execution")
        else:
            loop.create_task(coro_factory())

    def create(self) -> ui.column:
        """Create the main UI for the CSV importer view."""
        with ui.column().classes("w-full p-4 gap-4") as container:
            ui.label("Importar Nuevas Afiliadas desde CSV").classes(
                "text-h6 font-italic"
            )
            ui.markdown(
                "Sube un archivo CSV. Los datos se validarán y se mostrarán en pestañas para su revisión y edición antes de la importación final."
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

            with ui.tab_panels(tabs, value="afiliadas").classes(
                "w-full border rounded-md"
            ):
                for key in self.panels:
                    with ui.tab_panel(key):
                        self.panels[key] = ui.column().classes("w-full")

            if not self._failed_preview_dialog:
                self._failed_preview_dialog = ui.dialog()
                with self._failed_preview_dialog, ui.card().classes(
                    "w-[90vw] max-w-[1200px]"
                ):
                    ui.label("Registros fallidos").classes("text-h6")
                    self._failed_preview_container = ui.column().classes("w-full gap-2")
                    ui.button(
                        "Cerrar", on_click=self._failed_preview_dialog.close
                    ).classes("self-end mt-2")
        return container

    @property
    def all_records_valid(self) -> bool:
        """A computed property to check if all records in the state are valid."""
        if not self.state.records:
            return False
        return all(
            r.get("validation", {}).get("is_valid", False) for r in self.state.records
        )

    async def _handle_upload(self, e: events.UploadEventArguments):
        """Handle the file upload, parse the data, fetch suggestions, and render the UI."""
        self._failed_records = []
        self.status_service.reset()
        try:
            content = e.content.read().decode("utf-8-sig")
            df = pd.read_csv(io.StringIO(content), header=None, dtype=str).fillna("")

            records = [
                rec
                for _, row in df.iloc[1:].iterrows()
                if (rec := transform_and_validate_row(row)) is not None
            ]

            self._bloque_details_cache.clear()
            self.state.set_records(records)
            await self._preload_record_status()
            await self._apply_batch_bloque_suggestions()
            self._render_all_panels()
            ui.notify(
                f"{len(records)} registros han sido procesados desde el archivo.",
                type="positive",
            )
        except Exception as ex:
            log.error("Error processing the uploaded CSV file.", exc_info=True)
            ui.notify(f"Error al procesar el archivo: {ex}", type="negative")
            self.state.set_records([])
            self._render_all_panels()

    def _render_all_panels(self):
        """Orchestrates the rendering of all data preview tabs using the dedicated component."""
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
            get_bloque_score_limit=lambda: self.bloque_score_limit,
            on_reset_bloques=self._reset_bloques_entries,
        )
        self._update_import_button_state()

    async def _preload_record_status(self):
        """Prime duplicate/existence caches and update record metadata."""
        records = self.state.records or []
        if not records:
            return

        await self.status_service.preload_afiliada_cifs(records)
        await self.status_service.preload_piso_addresses(records)

        for record in records:
            self._sync_metadata_from_status_cache(record, trigger_ui=False)

    def _sync_metadata_from_status_cache(
        self, record: Dict[str, Any], *, trigger_ui: bool
    ) -> None:
        """Mirror cached record status into metadata fields."""
        afiliada_cif = (
            str(record.get("afiliada", {}).get("cif", "")).strip().upper()
            if record.get("afiliada")
            else ""
        )
        exists_afiliada = bool(
            afiliada_cif
            and self.status_service.existing_afiliada_cifs.get(afiliada_cif)
        )
        self._apply_duplicate_status(record, exists_afiliada, trigger_ui=trigger_ui)

        direccion = (record.get("piso", {}).get("direccion") or "").strip()
        key = normalize_address_key(direccion)
        exists_piso = bool(self.status_service.existing_piso_addresses.get(key))
        self._apply_piso_existing_status(record, exists_piso, trigger_ui=trigger_ui)

    def _update_import_button_state(self):
        """Enables or disables the import button based on data validity."""
        if self.import_button:
            self.import_button.set_enabled(self.all_records_valid)

    def _sort_by_column(self, column: str):
        """Sorts the records based on a selected column and re-renders the UI."""
        # Check if the current sort is on the same column to determine direction
        if self.state.sort_criteria and self.state.sort_criteria[0][0] == column:
            # Stored flag tracks ascending; using it for `reverse` toggles the order
            is_reverse = self.state.sort_criteria[0][1]
        else:
            # Otherwise, start with ascending sort (not reversed)
            is_reverse = False

        self.state.records.sort(
            key=lambda r: normalize_for_sorting(
                r["validation"]["is_valid"]
                if column == "is_valid"
                else next(
                    (
                        r[key].get(column)
                        for key in ["afiliada", "piso", "facturacion", "bloque"]
                        if column in r.get(key, {})
                    ),
                    None,
                )
            ),
            reverse=is_reverse,
        )

        # Update sort criteria: True means ascending for icon display
        self.state.sort_criteria = [(column, not is_reverse)]
        self._render_all_panels()

    def _drop_record(self, record_to_drop: Dict):
        """Removes a record from the state and refreshes the UI."""
        self.state.records.remove(record_to_drop)
        self._render_all_panels()

    def _revalidate_record(self, record: Dict):
        """Re-validates a single record after an edit, and updates its UI elements."""
        afiliada_data = record.setdefault("afiliada", {})
        cif_value = afiliada_data.get("cif")
        if cif_value is not None:
            afiliada_data["cif"] = str(cif_value).strip().upper()
            cif_value = afiliada_data["cif"]

        is_valid_afiliada, err_afiliada = validator.validate_record(
            "afiliadas", record["afiliada"], "create"
        )
        is_valid_piso, err_piso = validator.validate_record(
            "pisos", record["piso"], "create"
        )
        is_valid_bloque, err_bloque = validator.validate_record(
            "bloques", record.setdefault("bloque", {}), "create"
        )
        is_valid_facturacion, err_facturacion = validator.validate_record(
            "facturacion", record["facturacion"], "create"
        )

        record.setdefault("validation", {}).setdefault("warnings", [])
        record["validation"].update(
            {
                "is_valid": is_valid_afiliada
                and is_valid_piso
                and is_valid_bloque
                and is_valid_facturacion,
                "errors": err_afiliada + err_piso + err_bloque + err_facturacion,
            }
        )

        if cif_value:
            cached_status = self.status_service.existing_afiliada_cifs.get(cif_value)
            if cached_status is None:
                self.status_service.mark_unknown_cif(cif_value)
                self._apply_duplicate_status(record, False, trigger_ui=False)
                self._schedule_background_task(
                    lambda: self._refresh_duplicate_status(record)
                )
            else:
                self._apply_duplicate_status(
                    record, bool(cached_status), trigger_ui=False
                )
        else:
            self._apply_duplicate_status(record, False, trigger_ui=False)

        direccion_value = (record.get("piso", {}).get("direccion") or "").strip()
        if direccion_value:
            key = normalize_address_key(direccion_value)
            cached_piso = self.status_service.existing_piso_addresses.get(key)
            if cached_piso is None:
                self.status_service.mark_unknown_address(direccion_value)
                self._apply_piso_existing_status(record, False, trigger_ui=False)
                self._schedule_background_task(
                    lambda: self._refresh_piso_status(record)
                )
            else:
                self._apply_piso_existing_status(
                    record, bool(cached_piso), trigger_ui=False
                )
        else:
            self._apply_piso_existing_status(record, False, trigger_ui=False)

        for updater in record.get("ui_updaters", {}).values():
            updater()
        self._update_import_button_state()

    async def _on_score_limit_change(self, new_limit: float):
        """Handles changes to the suggestion score threshold and triggers a refresh."""
        if new_limit is not None and abs(new_limit - self.bloque_score_limit) > 0.001:
            self.bloque_score_limit = new_limit
            await self._schedule_refresh()

    async def _schedule_refresh(self):
        """Schedules a debounced refresh of bloque suggestions."""
        if self._suggestion_task and not self._suggestion_task.done():
            self._suggestion_task.cancel()
        self._suggestion_task = asyncio.create_task(
            self._apply_batch_bloque_suggestions()
        )
        try:
            await self._suggestion_task
        finally:
            self._render_all_panels()

    async def _refresh_duplicate_status(self, record: Dict[str, Any]):
        """Check (or reuse cached) duplicate status for a single record after edits."""
        cif = str(record.get("afiliada", {}).get("cif", "")).strip().upper()
        if not cif:
            self._apply_duplicate_status(record, False)
            return

        exists = await self.status_service.ensure_afiliada_status(cif)
        self._apply_duplicate_status(record, exists)

    async def _refresh_piso_status(self, record: Dict[str, Any]):
        """Check whether a piso address already exists after user edits."""
        direccion = (record.get("piso", {}).get("direccion") or "").strip()
        if not direccion:
            self._apply_piso_existing_status(record, False)
            return

        exists = await self.status_service.ensure_piso_status(direccion)
        self._apply_piso_existing_status(record, exists)

    def _apply_duplicate_status(
        self, record: Dict[str, Any], exists: bool, *, trigger_ui: bool = True
    ):
        """Update a record with duplicate warning metadata and optionally refresh UI."""
        meta = record.setdefault("meta", {})
        meta["nif_exists"] = exists

        validation = record.setdefault("validation", {"is_valid": False, "errors": []})
        warnings = validation.setdefault("warnings", [])

        if exists and DUPLICATE_NIF_WARNING not in warnings:
            warnings.append(DUPLICATE_NIF_WARNING)
        if not exists and DUPLICATE_NIF_WARNING in warnings:
            warnings.remove(DUPLICATE_NIF_WARNING)

        if trigger_ui:
            for updater in record.get("ui_updaters", {}).values():
                try:
                    updater()
                except Exception:
                    pass

    def _apply_piso_existing_status(
        self, record: Dict[str, Any], exists: bool, *, trigger_ui: bool = True
    ):
        """Update piso metadata when the address already exists in the system."""
        meta = record.setdefault("meta", {})
        meta["piso_exists"] = exists

        if trigger_ui:
            for updater in record.get("ui_updaters", {}).values():
                try:
                    updater()
                except Exception:
                    pass

    def _snapshot_failed_record(
        self, record: Dict[str, Any], error_message: str
    ) -> Dict[str, Any]:
        """Create a serializable snapshot of a record that failed to import."""
        snapshot = {
            "afiliada": copy.deepcopy(record.get("afiliada", {})),
            "piso": copy.deepcopy(record.get("piso", {})),
            "bloque": copy.deepcopy(record.get("bloque", {})),
            "facturacion": copy.deepcopy(record.get("facturacion", {})),
            "meta": {
                "nif_exists": record.get("meta", {}).get("nif_exists"),
            },
            "validation": {
                "errors": list(record.get("validation", {}).get("errors", [])),
                "warnings": list(record.get("validation", {}).get("warnings", [])),
            },
            "error": error_message,
        }
        return snapshot

    def _prepare_failed_records_export(self) -> List[Dict[str, Any]]:
        """Flatten failed record snapshots into CSV-friendly dictionaries."""
        export_rows: List[Dict[str, Any]] = []
        for idx, snapshot in enumerate(self._failed_records, start=1):
            row: Dict[str, Any] = {"__index": idx}
            for section, fields in FAILED_EXPORT_FIELD_MAP.items():
                section_data = snapshot.get(section, {}) or {}
                for field in fields:
                    key = f"{section}_{field}"
                    value = section_data.get(field)
                    row[key] = "" if value is None else value

            meta_info = snapshot.get("meta", {}) or {}
            row["meta_nif_exists"] = "Sí" if meta_info.get("nif_exists") else "No"

            validation = snapshot.get("validation", {}) or {}
            row["validation_errors"] = "; ".join(validation.get("errors", []))
            row["warnings"] = "; ".join(validation.get("warnings", []))
            row["error"] = snapshot.get("error", "")
            export_rows.append(row)
        return export_rows

    def _get_failed_records_table_data(
        self,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Return columns and rows for the failed records preview table."""
        rows = self._prepare_failed_records_export()
        if not rows:
            return [], []

        columns: List[Dict[str, Any]] = [
            {"name": "__index", "label": "#", "field": "__index", "align": "left"}
        ]

        for section, fields in FAILED_EXPORT_FIELD_MAP.items():
            for field in fields:
                name = f"{section}_{field}"
                label = f"{section.title()} - {field.replace('_', ' ').title()}"
                columns.append({"name": name, "label": label, "field": name})

        columns.extend(
            [
                {
                    "name": "meta_nif_exists",
                    "label": "NIF Duplicado",
                    "field": "meta_nif_exists",
                },
                {
                    "name": "warnings",
                    "label": "Avisos",
                    "field": "warnings",
                },
                {
                    "name": "validation_errors",
                    "label": "Errores de Validación",
                    "field": "validation_errors",
                },
                {
                    "name": "error",
                    "label": "Error Importación",
                    "field": "error",
                },
            ]
        )

        normalized_rows = [
            {col["name"]: row.get(col["name"], "") for col in columns} for row in rows
        ]
        return columns, normalized_rows

    def _open_failed_records_preview(self):
        """Show a dialog with a table preview of failed imports."""
        if not self._failed_records:
            ui.notify("No hay registros fallidos para mostrar.", type="warning")
            return
        if not self._failed_preview_dialog or not self._failed_preview_container:
            ui.notify(
                "La vista de registros fallidos no está disponible en este momento.",
                type="negative",
            )
            return

        columns, rows = self._get_failed_records_table_data()
        if not rows:
            ui.notify("No hay registros fallidos para mostrar.", type="warning")
            return

        self._failed_preview_container.clear()
        with self._failed_preview_container:
            ui.label("Registros que no se importaron").classes("text-subtitle1")
            with ui.scroll_area().classes("w-full max-h-[60vh] border rounded"):
                ui.table(
                    columns=columns,
                    rows=rows,
                    row_key="__index",
                ).classes(
                    "w-full"
                ).props("dense")

        self._failed_preview_dialog.open()

    def _export_failed_records_csv(self):
        """Trigger a CSV download with the failed import records."""
        rows = self._prepare_failed_records_export()
        if not rows:
            ui.notify("No hay registros fallidos para exportar.", type="warning")
            return
        export_to_csv(rows, "afiliadas_import_fallidos.csv")

    def _export_import_log(self):
        """Download the latest import log as a text file."""
        if not self._last_import_log:
            ui.notify(
                "No hay registro de importación disponible para exportar.",
                type="warning",
            )
            return

        content = "\n".join(self._last_import_log)
        ui.download(content.encode("utf-8"), "afiliadas_import_log.txt")
        ui.notify("Registro de importación exportado.", type="positive")

    async def _apply_batch_bloque_suggestions(self):
        """Fetches bloque suggestions from the API and updates the records' state."""
        if not self.state.records:
            return

        addresses = [
            {"index": idx, "direccion": r["piso"]["direccion"]}
            for idx, r in enumerate(self.state.records)
            if r.get("piso", {}).get("direccion")
        ]
        if not addresses:
            return

        try:
            suggestions = await self.api.get_bloque_suggestions(
                addresses, self.bloque_score_limit
            )
            suggestion_map = {
                s["piso_id"]: s for s in suggestions if s.get("piso_id") is not None
            }

            for idx, record in enumerate(self.state.records):
                suggestion = suggestion_map.get(idx)
                meta = record.setdefault("meta", {})
                if suggestion and (
                    suggestion.get("suggested_bloque_id")
                    or suggestion.get("suggested_bloque_direccion")
                ):
                    meta["bloque"] = {
                        "id": suggestion.get("suggested_bloque_id"),
                        "direccion": suggestion.get("suggested_bloque_direccion"),
                    }
                    meta["bloque_score"] = suggestion.get("suggested_score")
                    # Preview should show the suggested bloque address for easier comparison
                    record.setdefault("bloque", {})["direccion"] = suggestion.get(
                        "suggested_bloque_direccion"
                    ) or record.get("bloque", {}).get("direccion")
                else:
                    meta["bloque"] = None
                    meta["bloque_score"] = None
                    # If not already linked, revert preview field to default derived from piso address
                    if record.get("piso", {}).get("bloque_id") is None:
                        record.setdefault("bloque", {})["direccion"] = short_address(
                            record.get("piso", {}).get("direccion", "")
                        )
                self._revalidate_record(record)
        except Exception as e:
            log.warning("Failed to get bloque suggestions", exc_info=True)
            ui.notify(
                f"No se pudieron obtener sugerencias de bloques: {e}", type="warning"
            )

    def _handle_bloque_assignment_change(self, record: Dict):
        """Handles manual changes to a bloque assignment."""
        self._schedule_background_task(
            lambda: self._hydrate_assigned_bloque(record)
        )
        self._revalidate_record(record)

    async def _hydrate_assigned_bloque(self, record: Dict):
        """Fetches full details for a manually assigned bloque ID."""
        bloque_id_str = record.get("piso", {}).get("bloque_id")
        bloque_id = int(bloque_id_str) if str(bloque_id_str).isdigit() else None
        record["piso"]["bloque_id"] = bloque_id  # Ensure it's stored as int or None

        if not bloque_id:
            record["meta"]["bloque_manual"] = None
            self._revalidate_record(record)
            return

        if bloque_id in self._bloque_details_cache:
            record["meta"]["bloque_manual"] = self._bloque_details_cache[bloque_id]
            self._revalidate_record(record)
            return

        try:
            bloques = await self.api.get_records("bloques", {"id": f"eq.{bloque_id}"})
            if bloques:
                self._bloque_details_cache[bloque_id] = bloques[0]
                record["meta"]["bloque_manual"] = bloques[0]
            else:
                record["meta"]["bloque_manual"] = None
        except Exception:
            record["meta"]["bloque_manual"] = None
        finally:
            self._revalidate_record(record)

    def _apply_suggested_bloque(self, record: Dict):
        """Applies the suggested bloque to the record."""
        suggestion = record.get("meta", {}).get("bloque")
        if suggestion and suggestion.get("id"):
            record["piso"]["bloque_id"] = suggestion["id"]
            # Mirror the suggested address into the preview field for comparison
            record.setdefault("bloque", {})["direccion"] = suggestion.get(
                "direccion"
            ) or record.get("bloque", {}).get("direccion")
            self._handle_bloque_assignment_change(record)
        else:
            ui.notify("No hay sugerencia disponible.", type="warning")

    def _clear_bloque_assignment(self, record: Dict):
        """Clears the manual bloque assignment."""
        record["piso"]["bloque_id"] = None
        # Also revert the preview field to baseline from piso address
        record.setdefault("bloque", {})["direccion"] = short_address(
            record.get("piso", {}).get("direccion", "")
        )
        self._handle_bloque_assignment_change(record)

    def _reset_bloques_entries(self):
        """Reset all bloque inputs to baseline: clear IDs and restore derived addresses."""
        if not self.state.records:
            return
        for record in self.state.records:
            record.setdefault("piso", {})["bloque_id"] = None
            record.setdefault("bloque", {})["direccion"] = short_address(
                record.get("piso", {}).get("direccion", "")
            )
            meta = record.setdefault("meta", {})
            meta["bloque_manual"] = None
            # Keep suggestions available; they will reappear as labels but not pre-fill
            self._revalidate_record(record)
        self._render_all_panels()

    async def _start_import(self):
        """
        Initiates the final, multi-step import process, creating records in the database
        in the correct order: bloques, pisos, afiliadas, facturacion.
        """
        if not self.all_records_valid:
            ui.notify(
                "Hay registros con errores. Por favor, corríjalos antes de importar.",
                type="negative",
            )
            return

        valid_records = self.state.records
        total = len(valid_records)
        success_count = 0
        failed_imports = []
        full_log = []
        newly_created_afiliadas = []
        self._failed_records = []
        self._last_import_log = []

        with ui.dialog() as progress_dialog, ui.card().classes("min-w-[700px]"):
            ui.label("Proceso de Importación").classes("text-h6")
            status_label = ui.label(f"Iniciando importación de {total} registros...")
            progress = ui.linear_progress(0).classes("w-full my-2")
            log_area = ui.log(max_lines=15).classes(
                "w-full h-64 bg-gray-100 p-2 rounded"
            )

        progress_dialog.open()

        def log_message(msg: str):
            log_area.push(msg)
            full_log.append(msg)

        for i, record in enumerate(valid_records):
            name = f"{record['afiliada']['nombre']} {record['afiliada']['apellidos']}".strip()
            status_label.set_text(f"Procesando {i + 1}/{total}: {name}...")

            try:
                # Step 1: Ensure Bloque exists
                bloque_id = record["piso"].get("bloque_id")
                bloque_direccion = record["bloque"].get("direccion")

                if bloque_id:
                    existing_bloques = await self.api.get_records(
                        "bloques", {"id": f"eq.{bloque_id}"}
                    )
                    if not existing_bloques:
                        raise ValueError(
                            f"El ID de bloque '{bloque_id}' proporcionado no existe."
                        )
                elif bloque_direccion:
                    existing_bloques = await self.api.get_records(
                        "bloques", {"direccion": f"eq.{bloque_direccion}"}
                    )
                    if existing_bloques:
                        bloque_id = existing_bloques[0]["id"]
                        log_message(
                            f"ℹ️ Bloque encontrado: {bloque_direccion} (ID: {bloque_id})"
                        )
                    else:
                        new_bloque, error = await self.api.create_record(
                            "bloques", {"direccion": bloque_direccion}
                        )
                        if error:
                            raise Exception(f"Error al crear bloque: {error}")
                        bloque_id = new_bloque["id"]
                        log_message(
                            f"➕ Bloque creado: {bloque_direccion} (ID: {bloque_id})"
                        )

                record["piso"]["bloque_id"] = bloque_id

                # Step 2: Ensure Piso exists
                piso_direccion = record["piso"]["direccion"]
                existing_pisos = await self.api.get_records(
                    "pisos", {"direccion": f"eq.{piso_direccion}"}
                )
                if existing_pisos:
                    piso_id = existing_pisos[0]["id"]
                    log_message(f"ℹ️ Piso encontrado: {piso_direccion} (ID: {piso_id})")
                else:
                    new_piso, error = await self.api.create_record(
                        "pisos", record["piso"]
                    )
                    if error:
                        raise Exception(f"Error al crear piso: {error}")
                    piso_id = new_piso["id"]
                    log_message(f"➕ Piso creado: {piso_direccion} (ID: {piso_id})")

                # Step 3: Create Afiliada
                record["afiliada"]["piso_id"] = piso_id
                new_afiliada, error = await self.api.create_record(
                    "afiliadas", record["afiliada"]
                )
                if error:
                    raise Exception(f"Error al crear afiliada: {error}")
                afiliada_id = new_afiliada["id"]
                newly_created_afiliadas.append(new_afiliada)
                log_message(
                    f"✅ Afiliada creada: {name} (ID: {afiliada_id}, Nº: {new_afiliada.get('num_afiliada')})"
                )

                # Step 4: Create Facturacion
                if (
                    record["facturacion"].get("iban")
                    or record["facturacion"].get("cuota", 0) > 0
                ):
                    record["facturacion"]["afiliada_id"] = afiliada_id
                    _, error = await self.api.create_record(
                        "facturacion", record["facturacion"]
                    )
                    if error:
                        log_message(f"⚠️ Aviso (Facturación): {name}: {error}")
                    else:
                        log_message(f"💰 Facturación añadida para {name}")

                success_count += 1
            except Exception as e:
                log.error(f"Failed to import record for {name}", exc_info=True)
                error_message = str(e)
                failed_imports.append({"afiliada": name, "error": error_message})
                self._failed_records.append(
                    self._snapshot_failed_record(record, error_message)
                )
                log_message(f"❌ ERROR al importar a {name}: {error_message}")

            progress.value = (i + 1) / total
            await asyncio.sleep(0.05)

        failure_count = len(failed_imports)
        summary_lines = [
            "",
            "Resumen final del proceso de importación",
            f"Total de registros procesados: {total}",
            f"Importaciones exitosas: {success_count}",
            f"Registros con errores: {failure_count}",
        ]

        if newly_created_afiliadas:
            summary_lines.append("Afiliadas creadas durante este proceso:")
            for afiliada in newly_created_afiliadas:
                nombre = afiliada.get("nombre", "").strip()
                apellidos = afiliada.get("apellidos", "").strip()
                summary_lines.append(
                    f" - {nombre} {apellidos} (ID: {afiliada.get('id')}, Nº: {afiliada.get('num_afiliada')})"
                )

        if failure_count:
            summary_lines.append(
                "Consulta la pestaña de fallidos para revisar y corregir los errores."
            )

        for line in summary_lines:
            log_message(line)

        self._last_import_log = list(full_log)

        progress_dialog.close()

        with ui.dialog() as summary_dialog, ui.card().classes(
            "w-[90vw] max-w-[1200px]"
        ):
            ui.label("Resultado de la Importación").classes("text-h6 mb-2")
            # Render sections stacked vertically instead of side-by-side
            with ui.column().classes("w-full gap-4"):
                # Summary box
                with ui.card().classes("w-full"):
                    if success_count > 0:
                        ui.markdown(
                            f"✅ **Se importaron {success_count} de {total} registros exitosamente.**"
                        ).classes("text-positive")
                    if failed_imports:
                        ui.markdown(
                            f"❌ **Fallaron {len(failed_imports)} de {total} registros.**"
                        ).classes("text-negative")

                # Errors box
                with ui.card().classes("w-full"):
                    ui.label("Errores").classes("text-subtitle2 mb-1")
                    if failed_imports:
                        ui.table(
                            columns=[
                                {
                                    "name": "afiliada",
                                    "label": "Afiliada",
                                    "field": "afiliada",
                                },
                                {"name": "error", "label": "Error", "field": "error"},
                            ],
                            rows=failed_imports,
                            row_key="afiliada",
                        ).classes("w-full")
                    else:
                        ui.label("Sin errores").classes("text-gray-500")

                # Full log box
                with ui.card().classes("w-full"):
                    ui.label("Registro Completo").classes("text-subtitle2 mb-1")
                    ui.textarea(value="\n".join(self._last_import_log)).props(
                        "readonly outlined"
                    ).classes("w-full h-[40vh]")
                    with ui.row().classes("w-full justify-end mt-2"):
                        ui.button(
                            "Exportar registro",
                            on_click=self._export_import_log,
                        ).props("color=secondary")

            if self._failed_records:
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button(
                        "Ver registros fallidos",
                        on_click=self._open_failed_records_preview,
                    ).props("color=warning")
                    ui.button(
                        "Exportar CSV fallidos",
                        on_click=self._export_failed_records_csv,
                    ).props("color=primary")

            ui.button("Cerrar", on_click=summary_dialog.close).classes("mt-4 self-end")

        summary_dialog.open()

        self.state.set_records([])
        self.status_service.reset()
        self._render_all_panels()
