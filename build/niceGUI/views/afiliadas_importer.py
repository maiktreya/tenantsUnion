# build/niceGUI/views/afiliadas_importer.py (Corrected for Sorting)

import pandas as pd
import io
import asyncio
import logging
import unicodedata
import re
from typing import Dict, Any, Optional

from nicegui import ui, events
from api.client import APIClient
from api.validate import validator
from state.app_state import GenericViewState
from components.importer_utils import transform_and_validate_row, short_address
from components.importer_panels import render_preview_tabs

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

    def _update_import_button_state(self):
        """Enables or disables the import button based on data validity."""
        if self.import_button:
            self.import_button.set_enabled(self.all_records_valid)

    def _normalize_for_sorting(self, value: Any) -> str:
        """Return a normalized string key for consistent sorting across types."""
        if value is None:
            return ""
        # Handle booleans explicitly to avoid mixing with strings
        if isinstance(value, bool):
            return "1" if value else "0"
        s = str(value).strip()
        # Numeric normalization: sort numerically while returning a string key
        if re.match(r"^-?(?:\d+\.?\d*|\.\d+)$", s):
            try:
                num = float(s)
                return f"{num:020.6f}"
            except (ValueError, TypeError):
                pass
        # Accent-insensitive, case-insensitive normalization for text
        normalized = unicodedata.normalize("NFD", s.lower())
        return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

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
            key=lambda r: self._normalize_for_sorting(
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

        record["validation"].update(
            {
                "is_valid": is_valid_afiliada
                and is_valid_piso
                and is_valid_bloque
                and is_valid_facturacion,
                "errors": err_afiliada + err_piso + err_bloque + err_facturacion,
            }
        )

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
        asyncio.create_task(self._hydrate_assigned_bloque(record))
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

        with ui.dialog() as progress_dialog, ui.card().classes("min-w-[700px]"):
            ui.label("Proceso de Importación").classes("text-h6")
            status_label = ui.label(f"Iniciando importación de {total} registros...")
            progress = ui.linear_progress(0).classes("w-full my-2")
            log_area = ui.log(max_lines=15).classes(
                "w-full h-64 bg-gray-100 p-2 rounded"
            )

        progress_dialog.open()

        for i, record in enumerate(valid_records):
            name = f"{record['afiliada']['nombre']} {record['afiliada']['apellidos']}".strip()
            status_label.set_text(f"Procesando {i + 1}/{total}: {name}...")

            def log_message(msg):
                log_area.push(msg)
                full_log.append(msg)

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
                failed_imports.append({"afiliada": name, "error": str(e)})
                log_message(f"❌ ERROR al importar a {name}: {e}")

            progress.value = (i + 1) / total
            await asyncio.sleep(0.05)

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
                    ui.textarea(value="\n".join(full_log)).props(
                        "readonly outlined"
                    ).classes("w-full h-[40vh]")

            ui.button("Cerrar", on_click=summary_dialog.close).classes("mt-4 self-end")

        summary_dialog.open()

        self.state.set_records([])
        self._render_all_panels()
