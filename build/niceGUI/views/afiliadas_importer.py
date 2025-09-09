# /build/niceGUI/views/afiliadas_importer.py

import pandas as pd
import io
import re
from typing import List, Dict, Any, Optional
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

            # --- FIX: More robust stripping for the first column ---
            nombre = get_val(0).strip("<").strip('"')
            if not nombre:
                return None

            afiliada_data = {
                "nombre": nombre,
                "apellidos": f"{get_val(2)} {get_val(3)}".strip(),
                "genero": get_val(4),
                "cif": get_val(6),
                "telefono": get_val(7),
                "email": get_val(8),
                "fecha_alta": get_val(16),
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
            }

            cuota_str = get_val(25)
            cuota_match = re.search(r"\|(\d+)", cuota_str)
            iban_raw = get_val(26).replace(" ", "")

            facturacion_data = {
                "cuota": float(cuota_match.group(1)) if cuota_match else 0.0,
                "periodicidad": 12 if "año" in cuota_str else 1,
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
        """Renders the content for all three editable tabs."""
        self._render_afiliadas_panel()
        self._render_pisos_panel()
        self._render_facturacion_panel()

    def _render_afiliadas_panel(self):
        self.afiliadas_panel.clear()
        with self.afiliadas_panel:
            with ui.row().classes(
                "w-full font-bold text-gray-600 gap-2 p-2 bg-gray-50 rounded-t-md"
            ):
                ui.label("Nombre").classes("w-32")
                ui.label("Apellidos").classes("w-48")
                ui.label("CIF/NIE").classes("w-24")
                ui.label("Email").classes("flex-grow")
                ui.label("Teléfono").classes("w-24")
            with ui.scroll_area().classes("w-full h-96"):
                for record in self.records_to_import:
                    with ui.row().classes("w-full items-center gap-2 p-2 border-t"):
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
                        ).classes("w-24")

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
        """Imports the data and shows a final summary dialog with the results."""
        if not self.records_to_import:
            ui.notify("No hay datos para importar.", "warning")
            return

        total_records = len(self.records_to_import)
        success_count, error_messages = 0, []

        with ui.dialog() as progress_dialog, ui.card():
            ui.label("Importando...").classes("text-h6")
            progress = ui.linear_progress(0).classes("w-full")

        progress_dialog.open()

        for i, record in enumerate(self.records_to_import):
            try:
                piso_id = None
                existing_pisos = await self.api.get_records(
                    "pisos", {"direccion": f'eq.{record["piso"]["direccion"]}'}
                )
                if existing_pisos:
                    piso_id = existing_pisos[0]["id"]
                else:
                    new_piso = await self.api.create_record("pisos", record["piso"])
                    if new_piso:
                        piso_id = new_piso["id"]

                if not piso_id:
                    raise Exception("No se pudo crear/encontrar el piso.")

                record["afiliada"]["piso_id"] = piso_id
                cif = record["afiliada"]["cif"]
                if not cif:
                    raise Exception("CIF/NIE es obligatorio.")
                if await self.api.get_records("afiliadas", {"cif": f"eq.{cif}"}):
                    raise Exception(f"La afiliada con CIF {cif} ya existe.")

                new_afiliada = await self.api.create_record(
                    "afiliadas", record["afiliada"]
                )
                if not new_afiliada:
                    raise Exception("No se pudo crear la afiliada.")

                record["facturacion"]["afiliada_id"] = new_afiliada["id"]
                await self.api.create_record("facturacion", record["facturacion"])
                success_count += 1
            except Exception as e:
                error_messages.append(
                    f"Error en {record['afiliada'].get('nombre', 'registro')}: {e}"
                )

            progress.value = (i + 1) / total_records

        progress_dialog.close()

        with ui.dialog() as summary_dialog, ui.card().classes("min-w-[500px]"):
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
                    "Ver Detalles de Errores", icon="report_problem"
                ).classes("w-full"):
                    with ui.scroll_area().classes("w-full h-48 border rounded p-2"):
                        for msg in error_messages:
                            ui.label(msg).classes("text-sm text-negative")

            if not error_messages and success_count == 0:
                ui.markdown(
                    "ℹ️ No se importaron nuevos registros. Es posible que todos ya existieran en la base de datos."
                )

            with ui.row().classes("w-full justify-end"):
                ui.button("Aceptar", on_click=summary_dialog.close)

        summary_dialog.open()

        self.records_to_import = []
        self._render_preview_tabs()
