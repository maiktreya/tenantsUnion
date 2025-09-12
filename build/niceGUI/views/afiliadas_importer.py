# /build/niceGUI/views/afiliadas_importer.py

import pandas as pd
import io
import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import date
from nicegui import ui, events
from api.client import APIClient
from api.validate import validator
from state.importer_state import ImporterState


class AfiliadasImporterView:
    """A view to import 'afiliadas' with live validation, sorting, and an editable preview."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = ImporterState()
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

            records = [
                record
                for _, row in raw_dataframe.iterrows()
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
        try:

            def get_val(index):
                return "" if pd.isna(row.get(index)) else str(row.get(index)).strip()

            nombre = get_val(0).strip("<").strip('"')
            if not nombre:
                return None

            # Afiliada data is now cleaner
            afiliada_data = {
                "num_afiliada": get_val(29),
                "nombre": nombre,
                "apellidos": f"{get_val(2)} {get_val(3)}".strip(),
                "genero": get_val(4),
                "fecha_nacimiento": get_val(5),
                "cif": get_val(6),
                "telefono": get_val(7),
                "email": get_val(8),
                "fecha_alta": get_val(16),
                "regimen": get_val(17),
                "estado": "Alta",
                "trato_propiedad": bool(get_val(18)),
                "piso_id": None,
            }

            # Piso data now includes fields previously in afiliada
            piso_data = {
                "direccion": re.sub(
                    r"\s+",
                    " ",
                    f"{get_val(9)} {get_val(10)}, {get_val(11)} {get_val(12)}, {get_val(14)}, {get_val(13)}".strip(
                        ", "
                    ),
                ).strip(),
                "municipio": get_val(13),
                "cp": int(get_val(14)) if get_val(14).isdigit() else None,
                "n_personas": int(get_val(15)) if get_val(15).isdigit() else None,
                "inmobiliaria": get_val(18),
                "prop_vertical": get_val(20) == "Si",
            }

            cuota_type = get_val(22)
            cuota_str = (
                get_val(23)
                if cuota_type == "Cuota de Apoyo"
                else get_val(24) if cuota_type == "Cuota Sindical" else get_val(25)
            )
            cuota_match = re.search(r"(\d+)\s*€\s*(mes|año)", cuota_str)
            iban_raw = get_val(26).replace(" ", "")
            facturacion_data = {
                "cuota": float(cuota_match.group(1)) if cuota_match else 0.0,
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
            print(f"Skipping row due to parsing error: {e}")
            return None

    def _render_preview_tabs(self):
        """Render all three preview panels and update the import button state."""
        # Revised fields for afiliadas panel
        self._render_panel(
            "afiliada",
            self.afiliadas_panel,
            [
                "num_afiliada",
                "nombre",
                "apellidos",
                "cif",
                "email",
                "telefono",
                "fecha_nacimiento",
                "trato_propiedad",
                "fecha_alta",
            ],
        )
        # Revised fields for pisos panel
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
        """Generic function to render a preview panel with sorting and reactive rows."""
        if not panel:
            return
        panel.clear()

        header_map = {
            "num_afiliada": "Nº Afiliada",
            "nombre": "Nombre",
            "apellidos": "Apellidos",
            "cif": "CIF/NIE",
            "email": "Email",
            "telefono": "Teléfono",
            "direccion": "Dirección",
            "municipio": "Municipio",
            "cp": "CP",
            "fecha_nacimiento": "Fecha Nacimiento",
            "trato_propiedad": "Trato Directo",
            "propiedad": "Propiedad",
            "prop_vertical": "Prop. Vertical",
            "fecha_alta": "Fecha Alta",
            "n_personas": "Nº Personas",
            "inmobiliaria": "Inmobiliaria",
            "cuota": "Cuota (€)",
            "periodicidad": "Periodicidad (m)",
            "forma_pago": "Forma Pago",
            "iban": "IBAN",
        }

        with panel, ui.scroll_area().classes("w-full h-[32rem]"):
            with ui.row().classes(
                "w-full font-bold text-gray-600 gap-2 p-2 bg-gray-50 rounded-t-md items-center no-wrap sticky top-0 z-10"
            ):
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
                    width_class = (
                        "flex-grow min-w-[15rem]"
                        if field in ["email", "direccion", "iban"]
                        else "w-32 min-w-[8rem]"
                    )
                    with ui.row().classes(
                        f"{width_class} items-center cursor-pointer"
                    ).on("click", lambda f=field: self._sort_by_column(f)):
                        ui.label(header_map.get(field, field.title()))
                        sort_info = next(
                            (c for c in self.state.sort_criteria if c[0] == field), None
                        )
                        if sort_info:
                            ui.icon(
                                "arrow_upward" if sort_info[1] else "arrow_downward",
                                size="sm",
                            )
            for record in self.state.records:
                if "ui_updaters" not in record:
                    record["ui_updaters"] = {}
                with ui.row().classes(
                    "w-full items-center gap-2 p-2 border-t no-wrap"
                ) as row:

                    def update_row_style(r=row, rec=record):
                        is_valid = rec["validation"]["is_valid"]
                        errors = rec["validation"]["errors"]
                        r.classes(
                            remove="bg-red-100 bg-green-50",
                            add="bg-green-50" if is_valid else "bg-red-100",
                        )
                        r.tooltip(
                            "\n".join(errors) if not is_valid else "Registro válido"
                        )

                    record["ui_updaters"][data_key] = update_row_style
                    with ui.column().classes(
                        "w-24 min-w-[6rem] flex items-center justify-center"
                    ):
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
                    afiliada_label = f"{record['afiliada']['nombre']} {record['afiliada']['apellidos']}"
                    ui.label(afiliada_label).classes(
                        "w-48 min-w-[12rem] text-sm text-gray-600"
                    )
                    for field in fields:
                        value = record[data_key].get(field)
                        input_element = (
                            ui.number(label=None, format="%.0f")
                            if field in ["cp", "n_personas"]
                            else (
                                ui.checkbox()
                                if isinstance(value, bool)
                                else ui.input(label=None)
                            )
                        )
                        width_class = (
                            "flex-grow min-w-[15rem]"
                            if field in ["email", "direccion", "iban"]
                            else "w-32 min-w-[8rem]"
                        )
                        input_element.bind_value(record[data_key], field).classes(
                            width_class
                        )
                        input_element.on(
                            "change", lambda r=record: self._revalidate_record(r)
                        )
                update_row_style()

    def _sort_by_column(self, column: str):
        """Handles sorting when a column header is clicked."""
        existing_criterion = next(
            (c for c in self.state.sort_criteria if c[0] == column), None
        )
        new_direction = not existing_criterion[1] if existing_criterion else True
        self.state.sort_criteria = [(column, new_direction)]
        self.state.apply_filters_and_sort()
        self._render_preview_tabs()

    def _revalidate_record(self, record: Dict):
        """Re-validates a single record and updates its UI in ALL tabs."""
        is_valid_afiliada, errors_afiliada = validator.validate_record(
            "afiliadas", record["afiliada"], "create"
        )
        is_valid_piso, errors_piso = validator.validate_record(
            "pisos", record["piso"], "create"
        )
        is_valid_facturacion, errors_facturacion = validator.validate_record(
            "facturacion", record["facturacion"], "create"
        )
        record["validation"]["is_valid"] = (
            is_valid_afiliada and is_valid_piso and is_valid_facturacion
        )
        record["validation"]["errors"] = (
            errors_afiliada + errors_piso + errors_facturacion
        )
        if "ui_updaters" in record:
            for updater in record["ui_updaters"].values():
                updater()
        self._update_import_button_state()

    def _update_import_button_state(self):
        """Enable or disable the import button based on validation status."""
        if self.import_button:
            all_valid = all(r["validation"]["is_valid"] for r in self.state.records)
            self.import_button.set_enabled(all_valid and bool(self.state.records))

    async def _start_import(self):
        """Starts the import process, using the records from the state."""
        valid_records = [
            r
            for r in self.state.records
            if r.get("validation", {}).get("is_valid", False)
        ]
        if not valid_records:
            ui.notify("No hay datos válidos para importar.", "warning")
            return

        total_records, success_count = len(valid_records), 0
        error_messages, full_log_messages = [], []

        with ui.dialog() as progress_dialog, ui.card().classes("min-w-[600px]"):
            ui.label("Iniciando Importación...").classes("text-h6")
            status_label = ui.label(
                f"Preparando para importar {total_records} registros válidos."
            )
            progress = ui.linear_progress(0).classes("w-full my-2")
            live_log = ui.log(max_lines=10).classes(
                "w-full h-48 bg-gray-100 p-2 rounded"
            )
        progress_dialog.open()

        for i, record in enumerate(valid_records):
            afiliada_name = (
                f"{record['afiliada'].get('nombre', '')} {record['afiliada'].get('apellidos', '')}".strip()
                or f"Registro #{i+1}"
            )
            status_label.set_text(
                f"Procesando {i + 1}/{total_records}: {afiliada_name}..."
            )
            log_message = lambda msg: (
                live_log.push(msg),
                full_log_messages.append(msg),
            )
            try:
                piso_id = None
                existing_pisos = await self.api.get_records(
                    "pisos", {"direccion": f'eq.{record["piso"]["direccion"]}'}
                )
                if existing_pisos:
                    piso_id = existing_pisos[0]["id"]
                    # Update existing piso with new info from CSV
                    await self.api.update_record("pisos", piso_id, record["piso"])
                    log_message(
                        f"ℹ️ Piso encontrado y actualizado: {record['piso']['direccion']}"
                    )
                else:
                    new_piso = await self.api.create_record("pisos", record["piso"])
                    if new_piso:
                        piso_id = new_piso["id"]
                        log_message(f"➕ Piso creado: {record['piso']['direccion']}")
                if not piso_id:
                    raise Exception("No se pudo crear o encontrar el piso.")
                record["afiliada"]["piso_id"] = piso_id
                num_afiliada = record["afiliada"]["num_afiliada"]
                if not num_afiliada:
                    raise Exception("El Nº de Afiliada (ID Entrada) es obligatorio.")
                if await self.api.get_records(
                    "afiliadas", {"num_afiliada": f"eq.{num_afiliada}"}
                ):
                    raise Exception(f"La afiliada con Nº {num_afiliada} ya existe.")
                new_afiliada = await self.api.create_record(
                    "afiliadas", record["afiliada"]
                )
                if not new_afiliada:
                    raise Exception("No se pudo crear la afiliada.")
                log_message(f"➕ Afiliada creada: {afiliada_name} ({num_afiliada})")
                record["facturacion"]["afiliada_id"] = new_afiliada["id"]
                await self.api.create_record("facturacion", record["facturacion"])
                log_message(f"➕ Facturación añadida para {afiliada_name}")
                success_count += 1
                log_message(f"✅ ÉXITO: {afiliada_name} importada completamente.")
            except Exception as e:
                error_msg = f"Error en {afiliada_name}: {e}"
                error_messages.append(error_msg)
                log_message(f"❌ FALLO: {error_msg}")
            progress.value = (i + 1) / total_records
            await asyncio.sleep(0.05)
        progress_dialog.close()

        with ui.dialog() as summary_dialog, ui.card().classes("min-w-[700px]"):
            ui.label("Resultado de la Importación").classes("text-h6")
            if success_count > 0:
                ui.markdown(
                    f"✅ **Se importaron {success_count} de {total_records} registros exitosamente.**"
                ).classes("text-positive")
            if error_messages:
                ui.markdown(
                    f"❌ **Fallaron {len(error_messages)} de {total_records} registros.**"
                ).classes("text-negative")
            with ui.expansion(
                "Ver Registro Completo del Proceso", icon="article"
            ).classes("w-full"):
                ui.textarea(value="\n".join(full_log_messages)).props(
                    "readonly outlined rows=15"
                ).classes("w-full")
            if error_messages:
                with ui.expansion(
                    "Ver Resumen de Errores", icon="report_problem"
                ).classes("w-full"):
                    with ui.scroll_area().classes("w-full h-48 border rounded p-2"):
                        for msg in error_messages:
                            ui.label(msg).classes("text-sm text-negative")
            with ui.row().classes("w-full justify-end mt-4"):
                ui.button("Aceptar", on_click=summary_dialog.close)
        summary_dialog.open()

        self.state.set_records([])
        self._render_preview_tabs()
