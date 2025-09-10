# /build/niceGUI/views/afiliadas_importer.py

import pandas as pd
import io
import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import date
from nicegui import ui, events
from api.client import APIClient


class AfiliadasImporterView:
    """A view to import new 'afiliadas' from a WordPress CSV export with a tabbed, editable preview."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.records_to_import: List[Dict] = []
        # Containers for each tab's content
        self.afiliadas_panel = None
        self.pisos_panel = None
        self.facturacion_panel = None

    def create(self) -> ui.column:
        """Create the UI for the CSV importer view."""
        container = ui.column().classes("w-full p-4 gap-4")
        with container:
            ui.label("Importar Nuevas Afiliadas desde CSV").classes("text-h4")
            ui.markdown(
                "Sube el archivo CSV. Los datos se organizarán en pestañas para que puedas "
                "revisar y corregir la información de Afiliadas, Pisos y Facturación antes de la importación."
            )

            with ui.row().classes("w-full gap-4 items-center"):
                ui.upload(
                    on_upload=self._handle_upload,
                    auto_upload=True,
                    label="Subir archivo afiliacion.csv",
                ).props('accept=".csv"')
                ui.button(
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
        """Handle the file upload, parse data, and render the editable tabs."""
        try:
            content = e.content.read()
            raw_dataframe = pd.read_csv(
                io.BytesIO(content), header=None, quotechar='"', sep=","
            )

            self.records_to_import = [
                record
                for row in raw_dataframe.iterrows()
                if (record := self._transform_row(row[1])) is not None
            ]

            self._render_preview_tabs()
            ui.notify(
                "Archivo procesado. Ya puedes editar los datos en cada pestaña.",
                type="positive",
            )
        except Exception as ex:
            ui.notify(f"Error al leer el archivo: {ex}", type="negative")
            self.records_to_import = []
            self._render_preview_tabs()

    def _transform_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Transforms a single row into a structured dictionary."""
        try:

            def get_val(index):
                return "" if pd.isna(row.get(index)) else str(row.get(index)).strip()

            nombre = get_val(0).strip("<").strip('"')
            if not nombre:
                return None

            # --- FIX: 'api' field removed from afiliada data structure ---
            afiliada_data = {
                "num_afiliada": get_val(29),
                "nombre": nombre,
                "apellidos": f"{get_val(2)} {get_val(3)}".strip(),
                "genero": get_val(4),
                "cif": get_val(6),
                "telefono": get_val(7),
                "email": get_val(8),
                "fecha_alta": date.today().isoformat(),
                "regimen": get_val(17),
                "estado": "Alta",
                "piso_id": None,
            }

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
                "fecha_firma": get_val(16),
                "api": get_val(18),  # 'api' is now only associated with the piso
            }

            cuota_type = get_val(22)
            if cuota_type == "Cuota de Apoyo":
                cuota_str = get_val(23)
            elif cuota_type == "Cuota Sindical":
                cuota_str = get_val(24)
            else:
                cuota_str = get_val(25)

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

            return {
                "piso": piso_data,
                "afiliada": afiliada_data,
                "facturacion": facturacion_data,
            }
        except Exception as e:
            print(f"Skipping row due to parsing error: {e}")
            return None

    def _render_preview_tabs(self):
        self._render_afiliadas_panel()
        self._render_pisos_panel()
        self._render_facturacion_panel()

    def _render_afiliadas_panel(self):
        self.afiliadas_panel.clear()
        with self.afiliadas_panel:
            # --- FIX: 'API' column removed from afiliadas preview header ---
            with ui.row().classes(
                "w-full font-bold text-gray-600 gap-2 p-2 bg-gray-50 rounded-t-md"
            ):
                ui.label("Nº Afiliada").classes("w-24")
                ui.label("Nombre").classes("w-32")
                ui.label("Apellidos").classes("w-48")
                ui.label("CIF/NIE").classes("w-24")
                ui.label("Email").classes("flex-grow")
                ui.label("Teléfono").classes("w-32")
            with ui.scroll_area().classes("w-full h-96"):
                for record in self.records_to_import:
                    # --- FIX: 'API' input removed from afiliadas preview row ---
                    with ui.row().classes("w-full items-center gap-2 p-2 border-t"):
                        ui.input(label=None).bind_value(
                            record["afiliada"], "num_afiliada"
                        ).classes("w-24")
                        ui.input(label=None).bind_value(
                            record["afiliada"], "nombre"
                        ).classes("w-32")
                        ui.input(label=None).bind_value(
                            record["afiliada"], "apellidos"
                        ).classes("w-48")
                        ui.input(label=None).bind_value(
                            record["afiliada"], "cif"
                        ).classes("w-24")
                        ui.input(label=None).bind_value(
                            record["afiliada"], "email"
                        ).classes("flex-grow")
                        ui.input(label=None).bind_value(
                            record["afiliada"], "telefono"
                        ).classes("w-32")

    def _render_pisos_panel(self):
        self.pisos_panel.clear()
        with self.pisos_panel:
            with ui.row().classes(
                "w-full font-bold text-gray-600 gap-2 p-2 bg-gray-50 rounded-t-md"
            ):
                ui.label("Afiliada").classes("w-48")
                ui.label("Dirección").classes("flex-grow")
                ui.label("Municipio").classes("w-32")
                ui.label("CP").classes("w-16")
                ui.label("Fecha Firma").classes("w-32")
                ui.label("API").classes("w-24")
            with ui.scroll_area().classes("w-full h-96"):
                for record in self.records_to_import:
                    with ui.row().classes("w-full items-center gap-2 p-2 border-t"):
                        ui.label(
                            f"{record['afiliada']['nombre']} {record['afiliada']['apellidos']}"
                        ).classes("w-48 text-sm text-gray-600")
                        ui.input(label=None).bind_value(
                            record["piso"], "direccion"
                        ).classes("flex-grow")
                        ui.input(label=None).bind_value(
                            record["piso"], "municipio"
                        ).classes("w-32")
                        ui.number(label=None, format="%.0f").bind_value(
                            record["piso"], "cp"
                        ).classes("w-16")
                        ui.input(label=None).bind_value(
                            record["piso"], "fecha_firma"
                        ).classes("w-32")
                        ui.input(label=None).bind_value(record["piso"], "api").classes(
                            "w-24"
                        )

    def _render_facturacion_panel(self):
        self.facturacion_panel.clear()
        with self.facturacion_panel:
            with ui.row().classes(
                "w-full font-bold text-gray-600 gap-2 p-2 bg-gray-50 rounded-t-md"
            ):
                ui.label("Afiliada").classes("w-48")
                ui.label("Cuota (€)").classes("w-20")
                ui.label("Periodicidad").classes("w-24")
                ui.label("Forma Pago").classes("w-32")
                ui.label("IBAN").classes("flex-grow")
            with ui.scroll_area().classes("w-full h-96"):
                for record in self.records_to_import:
                    with ui.row().classes("w-full items-center gap-2 p-2 border-t"):
                        ui.label(
                            f"{record['afiliada']['nombre']} {record['afiliada']['apellidos']}"
                        ).classes("w-48 text-sm text-gray-600")
                        ui.number(label=None, format="%.2f").bind_value(
                            record["facturacion"], "cuota"
                        ).classes("w-20")
                        ui.number(label=None, format="%.0f", suffix="m").bind_value(
                            record["facturacion"], "periodicidad"
                        ).classes("w-24")
                        ui.input(label=None).bind_value(
                            record["facturacion"], "forma_pago"
                        ).classes("w-32")
                        ui.input(label=None).bind_value(
                            record["facturacion"], "iban"
                        ).classes("flex-grow")

    async def _start_import(self):
        if not self.records_to_import:
            ui.notify("No hay datos para importar.", "warning")
            return

        total_records = len(self.records_to_import)
        success_count, error_messages, full_log_messages = 0, [], []

        with ui.dialog() as progress_dialog, ui.card().classes("min-w-[600px]"):
            ui.label("Iniciando Importación...").classes("text-h6")
            status_label = ui.label(
                f"Preparando para importar {total_records} registros."
            )
            progress = ui.linear_progress(0).classes("w-full my-2")
            live_log = ui.log(max_lines=10).classes(
                "w-full h-48 bg-gray-100 p-2 rounded"
            )

        progress_dialog.open()

        for i, record in enumerate(self.records_to_import):
            afiliada_name = (
                f"{record['afiliada'].get('nombre', '')} {record['afiliada'].get('apellidos', '')}".strip()
                or f"Registro #{i+1}"
            )
            status_label.set_text(
                f"Procesando {i + 1}/{total_records}: {afiliada_name}..."
            )

            def log_message(msg: str):
                live_log.push(msg)
                full_log_messages.append(msg)

            try:
                piso_id = None
                existing_pisos = await self.api.get_records(
                    "pisos", {"direccion": f'eq.{record["piso"]["direccion"]}'}
                )
                if existing_pisos:
                    piso_id = existing_pisos[0]["id"]
                    log_message(f"ℹ️ Piso encontrado: {record['piso']['direccion']}")
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
                log_content = "\n".join(full_log_messages)
                ui.textarea(value=log_content).props(
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

        self.records_to_import = []
        self._render_preview_tabs()
