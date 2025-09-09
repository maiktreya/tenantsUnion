# /build/niceGUI/views/afiliadas_importer.py

import pandas as pd
import io
import re
from typing import List, Dict, Any, Optional
from nicegui import ui, events
from api.client import APIClient
# Note: We no longer need DataTable or a separate ImporterState for this view
from state.base import BaseTableState


class AfiliadasImporterView:
    """A view to import new 'afiliadas' from a WordPress CSV export with in-place editing."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        # This list will hold the structured data that the UI will bind to and that will be imported
        self.records_to_import: List[Dict] = []
        self.preview_container = None # The UI container for the editable grid

    def create(self) -> ui.column:
        """Create the UI for the CSV importer view."""
        container = ui.column().classes("w-full p-4 gap-4")
        with container:
            ui.label("Importar Nuevas Afiliadas desde CSV").classes("text-h4")
            ui.markdown(
                "Sube el archivo CSV. Los datos se mostrarán en una tabla editable a continuación. "
                "Puedes corregir cualquier campo antes de iniciar la importación final."
            )

            with ui.row().classes("w-full gap-4 items-center"):
                ui.upload(
                    on_upload=self._handle_upload,
                    auto_upload=True,
                    label="Subir archivo afiliacion.csv",
                ).props('accept=".csv"')

                ui.button(
                    "Iniciar Importación",
                    icon="upload",
                    on_click=self._start_import,
                ).props("color=orange-600")

            ui.separator().classes("mt-4")
            
            # This container will hold our dynamic, editable table
            self.preview_container = ui.column().classes("w-full")

        return container
    
    def _handle_upload(self, e: events.UploadEventArguments):
        """Handle the file upload, parse data, and render the editable grid."""
        try:
            content = e.content.read()
            raw_dataframe = pd.read_csv(
                io.BytesIO(content), header=None, quotechar='"', sep=","
            )
            
            self.records_to_import = []
            for _, row in raw_dataframe.iterrows():
                nested_record = self._transform_row(row)
                if nested_record:
                    self.records_to_import.append(nested_record)

            self._render_editable_grid() # Render the new editable UI
            ui.notify("Archivo procesado. Ya puedes editar los datos en la tabla.", type="positive")

        except Exception as ex:
            ui.notify(f"Error al leer el archivo: {ex}", type="negative")
            self.records_to_import = []
            self.preview_container.clear()


    def _transform_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Transforms a single row into a structured dictionary. (Same as before)"""
        try:
            def get_val(index):
                raw_value = row.get(index)
                return "" if pd.isna(raw_value) else str(raw_value).strip()

            nombre = get_val(0).lstrip('<"')
            if not nombre: return None

            afiliada_data = {
                "nombre": nombre, "apellidos": f"{get_val(2)} {get_val(3)}".strip(),
                "genero": get_val(4), "cif": get_val(6), "telefono": get_val(7),
                "email": get_val(8), "fecha_alta": get_val(16), "regimen": get_val(17),
                "estado": "Alta", "piso_id": None, # Will be set after piso creation
            }
            
            piso_data = {
                "direccion": re.sub(r"\s+", " ", f"{get_val(9)} {get_val(10)}, {get_val(11)} {get_val(12)}, {get_val(14)}, {get_val(13)}".strip(", ")).strip(),
                "municipio": get_val(13), "cp": int(get_val(14)) if get_val(14).isdigit() else None,
            }

            cuota_str = get_val(25)
            cuota_match = re.search(r"\|(\d+)", cuota_str)
            iban_raw = get_val(26).replace(" ", "")

            facturacion_data = {
                "cuota": float(cuota_match.group(1)) if cuota_match else 0.0,
                "periodicidad": 12 if "año" in cuota_str else 1,
                "forma_pago": "Domiciliación" if iban_raw else "Otro",
                "iban": iban_raw.upper() if iban_raw else None, "afiliada_id": None,
            }

            return {"piso": piso_data, "afiliada": afiliada_data, "facturacion": facturacion_data}
        except Exception as e:
            print(f"Skipping row due to parsing error: {e}")
            return None

    def _render_editable_grid(self):
        """Dynamically renders an editable grid bound to the records_to_import data."""
        self.preview_container.clear()
        with self.preview_container:
            if not self.records_to_import:
                ui.label("No se encontraron datos válidos para previsualizar.").classes("text-warning")
                return

            ui.label("Previsualización de Datos a Importar").classes("text-h6 mb-2")
            
            # Create a header row
            with ui.row().classes('w-full font-bold text-gray-600 gap-2 mb-1'):
                ui.label('Nombre').classes('w-32')
                ui.label('Apellidos').classes('w-48')
                ui.label('CIF/NIE').classes('w-24')
                ui.label('Dirección').classes('flex-grow')
                ui.label('Cuota (€)').classes('w-20')
                ui.label('IBAN').classes('w-48')

            # Create an editable row for each record
            with ui.scroll_area().classes('w-full h-96 border rounded-md p-2'):
                for record in self.records_to_import:
                    with ui.row().classes('w-full items-center gap-2 mb-2'):
                        # Bind each input directly to the dictionary values
                        ui.input(label=None).bind_value(record['afiliada'], 'nombre').classes('w-32')
                        ui.input(label=None).bind_value(record['afiliada'], 'apellidos').classes('w-48')
                        ui.input(label=None).bind_value(record['afiliada'], 'cif').classes('w-24')
                        ui.input(label=None).bind_value(record['piso'], 'direccion').classes('flex-grow')
                        ui.number(label=None, format='%.2f').bind_value(record['facturacion'], 'cuota').classes('w-20')
                        ui.input(label=None).bind_value(record['facturacion'], 'iban').classes('w-48')

    async def _start_import(self):
        """Imports the data, which may have been edited by the user in the UI."""
        if not self.records_to_import:
            ui.notify("No hay datos para importar.", "warning")
            return

        success_count = 0
        error_messages = []
        
        with ui.dialog() as dialog, ui.card():
            ui.label("Importando...").classes("text-h6")
            progress = ui.linear_progress(0).classes("w-full")
        
        dialog.open()

        for i, record in enumerate(self.records_to_import):
            try:
                # The import logic remains the same, but now uses the (potentially edited) data
                piso_id = None
                existing_pisos = await self.api.get_records("pisos", {"direccion": f'eq.{record["piso"]["direccion"]}'})
                piso_id = existing_pisos[0]["id"] if existing_pisos else (await self.api.create_record("pisos", record["piso"]))["id"]
                
                if not piso_id: raise Exception("No se pudo crear/encontrar el piso.")

                record["afiliada"]["piso_id"] = piso_id
                cif = record["afiliada"]["cif"]
                if not cif: raise Exception("CIF/NIE es obligatorio.")

                if await self.api.get_records("afiliadas", {"cif": f'eq.{cif}'}):
                    raise Exception(f"La afiliada con CIF {cif} ya existe.")

                new_afiliada = await self.api.create_record("afiliadas", record["afiliada"])
                if not new_afiliada: raise Exception("No se pudo crear la afiliada.")

                record["facturacion"]["afiliada_id"] = new_afiliada["id"]
                await self.api.create_record("facturacion", record["facturacion"])
                
                success_count += 1
            except Exception as e:
                error_messages.append(f"Error en {record['afiliada'].get('nombre', 'registro')}: {e}")
            
            progress.value = (i + 1) / len(self.records_to_import)

        dialog.close()
        
        if success_count > 0: ui.notify(f"Se importaron {success_count} afiliadas.", "positive")
        for msg in error_messages: ui.notify(msg, "negative")
        if not error_messages and success_count == 0: ui.notify("No se importaron nuevos registros.", "info")
        
        self.records_to_import = []
        self._render_editable_grid() # Clear the grid
