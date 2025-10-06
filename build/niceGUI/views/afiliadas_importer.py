# build/niceGUI/views/afiliadas_importer.py (Enhanced for Client-Side State)

import pandas as pd
import io
import asyncio
import logging
import copy
from typing import Dict, Any, Optional, List, Tuple, Callable, Awaitable
from dataclasses import dataclass, field
from nicegui import ui, events, app

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
from components.upload_event_utils import read_upload_event_bytes
from config import FAILED_EXPORT_FIELD_MAP, DUPLICATE_NIF_WARNING

log = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """A data class to hold the results of the import process."""

    total_records: int
    success_count: int = 0
    failed_imports: List[Dict] = field(default_factory=list)
    failed_snapshots: List[Dict] = field(default_factory=list)
    newly_created_afiliadas: List[Dict] = field(default_factory=list)
    log: List[str] = field(default_factory=list)


class AfiliadasImporterView:
    """
    A view to import 'afiliadas', with a clear separation between UI orchestration
    and pure, testable business logic methods, using per-tab client state.
    """

    def __init__(
        self, api_client: APIClient, state: Optional[GenericViewState] = None
    ):
        self.api = api_client

        if state is not None:
            self.state = state
        else:
            self.state = self._get_or_create_client_state()

        self.status_service = ImporterRecordStatusService(api_client)

        # UI-specific state and elements
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

        # Result holders, populated by logic methods and used by UI methods
        self._failed_records: List[Dict[str, Any]] = []
        self._last_import_log: List[str] = []

        # Dialogs are part of the view's UI responsibility
        self._failed_preview_dialog: Optional[ui.dialog] = None
        self._failed_preview_container: Optional[ui.column] = None

    def _get_or_create_client_state(self) -> GenericViewState:
        """Retrieve or initialize the per-client state."""
        storage = getattr(app, "storage", None)
        client_storage = getattr(storage, "client", None)
        if client_storage is None:
            return GenericViewState()
        if "afiliadas_importer_state" not in client_storage:
            client_storage["afiliadas_importer_state"] = GenericViewState()
        state = client_storage.get("afiliadas_importer_state")
        if isinstance(state, GenericViewState):
            return state
        new_state = GenericViewState()
        client_storage["afiliadas_importer_state"] = new_state
        return new_state

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
                    ui.label("Registros Fallidos").classes("text-h6")
                    self._failed_preview_container = ui.column().classes("w-full gap-2")
                    ui.button(
                        "Cerrar", on_click=self._failed_preview_dialog.close
                    ).classes("self-end mt-2")

        # If there are records in the state for this tab, render them.
        if self.state.records:
            self._render_all_panels()

        return container

    # ====================================================================
    # UI Orchestration Methods
    # ====================================================================

    async def _handle_upload(self, e: events.UploadEventArguments):
        """UI Orchestrator: Handles file upload, delegates processing, and updates UI."""
        self._failed_records = []
        try:
            csv_bytes = await read_upload_event_bytes(e)
            prepared_records = await self._prepare_records_from_csv(csv_bytes)
            self.state.set_records(prepared_records)
            self._render_all_panels()
            ui.notify(
                f"{len(prepared_records)} registros han sido procesados desde el archivo.",
                type="positive",
            )
        except Exception as ex:
            log.error("Error processing CSV file.", exc_info=True)
            ui.notify(f"Error al procesar el archivo: {ex}", type="negative")
            self.state.set_records([])
            self._render_all_panels()

    async def _start_import(self):
        """UI Orchestrator: Manages the import process UI flow."""
        if not self.all_records_valid:
            ui.notify(
                "Hay registros con errores. Por favor, corríjalos antes de importar.",
                type="negative",
            )
            return

        with ui.dialog() as progress_dialog, ui.card().classes("min-w-[700px]"):
            ui.label("Proceso de Importación").classes("text-h6")
            status_label = ui.label(
                f"Iniciando importación de {len(self.state.records)} registros..."
            )
            log_area = ui.log(max_lines=15).classes(
                "w-full h-64 bg-gray-100 p-2 rounded"
            )

        progress_dialog.open()

        def progress_callback(msg: str):
            current_status = msg.split("\n")[-1]
            status_label.set_text(current_status)
            log_area.push(current_status)

        import_result = await self._execute_import_logic(
            self.state.records, progress_callback
        )

        progress_dialog.close()

        self._failed_records = import_result.failed_snapshots
        self._last_import_log = import_result.log

        self._show_summary_dialog(import_result)

        self.state.set_records([])
        self._render_all_panels()

    def _show_summary_dialog(self, result: ImportResult):
        """UI Method: Displays a dialog summarizing the import result."""
        with ui.dialog() as summary_dialog, ui.card().classes(
            "w-[90vw] max-w-[1200px]"
        ):
            ui.label("Resultado de la Importación").classes("text-h6 mb-2")
            with ui.column().classes("w-full gap-4"):
                with ui.card().classes("w-full"):
                    if result.success_count > 0:
                        ui.markdown(
                            f"✅ **Se importaron {result.success_count} de {result.total_records} registros exitosamente.**"
                        ).classes("text-positive")
                    if result.failed_imports:
                        ui.markdown(
                            f"❌ **Fallaron {len(result.failed_imports)} de {result.total_records} registros.**"
                        ).classes("text-negative")

                with ui.card().classes("w-full"):
                    ui.label("Errores").classes("text-subtitle2 mb-1")
                    if result.failed_imports:
                        ui.table(
                            columns=[
                                {
                                    "name": "afiliada",
                                    "label": "Afiliada",
                                    "field": "afiliada",
                                },
                                {"name": "error", "label": "Error", "field": "error"},
                            ],
                            rows=result.failed_imports,
                            row_key="afiliada",
                        ).classes("w-full")
                    else:
                        ui.label("Sin errores.").classes("text-gray-500")

                with ui.card().classes("w-full"):
                    ui.label("Registro Completo").classes("text-subtitle2 mb-1")
                    ui.textarea(value="\n".join(result.log)).props(
                        "readonly outlined"
                    ).classes("w-full h-[40vh]")
                    with ui.row().classes("w-full justify-end mt-2"):
                        ui.button(
                            "Exportar registro", on_click=self._export_import_log
                        ).props("color=secondary")

            if self._failed_records:
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(
                        "Ver Registros Fallidos",
                        on_click=self._open_failed_records_preview,
                    ).props("color=warning")
                    ui.button(
                        "Exportar CSV de Fallidos",
                        on_click=self._export_failed_records_csv,
                    ).props("color=primary")

            ui.button("Cerrar", on_click=summary_dialog.close).classes("mt-4 self-end")
        summary_dialog.open()

    # ====================================================================

    def _open_failed_records_preview(self):
        """Open dialog listing failed records from the last import attempt."""
        if not self._failed_preview_dialog or not self._failed_preview_container:
            ui.notify(
                "La vista de registros fallidos no está disponible.", type="warning"
            )
            return

        if not self._failed_records:
            ui.notify("No hay registros fallidos para mostrar.", type="info")
            return

        columns, rows = self._get_failed_records_table_data()
        self._failed_preview_container.clear()

        with self._failed_preview_container:
            if not rows:
                ui.label("No hay registros fallidos para mostrar.").classes(
                    "text-gray-500"
                )
            else:
                ui.table(columns=columns, rows=rows, row_key="__index").classes(
                    "w-full"
                )

        self._failed_preview_dialog.open()

    # ====================================================================
    # Pure Business Logic Methods
    # ====================================================================

    async def _prepare_records_from_csv(self, csv_content: bytes) -> List[Dict]:
        """PURE LOGIC: Parses, validates, and enriches records from CSV content."""
        self.status_service.reset()
        self._bloque_details_cache.clear()

        content = csv_content.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(content), header=None, dtype=str).fillna("")
        records = [
            rec
            for _, row in df.iloc[1:].iterrows()
            if (rec := transform_and_validate_row(row)) is not None
        ]

        await self.status_service.preload_afiliada_cifs(records)
        await self.status_service.preload_piso_addresses(records)

        for record in records:
            self._sync_metadata_from_status_cache(record, trigger_ui=False)

        await self._apply_batch_bloque_suggestions(records)
        return records

    async def _execute_import_logic(
        self, records: List[Dict], progress_callback: Callable
    ) -> ImportResult:
        """PURE LOGIC: Executes the multi-step import and returns a detailed result."""
        result = ImportResult(total_records=len(records))

        for i, record in enumerate(records):
            name = f"{record['afiliada']['nombre']} {record['afiliada']['apellidos']}".strip()
            progress_callback(f"Procesando {i + 1}/{result.total_records}: {name}...")

            try:
                bloque_id = await self._ensure_bloque(record, result.log)
                record["piso"]["bloque_id"] = bloque_id

                piso_id = await self._ensure_piso(record, result.log)
                record["afiliada"]["piso_id"] = piso_id

                new_afiliada = await self._create_afiliada(record, result.log)
                result.newly_created_afiliadas.append(new_afiliada)

                await self._create_facturacion(record, new_afiliada["id"], result.log)

                result.success_count += 1
            except Exception as e:
                error_message = str(e)
                result.failed_imports.append({"afiliada": name, "error": error_message})
                result.failed_snapshots.append(
                    self._snapshot_failed_record(record, error_message)
                )
                result.log.append(f"❌ ERROR al importar a {name}: {error_message}")

            await asyncio.sleep(0.05)

        summary_lines = [
            f"\nResumen final del proceso de importación",
            f"Total de registros procesados: {result.total_records}",
            f"Importaciones exitosas: {result.success_count}",
            f"Registros con errores: {len(result.failed_imports)}",
        ]
        if result.newly_created_afiliadas:
            summary_lines.append("\nAfiliadas creadas durante este proceso:")
            for af in result.newly_created_afiliadas:
                summary_lines.append(
                    f" - {af.get('nombre')} {af.get('apellidos')} (ID: {af.get('id')}, Nº: {af.get('num_afiliada')})"
                )
        if result.failed_imports:
            summary_lines.append(
                "\nConsulta la pestaña de fallidos para revisar y corregir los errores."
            )

        result.log.extend(summary_lines)
        return result

    async def _ensure_bloque(self, record: Dict, log_list: List[str]) -> Optional[int]:
        bloque_id = record["piso"].get("bloque_id")
        bloque_direccion = record["bloque"].get("direccion")

        if bloque_id:
            if not await self.api.get_records("bloques", {"id": f"eq.{bloque_id}"}):
                raise ValueError(
                    f"El ID de bloque '{bloque_id}' proporcionado no existe."
                )
            return bloque_id

        if bloque_direccion:
            existing = await self.api.get_records(
                "bloques", {"direccion": f"eq.{bloque_direccion}"}
            )
            if existing:
                log_list.append(
                    f"ℹ️ Bloque encontrado: {bloque_direccion} (ID: {existing[0]['id']})"
                )
                return existing[0]["id"]

            new_bloque, error = await self.api.create_record(
                "bloques", {"direccion": bloque_direccion}
            )
            if error:
                raise Exception(f"Error al crear bloque: {error}")
            log_list.append(
                f"➕ Bloque creado: {bloque_direccion} (ID: {new_bloque['id']})"
            )
            return new_bloque["id"]
        return None

    async def _ensure_piso(self, record: Dict, log_list: List[str]) -> int:
        piso_direccion = record["piso"]["direccion"]
        existing = await self.api.get_records(
            "pisos", {"direccion": f"eq.{piso_direccion}"}
        )
        if existing:
            log_list.append(
                f"ℹ️ Piso encontrado: {piso_direccion} (ID: {existing[0]['id']})"
            )
            return existing[0]["id"]

        new_piso, error = await self.api.create_record("pisos", record["piso"])
        if error:
            raise Exception(f"Error al crear piso: {error}")
        log_list.append(f"➕ Piso creado: {piso_direccion} (ID: {new_piso['id']})")
        return new_piso["id"]

    async def _create_afiliada(self, record: Dict, log_list: List[str]) -> Dict:
        new_afiliada, error = await self.api.create_record(
            "afiliadas", record["afiliada"]
        )
        if error:
            raise Exception(f"Error al crear afiliada: {error}")
        name = f"{new_afiliada.get('nombre', '')} {new_afiliada.get('apellidos', '')}".strip()
        log_list.append(
            f"✅ Afiliada creada: {name} (ID: {new_afiliada['id']}, Nº: {new_afiliada.get('num_afiliada')})"
        )
        return new_afiliada

    async def _create_facturacion(
        self, record: Dict, afiliada_id: int, log_list: List[str]
    ):
        fact_data = record["facturacion"]
        if fact_data.get("iban") or fact_data.get("cuota", 0) > 0:
            fact_data["afiliada_id"] = afiliada_id
            _, error = await self.api.create_record("facturacion", fact_data)
            if error:
                log_list.append(f"⚠️ Aviso (Facturación): {error}")
            else:
                log_list.append(f"💰 Facturación añadida.")

    # ====================================================================
    # UI-Specific Helpers and Callbacks
    # ====================================================================

    @property
    def all_records_valid(self) -> bool:
        if not self.state.records:
            return False
        return all(
            r.get("validation", {}).get("is_valid", False) for r in self.state.records
        )

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
            get_bloque_score_limit=lambda: self.bloque_score_limit,
            on_reset_bloques=self._reset_bloques_entries,
        )
        self._update_import_button_state()

    def _update_import_button_state(self):
        if self.import_button:
            self.import_button.set_enabled(self.all_records_valid)

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
        self.state.sort_criteria = [(column, not is_reverse)]
        self._render_all_panels()

    def _drop_record(self, record_to_drop: Dict):
        self.state.records.remove(record_to_drop)
        self._render_all_panels()

    def _revalidate_record(self, record: Dict):
        afiliada_data, piso_data, bloque_data, facturacion_data = (
            record.get("afiliada", {}),
            record.get("piso", {}),
            record.get("bloque", {}),
            record.get("facturacion", {}),
        )

        if cif_val := afiliada_data.get("cif"):
            afiliada_data["cif"] = str(cif_val).strip().upper()

        is_valid_af, err_af = validator.validate_record(
            "afiliadas", afiliada_data, "create"
        )
        is_valid_p, err_p = validator.validate_record("pisos", piso_data, "create")
        is_valid_b, err_b = validator.validate_record("bloques", bloque_data, "create")
        is_valid_f, err_f = validator.validate_record(
            "facturacion", facturacion_data, "create"
        )

        validation = record.setdefault("validation", {})
        validation["is_valid"] = (
            is_valid_af and is_valid_p and is_valid_b and is_valid_f
        )
        validation["errors"] = err_af + err_p + err_b + err_f

        self._schedule_background_task(lambda: self._refresh_record_statuses(record))

        for updater in record.get("ui_updaters", {}).values():
            updater()
        self._update_import_button_state()

    async def _on_score_limit_change(self, new_limit: float):
        if new_limit is not None and abs(new_limit - self.bloque_score_limit) > 0.001:
            self.bloque_score_limit = new_limit
            await self._schedule_refresh()

    async def _schedule_refresh(self):
        if self._suggestion_task and not self._suggestion_task.done():
            self._suggestion_task.cancel()
            try:
                await self._suggestion_task
            except asyncio.CancelledError:
                pass

        async def refresh_task():
            await self._apply_batch_bloque_suggestions(self.state.records)
            self._render_all_panels()

        self._suggestion_task = asyncio.create_task(refresh_task())
        try:
            await self._suggestion_task
        except asyncio.CancelledError:
            pass
        finally:
            self._suggestion_task = None

    async def _refresh_record_statuses(self, record: Dict):
        cif = (record.get("afiliada", {}).get("cif") or "").strip().upper()
        if cif:
            self._apply_duplicate_status(
                record, await self.status_service.ensure_afiliada_status(cif)
            )

        direccion = (record.get("piso", {}).get("direccion") or "").strip()
        if direccion:
            self._apply_piso_existing_status(
                record, await self.status_service.ensure_piso_status(direccion)
            )

    def _apply_duplicate_status(
        self, record: Dict, exists: bool, *, trigger_ui: bool = True
    ):
        record.setdefault("meta", {})["nif_exists"] = exists
        warnings = record.setdefault("validation", {}).setdefault("warnings", [])
        if exists and DUPLICATE_NIF_WARNING not in warnings:
            warnings.append(DUPLICATE_NIF_WARNING)
        elif not exists and DUPLICATE_NIF_WARNING in warnings:
            warnings.remove(DUPLICATE_NIF_WARNING)
        if trigger_ui:
            for updater in record.get("ui_updaters", {}).values():
                updater()

    def _apply_piso_existing_status(
        self, record: Dict, exists: bool, *, trigger_ui: bool = True
    ):
        record.setdefault("meta", {})["piso_exists"] = exists
        if trigger_ui:
            for updater in record.get("ui_updaters", {}).values():
                updater()

    def _snapshot_failed_record(self, record: Dict, error_message: str) -> Dict:
        return {
            "afiliada": copy.deepcopy(record.get("afiliada")),
            "piso": copy.deepcopy(record.get("piso")),
            "bloque": copy.deepcopy(record.get("bloque")),
            "facturacion": copy.deepcopy(record.get("facturacion")),
            "meta": {"nif_exists": record.get("meta", {}).get("nif_exists")},
            "validation": {
                "errors": list(record.get("validation", {}).get("errors", [])),
                "warnings": list(record.get("validation", {}).get("warnings", [])),
            },
            "error": error_message,
        }

    def _prepare_failed_records_export(self) -> List[Dict[str, Any]]:
        rows = []
        for idx, snapshot in enumerate(self._failed_records, start=1):
            row = {"__index": idx}
            for section, fields in FAILED_EXPORT_FIELD_MAP.items():
                data = snapshot.get(section, {}) or {}
                for field in fields:
                    row[f"{section}_{field}"] = data.get(field, "")
            row.update(
                {
                    "meta_nif_exists": (
                        "Sí" if snapshot.get("meta", {}).get("nif_exists") else "No"
                    ),
                    "validation_errors": "; ".join(
                        snapshot.get("validation", {}).get("errors", [])
                    ),
                    "warnings": "; ".join(
                        snapshot.get("validation", {}).get("warnings", [])
                    ),
                    "error": snapshot.get("error", ""),
                }
            )
            rows.append(row)
        return rows

    def _get_failed_records_table_data(self) -> Tuple[List[Dict], List[Dict]]:
        rows = self._prepare_failed_records_export()
        if not rows:
            return [], []

        columns = [
            {"name": "__index", "label": "#", "field": "__index", "align": "left"}
        ]
        for section, fields in FAILED_EXPORT_FIELD_MAP.items():
            for field in fields:
                columns.append(
                    {
                        "name": f"{section}_{field}",
                        "label": f"{section.title()} - {field.replace('_', ' ').title()}",
                        "field": f"{section}_{field}",
                    }
                )
        columns.extend(
            [
                {
                    "name": "meta_nif_exists",
                    "label": "NIF Duplicado",
                    "field": "meta_nif_exists",
                },
                {"name": "warnings", "label": "Avisos", "field": "warnings"},
                {
                    "name": "validation_errors",
                    "label": "Errores de Validación",
                    "field": "validation_errors",
                },
                {"name": "error", "label": "Error Importación", "field": "error"},
            ]
        )
        return columns, [
            {col["name"]: row.get(col["name"], "") for col in columns} for row in rows
        ]

    def _export_failed_records_csv(self):
        rows = self._prepare_failed_records_export()
        if not rows:
            ui.notify("No hay registros fallidos para exportar.", type="warning")
            return
        export_to_csv(rows, "afiliadas_import_fallidos.csv")

    def _export_import_log(self):
        if not self._last_import_log:
            ui.notify(
                "No hay registro de importación disponible para exportar.",
                type="warning",
            )
            return
        ui.download(
            "\n".join(self._last_import_log).encode("utf-8"), "afiliadas_import_log.txt"
        )
        ui.notify("Registro de importación exportado.", type="positive")

    async def _apply_batch_bloque_suggestions(self, records: List[Dict]):
        if not records:
            return
        addresses = [
            {"index": idx, "direccion": r["piso"]["direccion"]}
            for idx, r in enumerate(records)
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
            for idx, record in enumerate(records):
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
                    record.setdefault("bloque", {})["direccion"] = suggestion.get(
                        "suggested_bloque_direccion"
                    ) or record.get("bloque", {}).get("direccion")
                else:
                    meta.update({"bloque": None, "bloque_score": None})
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
        self._schedule_background_task(lambda: self._hydrate_assigned_bloque(record))
        self._revalidate_record(record)

    async def _hydrate_assigned_bloque(self, record: Dict):
        bloque_id = (
            int(record.get("piso", {}).get("bloque_id"))
            if str(record.get("piso", {}).get("bloque_id")).isdigit()
            else None
        )
        record["piso"]["bloque_id"] = bloque_id
        if not bloque_id:
            record["meta"]["bloque_manual"] = None
        elif bloque_id in self._bloque_details_cache:
            record["meta"]["bloque_manual"] = self._bloque_details_cache[bloque_id]
        else:
            bloques = await self.api.get_records("bloques", {"id": f"eq.{bloque_id}"})
            record["meta"]["bloque_manual"] = self._bloque_details_cache[bloque_id] = (
                bloques[0] if bloques else None
            )
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
            try:
                asyncio.run(coro_factory())
            except Exception:
                log.exception("Background task failed.")

    def _sync_metadata_from_status_cache(
        self, record: Dict, *, trigger_ui: bool = True
    ):
        afiliada_cif = (record.get("afiliada", {}).get("cif") or "").strip().upper()
        exists_afiliada = bool(
            afiliada_cif
            and self.status_service.existing_afiliada_cifs.get(afiliada_cif)
        )
        self._apply_duplicate_status(record, exists_afiliada, trigger_ui=trigger_ui)

        direccion = (record.get("piso", {}).get("direccion") or "").strip()
        key = normalize_address_key(direccion)
        exists_piso = bool(self.status_service.existing_piso_addresses.get(key))
        self._apply_piso_existing_status(record, exists_piso, trigger_ui=trigger_ui)
