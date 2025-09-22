import pandas as pd
import io
import re
import asyncio
import unicodedata
import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from nicegui import ui, events

from api.client import APIClient
from api.validate import validator
from state.app_state import GenericViewState
from config import IMPORTER_HEADER_MAP


log = logging.getLogger(__name__)


class AfiliadasImporterView:
    """A view to import 'afiliadas' using a shared state slice."""

    # --- THIS IS THE FIX ---
    # The __init__ method now correctly accepts the state object.
    def __init__(self, api_client: APIClient, state: GenericViewState):
        self.api = api_client
        self.state = state  # Use the passed-in state slice
        self.afiliadas_panel: Optional[ui.column] = None
        self.pisos_panel: Optional[ui.column] = None
        self.facturacion_panel: Optional[ui.column] = None
        self.bloques_panel: Optional[ui.column] = None
        self.import_button: Optional[ui.button] = None
        self._bloque_details_cache: Dict[int, Dict[str, Any]] = {}
        self.bloque_score_limit: float = 0.88
        self._suggestion_task: Optional[asyncio.Task] = None

    # ... (The rest of the file remains the same as the last feature-complete version) ...
    def create(self) -> ui.column:
        """Create the UI for the CSV importer view."""
        container = ui.column().classes("w-full p-4 gap-4")
        with container:
            ui.label("Importar Nuevas Afiliadas desde CSV").classes(
                "text-h6 font-italic"
            )
            ui.markdown(
                "Sube un archivo CSV. Los datos se validarán y se mostrarán en pestañas."
            )
            with ui.row().classes("w-full gap-4 items-center"):
                ui.upload(
                    on_upload=self._handle_upload,
                    auto_upload=True,
                    label="Subir archivo",
                ).props('accept=".csv"')
                self.import_button = ui.button(
                    "Iniciar Importación", icon="upload", on_click=self._start_import
                ).props("color=orange-600")
            ui.separator().classes("mt-4")
            with ui.tabs().props('align="left"') as tabs:
                ui.tab("afiliadas", label="Afiliadas")
                ui.tab("pisos", label="Pisos")
                ui.tab("bloques", label="Bloques")
                ui.tab("facturacion", label="Facturación")
            with ui.tab_panels(tabs, value="afiliadas").classes(
                "w-full border rounded-md"
            ):
                with ui.tab_panel("afiliadas"):
                    self.afiliadas_panel = ui.column().classes("w-full")
                with ui.tab_panel("pisos"):
                    self.pisos_panel = ui.column().classes("w-full")
                with ui.tab_panel("bloques"):
                    self.bloques_panel = ui.column().classes("w-full")
                with ui.tab_panel("facturacion"):
                    self.facturacion_panel = ui.column().classes("w-full")
        return container

    # Helper: reduce an address to street + number (first two comma-separated chunks)
    def _short_address(self, address: Optional[str]) -> str:
        if not address:
            return ""
        parts = [p.strip() for p in str(address).split(",") if p is not None]
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return f"{parts[0]}, {parts[1]}"

    # Helper: safe nested get from dicts
    def _get_in(self, data: Dict[str, Any], path: List[str], default: Any = None) -> Any:
        cur: Any = data
        try:
            for key in path:
                if not isinstance(cur, dict):
                    return default
                cur = cur.get(key)
                if cur is None and key != path[-1]:
                    return default
            return cur if cur is not None else default
        except Exception:
            return default

    # Helper: register an updater that syncs a UI input from a record path
    def _register_input_updater(
        self,
        record: Dict[str, Any],
        path: List[str],
        component: Any,
        updater_key: str,
    ) -> None:
        def updater(rec=record, comp=component, p=path):
            val = self._get_in(rec, p, "")
            comp.set_value("" if val in (None, "") else str(val))

        record.setdefault("ui_updaters", {})[updater_key] = updater
        updater()

    async def _handle_upload(self, e: events.UploadEventArguments):
        """Handle the file upload, parse, validate, and render the editable tabs."""
        try:
            content = e.content.read()
            decoded_content = content.decode("utf-8-sig")
            df = pd.read_csv(
                io.StringIO(decoded_content),
                header=None,
                quotechar='"',
                sep=",",
                dtype=str,
            ).fillna("")
            records = [
                rec
                for _, row in df.iloc[1:].iterrows()
                if (rec := self._transform_and_validate_row(row)) is not None
            ]
            self._bloque_details_cache.clear()
            self.state.set_records(records)
            await self._apply_batch_bloque_suggestions(self.state.records)
            self._render_preview_tabs()
            ui.notify("Archivo procesado.", type="positive")
        except Exception as ex:
            ui.notify(f"Error al procesar el archivo: {ex}", type="negative")
            self.state.set_records([])
            self._render_preview_tabs()

    def _transform_and_validate_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        def _parse_date(date_str: str) -> Optional[str]:
            if not date_str:
                return None
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt).date().isoformat()
                except (ValueError, TypeError):
                    continue
            return None

        try:
            get_val = lambda index: row.get(index, "").strip()
            nombre = get_val(0).strip('<>"')
            if not nombre:
                return None
            full_address = ", ".join(
                filter(
                    None,
                    [
                        get_val(9),
                        get_val(10),
                        get_val(11),
                        get_val(12),
                        get_val(14),
                        get_val(13),
                    ],
                )
            )
            final_address = re.sub(r"\s*,\s*", ", ", full_address).strip(" ,")
            afiliada_data = {
                "nombre": nombre,
                "apellidos": f"{get_val(2)} {get_val(3)}".strip(),
                "genero": get_val(4),
                "fecha_nac": _parse_date(get_val(5)),
                "cif": get_val(6),
                "telefono": get_val(7),
                "email": get_val(8),
                "fecha_alta": date.today().isoformat(),
                "regimen": get_val(17),
                "estado": "Alta",
                "piso_id": None,
            }
            piso_data = {
                "direccion": final_address,
                "municipio": get_val(13),
                "cp": int(get_val(14)) if get_val(14).isdigit() else None,
                "n_personas": int(get_val(15)) if get_val(15).isdigit() else None,
                "inmobiliaria": get_val(18),
                "propiedad": get_val(20),
                "prop_vertical": get_val(21),
                "fecha_firma": _parse_date(get_val(16)),
                "bloque_id": None,
            }
            bloque_data = {"direccion": self._short_address(final_address)}
            cuota_str = get_val(23) or get_val(24) or get_val(25)
            cuota_match = re.search(r"(\d+[\.,]?\d*)\s*€\s*(mes|año)", cuota_str)
            iban_raw = get_val(26).replace(" ", "")
            facturacion_data = {
                "cuota": (
                    float(cuota_match.group(1).replace(",", "."))
                    if cuota_match
                    else 0.0
                ),
                "periodicidad": (
                    12 if cuota_match and cuota_match.group(2) == "año" else 1
                ),
                "forma_pago": "Domiciliación" if iban_raw else "Otro",
                "iban": iban_raw.upper() if iban_raw else None,
                "afiliada_id": None,
            }
            is_valid_afiliada, errors_afiliada = validator.validate_record(
                "afiliadas", afiliada_data, "create"
            )
            is_valid_piso, errors_piso = validator.validate_record(
                "pisos", piso_data, "create"
            )
            is_valid_bloque, errors_bloque = validator.validate_record(
                "bloques", bloque_data, "create"
            )
            is_valid_facturacion, errors_facturacion = validator.validate_record(
                "facturacion", facturacion_data, "create"
            )
            return {
                "piso": piso_data,
                "bloque": bloque_data,
                "afiliada": afiliada_data,
                "facturacion": facturacion_data,
                "validation": {
                    "is_valid": is_valid_afiliada
                    and is_valid_piso
                    and is_valid_bloque
                    and is_valid_facturacion,
                    "errors": errors_afiliada
                    + errors_piso
                    + errors_bloque
                    + errors_facturacion,
                },
                "meta": {"bloque": None, "bloque_manual": None},
            }
        except Exception:
            return None

    async def _apply_batch_bloque_suggestions(
        self, records: List[Dict[str, Any]]
    ):
        if not records:
            return

        addresses = []
        for idx, record in enumerate(records):
            direccion = (record.get("piso") or {}).get("direccion", "").strip()
            meta = record.setdefault("meta", {})
            if "bloque_manual" not in meta:
                meta["bloque_manual"] = None
            record.setdefault("bloque", {}).setdefault(
                "direccion",
                self._short_address(direccion)
                or record.get("bloque", {}).get("direccion"),
            )
            if direccion:
                addresses.append({"index": idx, "direccion": direccion})
            else:
                meta["bloque"] = None
                meta["bloque_score"] = None

        if not addresses:
            return

        try:
            suggestions = await self.api.get_bloque_suggestions(
                addresses, self.bloque_score_limit
            )
        except Exception as exc:
            log.error("No se pudieron obtener sugerencias de bloques", exc_info=True)
            ui.notify(
                f"No se pudieron obtener sugerencias de bloques: {exc}",
                type="warning",
            )
            suggestions = []

        suggestion_map: Dict[int, Dict[str, Any]] = {}
        for entry in suggestions or []:
            try:
                key = entry.get("piso_id")
                if key is None:
                    continue
                suggestion_map[int(key)] = entry
            except (ValueError, TypeError):
                continue

        for idx, record in enumerate(records):
            suggestion = suggestion_map.get(idx)
            meta = record.setdefault("meta", {})
            meta.setdefault("record_index", idx)
            manual_info = meta.get("bloque_manual")
            manual_id = manual_info.get("id") if isinstance(manual_info, dict) else None
            if suggestion and suggestion.get("suggested_bloque_id"):
                meta["bloque"] = {
                    "id": suggestion["suggested_bloque_id"],
                    "direccion": suggestion.get("suggested_bloque_direccion"),
                    "score": suggestion.get("suggested_score"),
                }
                meta["bloque_score"] = suggestion.get("suggested_score")
                if suggestion.get("suggested_bloque_direccion"):
                    record.setdefault("bloque", {})[
                        "direccion"
                    ] = suggestion["suggested_bloque_direccion"]
                if manual_id is None or manual_id == suggestion["suggested_bloque_id"]:
                    record["piso"]["bloque_id"] = suggestion["suggested_bloque_id"]
            else:
                meta["bloque"] = None
                meta["bloque_score"] = None
                if manual_id is None:
                    record["piso"]["bloque_id"] = None
                    # Provide a sensible default for editable bloque direccion
                    piso_dir = (record.get("piso") or {}).get("direccion", "")
                    record.setdefault("bloque", {})["direccion"] = self._short_address(
                        piso_dir
                    )
            self._revalidate_record(record)

    async def _fetch_bloque_details(self, bloque_id: int) -> Optional[Dict[str, Any]]:
        if bloque_id in self._bloque_details_cache:
            return self._bloque_details_cache[bloque_id]

        records = await self.api.get_records(
            "bloques", {"id": f"eq.{bloque_id}"}, limit=1
        )
        bloque = records[0] if records else None
        if bloque:
            self._bloque_details_cache[bloque_id] = bloque
        return bloque

    def _on_bloque_input_change(
        self, _event: events.GenericEventArguments, record: Dict[str, Any]
    ):
        self._handle_bloque_assignment_change(record)

    def _render_preview_tabs(self):
        self._render_panel(
            "afiliada",
            self.afiliadas_panel,
            [
                "nombre",
                "apellidos",
                "cif",
                "email",
                "telefono",
                "fecha_nac",
            ],
        )
        self._render_panel(
            "piso",
            self.pisos_panel,
            [
                "direccion",
                "municipio",
                "cp",
                "bloque_id",
                "n_personas",
                "inmobiliaria",
                "prop_vertical",
                "fecha_firma",
            ],
        )
        self._render_panel(
            "facturacion",
            self.facturacion_panel,
            ["cuota", "periodicidad", "forma_pago", "iban"],
        )
        self._render_bloques_panel()
        self._update_import_button_state()

    def _render_bloques_panel(self):
        if not self.bloques_panel:
            return
        self.bloques_panel.clear()
        with self.bloques_panel, ui.scroll_area().classes("w-full h-[32rem]"):
            if not self.state.records:
                ui.label("Sin registros cargados.").classes("text-sm text-gray-500")
                return
            self._render_bloques_toolbar()
            self._render_bloques_header()
            for record in self.state.records:
                self._render_bloques_row(record)

    def _render_bloques_toolbar(self):
        with ui.row().classes(
            "w-full items-center gap-2 p-2 bg-white/90 sticky top-0 z-20 border-b"
        ):
            ui.label("Umbral de coincidencia (0-1)").classes(
                "text-xs uppercase tracking-wide text-gray-500"
            )
            slider = ui.slider(min=0.0, max=1.0, step=0.01, value=self.bloque_score_limit).classes(
                "flex-1"
            )
            def on_slider_change(e: events.GenericEventArguments):
                raw = getattr(e, "value", None)
                if raw is None:
                    args = getattr(e, "args", None)
                    if isinstance(args, dict):
                        raw = args.get("value")
                    elif isinstance(args, (list, tuple)) and args:
                        raw = args[0]
                if raw is None and hasattr(e, "sender"):
                    raw = getattr(e.sender, "value", None)
                asyncio.create_task(self._on_score_limit_change(raw))
            slider.on("change", on_slider_change)
            ui.label(f"{self.bloque_score_limit:.2f}").classes("text-xs font-mono text-gray-600").bind_text_from(
                slider,
                "value",
                lambda v: (
                    f"{float(v):.2f}"
                    if isinstance(v, (int, float, str)) and str(v).strip() != ""
                    else (
                        f"{float(v.get('value', 0)):.2f}" if isinstance(v, dict) and v.get("value") is not None else "0.00"
                    )
                ),
            )
            ui.button(
                "Recalcular sugerencias",
                icon="refresh",
                on_click=lambda: asyncio.create_task(self._schedule_refresh()),
            ).props("size=sm outline")

    def _render_bloques_header(self):
        with ui.row().classes(
            "w-full font-bold text-gray-600 gap-2 p-2 bg-gray-50 items-center no-wrap sticky top-[3.2rem] z-10"
        ):
            ui.label("Acciones").classes("w-16 min-w-[4rem]")
            ui.label("Estado").classes("w-24 min-w-[6rem]")
            ui.label("Dirección piso").classes("w-48 min-w-[12rem]")
            ui.label("Dirección bloque").classes("flex-grow min-w-[18rem]")
            ui.label("ID bloque").classes("w-36 min-w-[9rem]")
            ui.label("Sugerencia").classes("flex-grow min-w-[18rem]")
            ui.label("Situación").classes("w-40 min-w-[10rem]")

    def _render_bloques_row(self, record: Dict[str, Any]):
        record.setdefault("ui_updaters", {})
        with ui.row().classes("w-full items-start gap-2 p-2 border-t no-wrap") as row:
            def update_row_style(r=row, rec=record):
                r.classes(
                    remove="bg-red-100 bg-green-50",
                    add=("bg-green-50" if rec["validation"]["is_valid"] else "bg-red-100"),
                ).tooltip(
                    "\n".join(rec["validation"]["errors"]) if not rec["validation"]["is_valid"] else "Válido"
                )
            record["ui_updaters"]["bloques_row"] = update_row_style

            with ui.column().classes("w-16 min-w-[4rem] items-center"):
                ui.button(icon="delete", on_click=lambda r=record: self._drop_record(r)).props(
                    "size=sm flat dense color=negative"
                )

            with ui.column().classes("w-24 min-w-[6rem] items-center"):
                status_icon = ui.icon("placeholder")
                def update_status_icon(rec=record, ic=status_icon):
                    is_valid = rec["validation"]["is_valid"]
                    ic.name = "check_circle" if is_valid else "cancel"
                    ic.classes(remove="text-green-500 text-red-500", add="text-green-500" if is_valid else "text-red-500")
                record["ui_updaters"]["bloques_status_icon"] = update_status_icon
                update_status_icon()

            ui.label(record.get("piso", {}).get("direccion", "")).classes("w-48 min-w-[12rem] text-sm")

            with ui.column().classes("flex-grow min-w-[18rem] gap-1"):
                bloque_dir_input = ui.input(
                    value=record.setdefault("bloque", {}).get(
                        "direccion", record["piso"].get("direccion", "")
                    ),
                    placeholder="Dirección del bloque",
                ).classes("w-full").props("type=text").bind_value(
                    record.setdefault("bloque", {}), "direccion"
                )
                bloque_dir_input.on(
                    "change", lambda _e=None, r=record: self._revalidate_record(r)
                )
                self._register_input_updater(
                    record, ["bloque", "direccion"], bloque_dir_input, "bloques_dir_input"
                )

            with ui.column().classes("w-36 min-w-[9rem] items-start gap-1"):
                bloque_input = ui.input(
                    value=(
                        "" if record["piso"].get("bloque_id") is None else str(record["piso"].get("bloque_id"))
                    )
                ).classes("w-full").props('type=number placeholder="ID de bloque"').bind_value(
                    record["piso"], "bloque_id"
                )
                bloque_input.on(
                    "change", lambda e, r=record: self._on_bloque_input_change(e, r)
                )
                self._register_input_updater(
                    record, ["piso", "bloque_id"], bloque_input, "bloques_input"
                )
                with ui.row().classes("gap-1"):
                    apply_button = ui.button("Usar sugerencia", icon="lightbulb", on_click=lambda _=None, r=record: self._apply_suggested_bloque(r)).props("size=sm flat")
                    clear_button = ui.button("Limpiar", icon="backspace", on_click=lambda _=None, r=record: self._clear_bloque_assignment(r)).props("size=sm flat")

            with ui.column().classes("flex-grow min-w-[18rem] gap-1"):
                suggestion_label = ui.label().classes("text-xs text-gray-500")

            with ui.column().classes("w-40 min-w-[10rem]"):
                estado_label = ui.label().classes("text-xs font-medium")

            def update_bloque_labels(
                rec=record,
                suggestion=suggestion_label,
                estado=estado_label,
                apply_btn=apply_button,
                clear_btn=clear_button,
            ):
                meta_info = rec.get("meta", {})
                assigned_id = rec.get("piso", {}).get("bloque_id")
                suggested = meta_info.get("bloque")
                assigned_info = meta_info.get("bloque_manual")
                if assigned_info and assigned_info.get("id") != assigned_id:
                    assigned_info = None
                bloque_dir = rec.setdefault("bloque", {}).get("direccion", "Sin dirección")
                suggested_text = (
                    f"ID {suggested.get('id')} · {suggested.get('direccion')}" if suggested else f"Sin sugerencia · {bloque_dir}"
                )
                if suggested and suggested.get("score") is not None:
                    try:
                        suggested_text += f" ({float(suggested['score']) * 100:.1f}%)"
                    except (TypeError, ValueError):
                        pass
                suggestion.set_text(f"Sugerencia: {suggested_text}")
                estado_color = "text-amber-600"
                if assigned_id:
                    assigned_dir = ((assigned_info or suggested or {}).get("direccion"))
                    estado_text = f"Asignado: {assigned_id}" + (f" · {assigned_dir}" if assigned_dir else "")
                    score_hint = None
                    if assigned_info and assigned_info.get("score") is not None:
                        score_hint = assigned_info.get("score")
                    elif suggested and assigned_id == suggested.get("id") and suggested.get("score") is not None:
                        score_hint = suggested.get("score")
                    if score_hint is not None:
                        try:
                            estado_text += f" ({float(score_hint) * 100:.1f}%)"
                        except (TypeError, ValueError):
                            pass
                    if suggested and assigned_id == suggested.get("id"):
                        estado_text += " (sugerencia aplicada)"
                        estado_color = "text-green-600"
                    else:
                        estado_text += " (manual)"
                else:
                    estado_text = "Pendiente de asignar" if suggested else f"Sin bloque asignado · {bloque_dir}"
                    estado_color = ("text-amber-600" if suggested else "text-red-600")
                estado.set_text(estado_text)
                estado.classes(
                    remove="text-green-600 text-amber-600 text-red-600", add=estado_color
                )
                # Run the registered input updaters (ID and dirección)
                rec.get("ui_updaters", {}).get("bloques_input", lambda: None)()
                rec.get("ui_updaters", {}).get("bloques_dir_input", lambda: None)()
                if suggested and assigned_id != suggested.get("id"):
                    apply_btn.enable()
                else:
                    apply_btn.disable()
                if assigned_id is not None:
                    clear_btn.enable()
                else:
                    clear_btn.disable()
            record["ui_updaters"]["bloques_labels"] = update_bloque_labels
            update_bloque_labels(); update_row_style()

    def _handle_bloque_assignment_change(self, record: Dict[str, Any]):
        try:
            self._revalidate_record(record)
            bloque_id = record.get("piso", {}).get("bloque_id")
            if bloque_id:
                asyncio.create_task(
                    self._hydrate_assigned_bloque(record, bloque_id)
                )
            else:
                record.setdefault("meta", {})["bloque_manual"] = None
        finally:
            updater = record.get("ui_updaters", {}).get("bloques_labels")
            if updater:
                updater()

    def _apply_suggested_bloque(self, record: Dict[str, Any]):
        suggested = record.get("meta", {}).get("bloque")
        suggested_id = (suggested or {}).get("id")
        if not suggested_id:
            ui.notify("No hay sugerencia disponible para este registro.", "warning")
            return
        record.setdefault("meta", {})["bloque_manual"] = suggested
        record.setdefault("piso", {})["bloque_id"] = suggested_id
        if suggested.get("direccion"):
            record.setdefault("bloque", {})["direccion"] = suggested["direccion"]
        self._handle_bloque_assignment_change(record)

    def _clear_bloque_assignment(self, record: Dict[str, Any]):
        record.setdefault("piso", {})["bloque_id"] = None
        record.setdefault("meta", {})["bloque_manual"] = None
        self._handle_bloque_assignment_change(record)

    async def _hydrate_assigned_bloque(
        self, record: Dict[str, Any], bloque_id: int
    ):
        meta = record.setdefault("meta", {})
        suggested = meta.get("bloque")
        if suggested and suggested.get("id") == bloque_id:
            meta["bloque_manual"] = suggested
            return
        try:
            bloque_info = await self._fetch_bloque_details(bloque_id)
            if bloque_info:
                meta["bloque_manual"] = {**bloque_info, "score": None}
            else:
                meta["bloque_manual"] = None
        except asyncio.CancelledError:
            raise
        except Exception:
            return
        updater = record.get("ui_updaters", {}).get("bloques_labels")
        if updater:
            updater()

    def _render_panel(self, data_key: str, panel: ui.column, fields: List[str]):
        if not panel:
            return
        panel.clear()
        with panel, ui.scroll_area().classes("w-full h-[32rem]"):
            with ui.row().classes(
                "w-full font-bold text-gray-600 gap-2 p-2 bg-gray-50 items-center no-wrap sticky top-0 z-10"
            ):
                ui.label("Acciones").classes("w-16 min-w-[4rem]")
                with ui.row().classes(
                    "w-24 min-w-[6rem] items-center cursor-pointer"
                ).on("click", lambda: self._sort_by_column("is_valid")):
                    ui.label("Estado")
                    sort_info = next(
                        (c for c in self.state.sort_criteria if c[0] == "is_valid"),
                        None,
                    )
                    if sort_info:
                        ui.icon(
                            "arrow_upward" if sort_info[1] else "arrow_downward",
                            size="sm",
                        )
                ui.label("Afiliada").classes("w-48 min-w-[12rem]")
                for field in fields:
                    width = (
                        "flex-grow min-w-[15rem]"
                        if field in ["email", "direccion", "iban"]
                        else "w-32 min-w-[8rem]"
                    )
                    with ui.row().classes(f"{width} items-center cursor-pointer").on(
                        "click", lambda f=field: self._sort_by_column(f)
                    ):
                        ui.label(IMPORTER_HEADER_MAP.get(field, field.title()))
                        sort_info = next(
                            (c for c in self.state.sort_criteria if c[0] == field), None
                        )
                        if sort_info:
                            ui.icon(
                                "arrow_upward" if sort_info[1] else "arrow_downward",
                                size="sm",
                            )
            for record in self.state.records:
                record.setdefault("ui_updaters", {})
                with ui.row().classes(
                    "w-full items-center gap-2 p-2 border-t no-wrap"
                ) as row:

                    def update_row_style(r=row, rec=record):
                        r.classes(
                            remove="bg-red-100 bg-green-50",
                            add=(
                                "bg-green-50"
                                if rec["validation"]["is_valid"]
                                else "bg-red-100"
                            ),
                        ).tooltip(
                            "\n".join(rec["validation"]["errors"])
                            if not rec["validation"]["is_valid"]
                            else "Válido"
                        )

                    record["ui_updaters"][data_key] = update_row_style
                    with ui.column().classes("w-16 min-w-[4rem] items-center"):
                        ui.button(
                            icon="delete",
                            on_click=lambda r=record: self._drop_record(r),
                        ).props("size=sm flat dense color=negative")
                    with ui.column().classes("w-24 min-w-[6rem] items-center"):
                        status_icon = ui.icon("placeholder")

                        def update_status_icon(rec=record, ic=status_icon):
                            is_valid = rec["validation"]["is_valid"]
                            ic.name = "check_circle" if is_valid else "cancel"
                            ic.classes(
                                remove="text-green-500 text-red-500",
                                add="text-green-500" if is_valid else "text-red-500",
                            )

                        record["ui_updaters"][
                            f"status_icon_{data_key}"
                        ] = update_status_icon
                        update_status_icon()
                    ui.label(
                        f"{record['afiliada']['nombre']} {record['afiliada']['apellidos']}"
                    ).classes("w-48 min-w-[12rem] text-sm")
                    for field in fields:
                        width = (
                            "flex-grow min-w-[15rem]"
                            if field in ["email", "direccion", "iban"]
                            else "w-32 min-w-[8rem]"
                        )
                        if field == "bloque_id":
                            with ui.column().classes(f"{width} items-start gap-1"):
                                bloque_input = (
                                    ui.input(
                                        value=
                                        (
                                            ""
                                            if record[data_key].get(field) in (None, "")
                                            else str(record[data_key].get(field))
                                        )
                                    )
                                    .classes("w-full")
                                    .props('type=number placeholder="ID de bloque"')
                                    .bind_value(record[data_key], field)
                                )
                                if data_key == "piso":
                                    bloque_input.on(
                                        "change",
                                        lambda e, r=record: self._on_bloque_input_change(
                                            e, r
                                        ),
                                    )
                                else:
                                    bloque_input.on(
                                        "change",
                                        lambda _e, r=record: self._revalidate_record(r),
                                    )

                                hint_label = ui.label("").classes(
                                    "text-xs text-gray-500"
                                )

                                def update_input(
                                    rec=record,
                                    inp=bloque_input,
                                    label=hint_label,
                                ):
                                    value = rec.get(data_key, {}).get(field)
                                    inp.set_value("" if value in (None, "") else str(value))
                                    meta_info = rec.get("meta", {})
                                    assigned = meta_info.get("bloque_manual")
                                    suggested = meta_info.get("bloque")
                                    assigned_id = rec.get("piso", {}).get("bloque_id")
                                    label_info = None
                                    if assigned and assigned.get("id") == assigned_id:
                                        label_info = assigned
                                    elif suggested and suggested.get("id") == assigned_id:
                                        label_info = suggested
                                    else:
                                        label_info = assigned or suggested
                                    if label_info:
                                        label_text = label_info.get(
                                            "direccion", f"ID {label_info.get('id')}"
                                        )
                                        if label_info.get("score") is not None:
                                            try:
                                                label_text += " · " + (
                                                    f"{float(label_info['score']) * 100:.1f}%"
                                                )
                                            except (TypeError, ValueError):
                                                pass
                                    elif assigned_id:
                                        label_text = f"ID {assigned_id}"
                                    elif suggested:
                                        label_text = suggested.get(
                                            "direccion", "Sin bloque sugerido"
                                        )
                                        if suggested.get("score") is not None:
                                            try:
                                                label_text += " · " + (
                                                    f"{float(suggested['score']) * 100:.1f}%"
                                                )
                                            except (TypeError, ValueError):
                                                pass
                                    else:
                                        label_text = "Sin bloque sugerido"
                                    label.set_text(label_text)

                                record.setdefault("ui_updaters", {})[
                                    f"{data_key}_bloque_input"
                                ] = update_input
                                update_input()
                            continue
                        ui.input(value=record[data_key].get(field)).classes(
                            width
                        ).bind_value(record[data_key], field).on(
                            "change", lambda r=record: self._revalidate_record(r)
                        )
                    update_row_style()

    def _normalize_for_sorting(self, value: Any) -> Any:
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, bool):
            return str(value)
        str_value = str(value).strip()
        try:
            return float(str_value)
        except (ValueError, TypeError):
            pass
        return "".join(
            c
            for c in unicodedata.normalize("NFD", str_value.lower())
            if unicodedata.category(c) != "Mn"
        )

    def _sort_by_column(self, column: str):
        existing = next((c for c in self.state.sort_criteria if c[0] == column), None)
        direction = not existing[1] if existing else True
        self.state.sort_criteria = [(column, direction)]
        self.state.records.sort(
            key=lambda r: self._normalize_for_sorting(
                r["validation"]["is_valid"]
                if column == "is_valid"
                else next(
                    (
                        r[key].get(column)
                        for key in ["afiliada", "piso", "facturacion"]
                        if column in r[key]
                    ),
                    None,
                )
            ),
            reverse=not direction,
        )
        self._render_preview_tabs()

    def _drop_record(self, record_to_drop: Dict):
        self.state.records.remove(record_to_drop)
        self._render_preview_tabs()

    def _revalidate_record(self, record: Dict):
        bloque_val = record.get("piso", {}).get("bloque_id")
        if isinstance(bloque_val, str):
            trimmed = bloque_val.strip()
            record["piso"]["bloque_id"] = int(trimmed) if trimmed.isdigit() else None
        elif isinstance(bloque_val, float) and bloque_val.is_integer():
            record["piso"]["bloque_id"] = int(bloque_val)

        meta = record.setdefault("meta", {})
        assigned_id = record["piso"].get("bloque_id")
        suggested = meta.get("bloque")
        manual_info = meta.get("bloque_manual")
        if assigned_id is None:
            meta["bloque_manual"] = None
        elif suggested and suggested.get("id") == assigned_id:
            meta["bloque_manual"] = suggested
        elif manual_info and manual_info.get("id") != assigned_id:
            meta["bloque_manual"] = None

        is_valid_afiliada, errors_afiliada = validator.validate_record(
            "afiliadas", record["afiliada"], "create"
        )
        is_valid_piso, errors_piso = validator.validate_record(
            "pisos", record["piso"], "create"
        )
        is_valid_bloque, errors_bloque = validator.validate_record(
            "bloques", record.setdefault("bloque", {}), "create"
        )
        is_valid_facturacion, errors_facturacion = validator.validate_record(
            "facturacion", record["facturacion"], "create"
        )
        record["validation"].update(
            {
                "is_valid": is_valid_afiliada
                and is_valid_piso
                and is_valid_bloque
                and is_valid_facturacion,
                "errors": errors_afiliada
                + errors_piso
                + errors_bloque
                + errors_facturacion,
            }
        )
        for updater in record.get("ui_updaters", {}).values():
            updater()
        self._update_import_button_state()

    def _update_import_button_state(self):
        if self.import_button:
            self.import_button.set_enabled(
                all(r["validation"]["is_valid"] for r in self.state.records)
                and bool(self.state.records)
            )

    async def _on_score_limit_change(self, value: Any):
        if isinstance(value, dict):
            value = value.get("value")
        if value is None:
            return
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return
        try:
            new_limit = float(value)
        except (TypeError, ValueError):
            ui.notify("Valor de umbral no válido", type="warning")
            return
        new_limit = max(0.0, min(1.0, new_limit))
        if abs(new_limit - self.bloque_score_limit) < 0.001:
            return
        self.bloque_score_limit = new_limit
        await self._schedule_refresh()

    async def _refresh_bloque_suggestions(self):
        if not self.state.records:
            return
        await self._apply_batch_bloque_suggestions(self.state.records)

    async def _schedule_refresh(self):
        if self._suggestion_task and not self._suggestion_task.done():
            self._suggestion_task.cancel()
            try:
                await self._suggestion_task
            except asyncio.CancelledError:
                pass
        self._suggestion_task = asyncio.create_task(self._refresh_bloque_suggestions())
        try:
            await self._suggestion_task
        except asyncio.CancelledError:
            pass
        finally:
            self._suggestion_task = None

    async def _start_import(self):
        valid_records = [
            r
            for r in self.state.records
            if r.get("validation", {}).get("is_valid", False)
        ]
        if not valid_records:
            return ui.notify("No hay datos válidos para importar.", "warning")
        total, success_count, failed, full_log, new_afiliadas = (
            len(valid_records),
            0,
            [],
            [],
            [],
        )
        with ui.dialog() as progress_dialog, ui.card().classes("min-w-[600px]"):
            ui.label("Iniciando Importación...").classes("text-h6")
            status = ui.label(f"Preparando {total} registros.")
            progress = ui.linear_progress(0).classes("w-full my-2")
            live_log = ui.log(max_lines=10).classes(
                "w-full h-48 bg-gray-100 p-2 rounded"
            )
        progress_dialog.open()
        for i, record in enumerate(valid_records):
            name = f"{record['afiliada'].get('nombre')} {record['afiliada'].get('apellidos')}".strip()
            status.set_text(f"Procesando {i + 1}/{total}: {name}...")
            log = lambda msg: (live_log.push(msg), full_log.append(msg))
            try:
                piso = (
                    await self.api.get_records(
                        "pisos", {"direccion": f'eq.{record["piso"]["direccion"]}'}
                    )
                    or [None]
                )[0]
                piso_id = piso["id"] if piso else None
                meta_info = record.get("meta", {})
                bloque_data = record.setdefault("bloque", {})
                suggested_bloque_id = record.get("piso", {}).get("bloque_id")
                suggested_info = meta_info.get("bloque") or {}
                manual_info = meta_info.get("bloque_manual") or {}
                display_info = manual_info if manual_info.get("id") else suggested_info
                bloque_dir_fallback = (
                    manual_info.get("direccion")
                    or suggested_info.get("direccion")
                    or bloque_data.get("direccion")
                    or record["piso"].get("direccion")
                    or ""
                )
                bloque_data["direccion"] = bloque_dir_fallback

                bloque_id = suggested_bloque_id
                if bloque_dir_fallback:
                    try:
                        if bloque_id:
                            existing_bloque = await self.api.get_records(
                                "bloques", {"id": f"eq.{bloque_id}"}, limit=1
                            )
                            if not existing_bloque:
                                new_bloque, b_err = await self.api.create_record(
                                    "bloques",
                                    {"direccion": bloque_dir_fallback},
                                    validate=False,
                                    show_validation_errors=False,
                                )
                                if b_err:
                                    raise Exception(f"Bloque: {b_err}")
                                bloque_id = new_bloque["id"]
                                record["piso"]["bloque_id"] = bloque_id
                                meta_info["bloque_manual"] = {
                                    **new_bloque,
                                    "score": None,
                                }
                                display_info = meta_info["bloque_manual"]
                                log(
                                    f"➕ Bloque creado (ID {bloque_id}): {new_bloque.get('direccion')}"
                                )
                            else:
                                meta_info["bloque_manual"] = {
                                    **existing_bloque[0],
                                    "score": meta_info.get("bloque_score"),
                                }
                                display_info = meta_info["bloque_manual"]
                        else:
                            existing_bloque = await self.api.get_records(
                                "bloques",
                                {"direccion": f"eq.{bloque_dir_fallback}"},
                                limit=1,
                            )
                            if existing_bloque:
                                bloque_id = existing_bloque[0]["id"]
                                record["piso"]["bloque_id"] = bloque_id
                                meta_info["bloque_manual"] = {
                                    **existing_bloque[0],
                                    "score": meta_info.get("bloque_score"),
                                }
                                display_info = meta_info["bloque_manual"]
                                log(
                                    f"ℹ️ Bloque encontrado: {existing_bloque[0].get('direccion')}"
                                )
                            else:
                                new_bloque, b_err = await self.api.create_record(
                                    "bloques",
                                    {"direccion": bloque_dir_fallback},
                                    validate=False,
                                    show_validation_errors=False,
                                )
                                if b_err:
                                    raise Exception(f"Bloque: {b_err}")
                                bloque_id = new_bloque["id"]
                                record["piso"]["bloque_id"] = bloque_id
                                meta_info["bloque_manual"] = {
                                    **new_bloque,
                                    "score": None,
                                }
                                display_info = meta_info["bloque_manual"]
                                log(
                                    f"➕ Bloque creado (ID {bloque_id}): {new_bloque.get('direccion')}"
                                )
                        suggested_bloque_id = bloque_id
                    except Exception as bloque_exc:
                        raise Exception(str(bloque_exc))
                suggested_bloque_msg = (display_info or {}).get("direccion")
                if piso_id:
                    log(f"ℹ️ Piso encontrado: {piso['direccion']}")
                    if suggested_bloque_id and piso.get("bloque_id") != suggested_bloque_id:
                        updated = await self.api.update_record(
                            "pisos",
                            piso_id,
                            {"bloque_id": suggested_bloque_id},
                            validate=False,
                            show_validation_errors=False,
                        )
                        if updated and updated.get("bloque_id") == suggested_bloque_id:
                            log(
                                "🔗 Bloque enlazado al piso existente"
                                + (
                                    f": {suggested_bloque_msg}"
                                    if suggested_bloque_msg
                                    else ""
                                )
                            )
                else:
                    new_piso, p_err = await self.api.create_record(
                        "pisos", record["piso"], show_validation_errors=False
                    )
                    if p_err:
                        raise Exception(f"Piso: {p_err}")
                    piso_id = new_piso["id"]
                    log(f"➕ Piso creado: {new_piso['direccion']}")
                    if suggested_bloque_msg:
                        log(f"🔗 Piso asociado al bloque sugerido: {suggested_bloque_msg}")
                if not suggested_bloque_id:
                    log("⚠️ Sin bloque sugerido para este piso")
                record["afiliada"]["piso_id"] = piso_id
                new_afiliada, a_err = await self.api.create_record(
                    "afiliadas", record["afiliada"], show_validation_errors=False
                )
                if a_err:
                    raise Exception(f"Afiliada: {a_err}")
                new_afiliadas.append(new_afiliada)
                log(
                    f"➕ Afiliada creada: {name} (Nº: {new_afiliada.get('num_afiliada')})"
                )
                record["facturacion"]["afiliada_id"] = new_afiliada["id"]
                _, f_err = await self.api.create_record(
                    "facturacion", record["facturacion"], show_validation_errors=False
                )
                if f_err:
                    log(f"⚠️ AVISO (Facturación): {name}: {f_err}")
                else:
                    log(f"➕ Facturación añadida para {name}")
                success_count += 1
            except Exception as e:
                failed.append((name, str(e)))
                log(f"❌ FALLO: {name} - {str(e)}")
            progress.value = (i + 1) / total
            await asyncio.sleep(0.01)
        progress_dialog.close()
        with ui.dialog() as summary_dialog, ui.card().classes(
            "min-w-[800px] max-w-[90vw]"
        ):
            ui.label("Resultado de la Importación").classes("text-h6")
            if success_count > 0:
                ui.markdown(
                    f"✅ **Se importaron {success_count} de {total} registros exitosamente.**"
                ).classes("text-positive")
            if new_afiliadas:
                with ui.expansion("Ver Afiliadas Creadas", icon="person_add").classes(
                    "w-full"
                ):
                    ui.table(
                        columns=[
                            {
                                "name": "num",
                                "label": "Nº Afiliada",
                                "field": "num_afiliada",
                            },
                            {
                                "name": "nombre",
                                "label": "Nombre Completo",
                                "field": "nombre_completo",
                            },
                        ],
                        rows=[
                            {
                                **na,
                                "nombre_completo": f"{na['nombre']} {na['apellidos']}",
                            }
                            for na in new_afiliadas
                        ],
                        row_key="id",
                    ).classes("w-full")
            if failed:
                ui.markdown(
                    f"❌ **Fallaron {len(failed)} de {total} registros.**"
                ).classes("text-negative")
                with ui.expansion(
                    "Ver Resumen de Errores", icon="report_problem", value=True
                ).classes("w-full"):
                    ui.table(
                        columns=[
                            {
                                "name": "afiliada",
                                "label": "Afiliada",
                                "field": "afiliada",
                            },
                            {
                                "name": "error",
                                "label": "Razón del Fallo",
                                "field": "error",
                            },
                        ],
                        rows=[
                            {"afiliada": name, "error": reason}
                            for name, reason in failed
                        ],
                        row_key="afiliada",
                    ).classes("w-full")
            with ui.expansion("Ver Registro Completo", icon="article").classes(
                "w-full"
            ):
                ui.textarea(value="\n".join(full_log)).props(
                    "readonly outlined rows=10"
                ).classes("w-full")
            ui.button("Aceptar", on_click=summary_dialog.close).classes("mt-4 self-end")
        summary_dialog.open()
        self.state.set_records([])
        self._render_preview_tabs()
