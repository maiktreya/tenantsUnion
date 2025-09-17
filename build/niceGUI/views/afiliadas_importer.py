import pandas as pd
import io
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
from nicegui import ui, events

from api.client import APIClient
from api.validate import validator
from state.app_state import GenericViewState
from config import IMPORTER_HEADER_MAP


class AfiliadasImporterView:
    """A view to import 'afiliadas' with live validation, sorting, and an editable preview."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = GenericViewState()
        self.afiliadas_panel: Optional[ui.column] = None
        self.pisos_panel: Optional[ui.column] = None
        self.facturacion_panel: Optional[ui.column] = None
        self.import_button: Optional[ui.button] = None

    def create(self) -> ui.column:
        """Create the UI for the CSV importer view."""
        container = ui.column().classes("w-full p-4 gap-4")
        with container:
            ui.label("Importar Nuevas Afiliadas desde CSV").classes("text-h4")
            ui.markdown(
                "Sube un archivo CSV. Los datos se validarán y se mostrarán en pestañas. "
                "Las filas con errores se marcarán en rojo. Corrige los datos antes de importar."
            )

            with ui.row().classes("w-full gap-4 items-center"):
                ui.upload(
                    on_upload=self._handle_upload,
                    auto_upload=True,
                    label="Subir archivo afiliacion.csv",
                ).props('accept=".csv"')
                self.import_button = ui.button(
                    "Iniciar Importación", icon="upload", on_click=self._start_import
                ).props("color=orange-600")

            ui.separator().classes("mt-4")

            with ui.tabs().props('align="left"') as tabs:
                ui.tab("afiliadas", label="Afiliadas")
                ui.tab("pisos", label="Pisos")
                ui.tab("facturacion", label="Facturación")

            with ui.tab_panels(tabs, value="afiliadas").classes(
                "w-full border rounded-md"
            ):
                with ui.tab_panel("afiliadas"):
                    self.afiliadas_panel = ui.column().classes("w-full")
                with ui.tab_panel("pisos"):
                    self.pisos_panel = ui.column().classes("w-full")
                with ui.tab_panel("facturacion"):
                    self.facturacion_panel = ui.column().classes("w-full")

        return container

    def _handle_upload(self, e: events.UploadEventArguments):
        """Handle the file upload, parse, validate, and render the editable tabs."""
        try:
            content = e.content.read()
            decoded_content = content.decode("utf-8-sig")
            raw_dataframe = pd.read_csv(
                io.StringIO(decoded_content), header=None, quotechar='"', sep=","
            )

            data_dataframe = raw_dataframe.iloc[1:]

            records = [
                record
                for _, row in data_dataframe.iterrows()
                if (record := self._transform_and_validate_row(row)) is not None
            ]
            self.state.set_records(records)

            self._render_preview_tabs()
            ui.notify(
                "Archivo procesado. Revisa y corrige los datos antes de importar.",
                type="positive",
            )
        except Exception as ex:
            ui.notify(
                f"Error al procesar el archivo: {type(ex).__name__}: {ex}",
                type="negative",
            )
            self.state.set_records([])
            self._render_preview_tabs()

    def _transform_and_validate_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Transforms a single row, validates it, and adds validation status."""

        def _parse_date(date_str: str) -> Optional[str]:
            if not date_str or pd.isna(date_str):
                return None
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(str(date_str), fmt).date().isoformat()
                except (ValueError, TypeError):
                    continue
            return None

        try:

            def get_val(index):
                return "" if pd.isna(row.get(index)) else str(row.get(index)).strip()

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
                "trato_propiedad": (
                    True if get_val(18).lower() in ["true", "si", "1"] else False
                ),
                "piso_id": None,
            }

            piso_data = {
                "direccion": final_address,
                "municipio": get_val(13),
                "cp": int(get_val(14)) if get_val(14).isdigit() else None,
                "n_personas": int(get_val(15)) if get_val(15).isdigit() else None,
                "inmobiliaria": get_val(18),
                "prop_vertical": get_val(20),
                "fecha_firma": _parse_date(get_val(16)),
            }

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
            is_valid_facturacion, errors_facturacion = validator.validate_record(
                "facturacion", facturacion_data, "create"
            )

            return {
                "piso": piso_data,
                "afiliada": afiliada_data,
                "facturacion": facturacion_data,
                "validation": {
                    "is_valid": is_valid_afiliada
                    and is_valid_piso
                    and is_valid_facturacion,
                    "errors": errors_afiliada + errors_piso + errors_facturacion,
                },
            }
        except Exception as e:
            return None

    def _render_preview_tabs(self):
        """Render all three preview panels and update the import button state."""
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
                "trato_propiedad",
            ],
        )
        self._render_panel(
            "piso",
            self.pisos_panel,
            [
                "direccion",
                "municipio",
                "cp",
                "n_personas",
                "inmobiliaria",
                "prop_vertical",
            ],
        )
        self._render_panel(
            "facturacion",
            self.facturacion_panel,
            ["cuota", "periodicidad", "forma_pago", "iban"],
        )
        self._update_import_button_state()

    def _render_panel(self, data_key: str, panel: ui.column, fields: List[str]):
        if not panel:
            return
        panel.clear()
        with panel, ui.scroll_area().classes("w-full h-[32rem]"):
            with ui.row().classes(
                "w-full font-bold text-gray-600 gap-2 p-2 bg-gray-50 items-center no-wrap sticky top-0 z-10"
            ):
                ui.label("Acciones").classes("w-16 min-w-[4rem]")
                ui.label("Estado").classes("w-24 min-w-[6rem]")
                ui.label("Afiliada").classes("w-48 min-w-[12rem]")
                for field in fields:
                    width = (
                        "flex-grow min-w-[15rem]"
                        if field in ["email", "direccion", "iban"]
                        else "w-32 min-w-[8rem]"
                    )
                    ui.label(IMPORTER_HEADER_MAP.get(field, field.title())).classes(
                        width
                    )

            for record in self.state.records:
                record.setdefault("ui_updaters", {})
                with ui.row().classes(
                    "w-full items-center gap-2 p-2 border-t no-wrap"
                ) as row:

                    def update_row_style(r=row, rec=record):
                        is_valid = rec["validation"]["is_valid"]
                        r.classes(
                            remove="bg-red-100 bg-green-50",
                            add="bg-green-50" if is_valid else "bg-red-100",
                        )
                        r.tooltip(
                            "\n".join(rec["validation"]["errors"])
                            if not is_valid
                            else "Registro válido"
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
                            ic.name, ic_color = (
                                ("check_circle", "text-green-500")
                                if is_valid
                                else ("cancel", "text-red-500")
                            )
                            ic.classes(
                                remove="text-green-500 text-red-500", add=ic_color
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
                        ui.input(value=record[data_key].get(field)).classes(
                            width
                        ).bind_value(record[data_key], field).on(
                            "change", lambda r=record: self._revalidate_record(r)
                        )
                update_row_style()

    def _drop_record(self, record_to_drop: Dict):
        self.state.records.remove(record_to_drop)
        self._render_preview_tabs()
        ui.notify("Fila eliminada de la importación.", type="info")

    def _revalidate_record(self, record: Dict):
        is_valid_afiliada, errors_afiliada = validator.validate_record(
            "afiliadas", record["afiliada"], "create"
        )
        is_valid_piso, errors_piso = validator.validate_record(
            "pisos", record["piso"], "create"
        )
        is_valid_facturacion, errors_facturacion = validator.validate_record(
            "facturacion", record["facturacion"], "create"
        )
        record["validation"].update(
            {
                "is_valid": is_valid_afiliada
                and is_valid_piso
                and is_valid_facturacion,
                "errors": errors_afiliada + errors_piso + errors_facturacion,
            }
        )
        for updater in record["ui_updaters"].values():
            updater()
        self._update_import_button_state()

    def _update_import_button_state(self):
        if self.import_button:
            all_valid = all(r["validation"]["is_valid"] for r in self.state.records)
            self.import_button.set_enabled(all_valid and bool(self.state.records))

    async def _start_import(self):
        valid_records = [
            r
            for r in self.state.records
            if r.get("validation", {}).get("is_valid", False)
        ]
        if not valid_records:
            return ui.notify("No hay datos válidos para importar.", "warning")

        total_records, success_count = len(valid_records), 0
        failed_records: List[Tuple[str, str]] = []
        full_log_messages, new_afiliadas = [], []

        with ui.dialog() as progress_dialog, ui.card().classes("min-w-[600px]"):
            ui.label("Iniciando Importación...").classes("text-h6")
            status_label = ui.label(f"Preparando {total_records} registros.")
            progress = ui.linear_progress(0).classes("w-full my-2")
            live_log = ui.log(max_lines=10).classes(
                "w-full h-48 bg-gray-100 p-2 rounded"
            )
        progress_dialog.open()

        for i, record in enumerate(valid_records):
            afiliada_name = f"{record['afiliada'].get('nombre')} {record['afiliada'].get('apellidos')}".strip()
            status_label.set_text(
                f"Procesando {i + 1}/{total_records}: {afiliada_name}..."
            )
            log_message = lambda msg: (
                live_log.push(msg),
                full_log_messages.append(msg),
            )

            try:
                existing_pisos = await self.api.get_records(
                    "pisos", {"direccion": f'eq.{record["piso"]["direccion"]}'}
                )
                piso_id = existing_pisos[0]["id"] if existing_pisos else None

                if not piso_id:
                    new_piso, piso_error = await self.api.create_record(
                        "pisos", record["piso"], show_validation_errors=False
                    )
                    if piso_error:
                        raise Exception(f"Piso: {piso_error}")
                    piso_id = new_piso["id"]
                    log_message(f"➕ Piso creado: {record['piso']['direccion']}")
                else:
                    log_message(f"ℹ️ Piso encontrado: {record['piso']['direccion']}")

                record["afiliada"]["piso_id"] = piso_id
                new_afiliada, afiliada_error = await self.api.create_record(
                    "afiliadas", record["afiliada"], show_validation_errors=False
                )
                if afiliada_error:
                    raise Exception(f"Afiliada: {afiliada_error}")
                new_afiliadas.append(new_afiliada)
                log_message(f"➕ Afiliada creada: {afiliada_name}")

                record["facturacion"]["afiliada_id"] = new_afiliada["id"]
                _, facturacion_error = await self.api.create_record(
                    "facturacion", record["facturacion"], show_validation_errors=False
                )
                if facturacion_error:
                    log_message(f"⚠️ AVISO: {afiliada_name}: {facturacion_error}")
                else:
                    log_message(f"➕ Facturación añadida para {afiliada_name}")

                success_count += 1
                log_message(f"✅ ÉXITO: {afiliada_name} importada.")
            except Exception as e:
                error_msg = str(e)
                failed_records.append((afiliada_name, error_msg))
                log_message(f"❌ FALLO: {afiliada_name} - {error_msg}")

            progress.value = (i + 1) / total_records
            await asyncio.sleep(0.01)

        progress_dialog.close()

        with ui.dialog() as summary_dialog, ui.card().classes("min-w-[700px]"):
            ui.label("Resultado de la Importación").classes("text-h6")
            if success_count > 0:
                ui.markdown(
                    f"✅ **Se importaron {success_count} de {total_records} registros exitosamente.**"
                ).classes("text-positive")
            if failed_records:
                ui.markdown(
                    f"❌ **Fallaron {len(failed_records)} de {total_records} registros.**"
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
                                "align": "left",
                            },
                            {
                                "name": "error",
                                "label": "Razón del Fallo",
                                "field": "error",
                                "align": "left",
                                "style": "white-space: normal;",
                            },
                        ],
                        rows=[
                            {"afiliada": name, "error": reason}
                            for name, reason in failed_records
                        ],
                        row_key="afiliada",
                    ).classes("w-full")

            with ui.expansion(
                "Ver Registro Completo del Proceso", icon="article"
            ).classes("w-full"):
                ui.textarea(value="\n".join(full_log_messages)).props(
                    "readonly outlined rows=10"
                ).classes("w-full")

            ui.button("Aceptar", on_click=summary_dialog.close).classes("mt-4 self-end")
        summary_dialog.open()

        self.state.set_records([])
        self._render_preview_tabs()
