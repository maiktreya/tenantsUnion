# /build/niceGUI/views/afiliadas_importer.py

import pandas as pd
import io
import re
from typing import List, Dict, Any
from nicegui import ui, events
from api.client import APIClient


class AfiliadasImporterView:
    """A view to import new 'afiliadas' from a WordPress CSV export."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.raw_dataframe = None
        self.preview_data = []
        self.preview_container = None

    def create(self) -> ui.column:
        """Create the UI for the CSV importer view."""
        container = ui.column().classes("w-full p-4 gap-4")
        with container:
            ui.label("Importar Nuevas Afiliadas desde CSV").classes("text-h4")
            ui.markdown(
                "Esta herramienta está diseñada para procesar el CSV exportado desde el "
                "formulario de afiliación de WordPress. Sube el archivo, revisa los "
                "datos procesados y luego inicia la importación."
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

            self.preview_container = ui.column().classes("w-full mt-4")
        return container

    def _handle_upload(self, e: events.UploadEventArguments):
        """Handle the file upload and trigger the parsing and preview."""
        try:
            content = e.content.read()
            # The CSV seems to be quote-less and header-less
            self.raw_dataframe = pd.read_csv(
                io.BytesIO(content), header=None, quotechar='"', sep=","
            )
            self._parse_and_preview()
            ui.notify(
                "Archivo procesado. Revisa los datos antes de importar.",
                type="positive",
            )
        except Exception as ex:
            ui.notify(f"Error al leer el archivo: {ex}", type="negative")

    def _parse_and_preview(self):
        """Parse the raw DataFrame and generate a preview for the UI."""
        if self.raw_dataframe is None:
            return

        self.preview_data = []
        for _, row in self.raw_dataframe.iterrows():
            processed_record = self._transform_row(row)
            if processed_record:
                self.preview_data.append(processed_record)

        self._display_preview()

    def _transform_row(self, row: pd.Series) -> Dict[str, Any]:
        """Transforms a single row of the DataFrame into structured data for insertion."""

        # --- CORRECTED HELPER FUNCTION ---
        # Helper to safely get data, convert to string, then strip whitespace.
        def get_val(index):
            raw_value = row.get(index)
            if pd.isna(raw_value):
                return ""
            return str(raw_value).strip()

        # --- 1. Extract and clean data for 'pisos' table ---
        direccion_completa = (
            f"{get_val(9)} {get_val(10)}, "
            f"{get_val(11)} {get_val(12)}, "
            f"{get_val(14)}, {get_val(13)}"
        ).strip(", ")

        piso_data = {
            "direccion": re.sub(r"\s+", " ", direccion_completa).strip(),
            "municipio": get_val(13),
            "cp": int(get_val(14)) if get_val(14).isdigit() else None,
        }

        # --- 2. Extract and clean data for 'afiliadas' table ---
        apellidos = f"{get_val(2)} {get_val(3)}".strip()
        afiliada_data = {
            "nombre": get_val(0),
            "apellidos": apellidos,
            "genero": get_val(4),
            "cif": get_val(6),
            "telefono": get_val(7),
            "email": get_val(8),
            "fecha_alta": get_val(16),
            "regimen": get_val(17),
            "estado": "Alta",  # Default state for new members
        }

        # --- 3. Extract and clean data for 'facturacion' table ---
        cuota_str = get_val(24)
        cuota_match = re.search(r"\|(\d+)", cuota_str)
        cuota_valor = float(cuota_match.group(1)) if cuota_match else 0.0

        forma_pago = "Domiciliación" if get_val(25) else "Otro"

        # Clean IBAN
        iban_raw = get_val(25).replace(" ", "")
        iban = iban_raw.upper() if iban_raw else None

        facturacion_data = {
            "cuota": cuota_valor,
            "periodicidad": (
                12 if "año" in cuota_str else 1
            ),  # Simple logic for periodicity
            "forma_pago": forma_pago,
            "iban": iban,
        }

        return {
            "piso": piso_data,
            "afiliada": afiliada_data,
            "facturacion": facturacion_data,
        }

    def _display_preview(self):
        """Renders the preview data in a table in the UI."""
        self.preview_container.clear()
        with self.preview_container:
            ui.label("Previsualización de Datos a Importar").classes("text-h6")

            if not self.preview_data:
                ui.label("No se encontraron datos válidos para importar.").classes(
                    "text-warning"
                )
                return

            columns = [
                {
                    "name": "nombre",
                    "label": "Nombre",
                    "field": "nombre",
                    "align": "left",
                },
                {
                    "name": "apellidos",
                    "label": "Apellidos",
                    "field": "apellidos",
                    "align": "left",
                },
                {
                    "name": "direccion",
                    "label": "Dirección",
                    "field": "direccion",
                    "align": "left",
                },
                {
                    "name": "cuota",
                    "label": "Cuota (€)",
                    "field": "cuota",
                    "align": "right",
                },
                {"name": "iban", "label": "IBAN", "field": "iban", "align": "left"},
            ]

            table_rows = []
            for item in self.preview_data:
                table_rows.append(
                    {
                        "nombre": item["afiliada"]["nombre"],
                        "apellidos": item["afiliada"]["apellidos"],
                        "direccion": item["piso"]["direccion"],
                        "cuota": item["facturacion"]["cuota"],
                        "iban": item["facturacion"]["iban"] or "---",
                    }
                )

            ui.table(columns=columns, rows=table_rows, row_key="nombre").classes(
                "w-full"
            )

    async def _start_import(self):
        """Starts the process of importing the previewed data into the database."""
        if not self.preview_data:
            ui.notify(
                "No hay datos para importar. Por favor, sube un archivo CSV.",
                type="warning",
            )
            return

        success_count = 0
        failed_count = 0

        with ui.dialog() as dialog, ui.card():
            ui.label("Importando...").classes("text-h6")
            progress = ui.linear_progress(0).classes("w-full")

        dialog.open()

        for i, record in enumerate(self.preview_data):
            try:
                # --- Step 1: Create or get 'piso' ---
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
                    raise Exception("No se pudo crear o encontrar el piso.")

                # --- Step 2: Create 'afiliada' ---
                record["afiliada"]["piso_id"] = piso_id

                # Prevent duplicates by checking CIF/NIF
                cif = record["afiliada"]["cif"]
                existing_afiliada = await self.api.get_records(
                    "afiliadas", {"cif": f"eq.{cif}"}
                )
                if existing_afiliada:
                    raise Exception(f"La afiliada con CIF {cif} ya existe.")

                new_afiliada = await self.api.create_record(
                    "afiliadas", record["afiliada"]
                )
                if not new_afiliada:
                    raise Exception("No se pudo crear la afiliada.")

                # --- Step 3: Create 'facturacion' ---
                record["facturacion"]["afiliada_id"] = new_afiliada["id"]
                new_facturacion = await self.api.create_record(
                    "facturacion", record["facturacion"]
                )
                if not new_facturacion:
                    # This is not critical, so we'll just log it
                    print(
                        f"Warning: Could not create billing for {new_afiliada['nombre']}"
                    )

                success_count += 1
            except Exception as e:
                failed_count += 1
                ui.notify(
                    f"Error importando a {record['afiliada']['nombre']}: {e}",
                    type="negative",
                )

            progress.value = (i + 1) / len(self.preview_data)

        dialog.close()

        if success_count > 0:
            ui.notify(
                f"Se importaron {success_count} afiliadas exitosamente.",
                type="positive",
            )
        if failed_count > 0:
            ui.notify(
                f"Fallaron {failed_count} registros durante la importación.",
                type="negative",
            )

        # Clear the view for the next import
        self.preview_container.clear()
        self.preview_data = []
        self.raw_dataframe = None
