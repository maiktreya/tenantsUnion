import csv
import io
from typing import Dict, Callable, Optional

from nicegui import ui
from api.client import APIClient


def _clean_record(record: Dict) -> Dict:
    """
    Cleans a record by converting empty strings to None and attempting
    to cast numeric strings to int or float. This helps prevent API errors
    when inserting data into typed columns.
    """
    cleaned = {}
    for key, value in record.items():
        if value is None or value == '':
            cleaned[key] = None
        else:
            try:
                # Try to convert to integer first
                cleaned[key] = int(value)
            except (ValueError, TypeError):
                try:
                    # If int conversion fails, try float
                    cleaned[key] = float(value)
                except (ValueError, TypeError):
                    # Otherwise, keep it as a string
                    cleaned[key] = value
    return cleaned


async def import_from_csv(
    api: APIClient,
    table: str,
    file_content: bytes,
) -> bool:
    """
    Imports records from a CSV file's byte content into a specified table.

    Args:
        api: The APIClient instance for database operations.
        table: The name of the target table for the import.
        file_content: The raw byte content of the CSV file.

    Returns:
        True if the import process completes without failing records, False otherwise.
    """
    if not file_content:
        ui.notify('No file content was provided.', type='warning')
        return False

    try:
        # Decode bytes to a string and use StringIO to treat it like an in-memory file
        content_as_string = file_content.decode('utf-8-sig') # Use utf-8-sig to handle BOM
        file_like_object = io.StringIO(content_as_string)

        reader = csv.DictReader(file_like_object)
        records_to_import = list(reader)

        if not records_to_import:
            ui.notify('The CSV file is empty or could not be read.', type='warning')
            return False

        success_count = 0
        failed_count = 0

        # Show a spinner while the import is in progress
        with ui.spinner(size='lg', color='orange'):
            for record in records_to_import:
                cleaned_record = _clean_record(record)
                # The 'id' column should typically be excluded, as the database generates it.
                cleaned_record.pop('id', None)

                result = await api.create_record(table, cleaned_record)
                if result:
                    success_count += 1
                else:
                    failed_count += 1

        # Provide detailed feedback to the user
        if success_count > 0:
            ui.notify(f'Successfully imported {success_count} records.', type='positive')
        if failed_count > 0:
            ui.notify(f'Failed to import {failed_count} records. Please check the data format.', type='negative')

        return failed_count == 0

    except Exception as e:
        ui.notify(f'An error occurred during the import process: {str(e)}', type='negative')
        return False


class CSVImporterDialog:
    """A reusable dialog for handling CSV file uploads and triggering the import."""

    def __init__(
        self,
        api: APIClient,
        table_name: str,
        on_success: Optional[Callable] = None,
    ):
        self.api = api
        self.table_name = table_name
        self.on_success = on_success
        self.dialog = None
        self.uploaded_file_content = None

    def open(self):
        """Opens the import dialog window."""
        self.dialog = ui.dialog()

        with self.dialog, ui.card().classes("w-96"):
            ui.label(f'Importar CSV a "{self.table_name}"').classes("text-h6")
            ui.markdown(
                "**Importante:** El archivo CSV debe tener una fila de encabezado "
                "con nombres de columna que coincidan **exactamente** con los campos de la tabla."
            ).classes("text-caption text-gray-600")

            ui.upload(
                on_upload=self._handle_upload,
                auto_upload=True,
                max_files=1,
                label="Seleccionar archivo .csv",
            ).props('accept=".csv"')

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")
                ui.button("Importar", on_click=self._start_import).props("color=orange-600")

        self.dialog.open()

    def _handle_upload(self, e):
        """Callback function to store the content of the uploaded file."""
        self.uploaded_file_content = e.content.read()
        ui.notify(f"Archivo '{e.name}' cargado y listo para importar.", type='info')

    async def _start_import(self):
        """Validates and initiates the CSV import process."""
        if not self.table_name:
            ui.notify("No table has been selected.", type='warning')
            return

        if not self.uploaded_file_content:
            ui.notify("Por favor, suba un archivo CSV primero.", type='warning')
            return

        # Close the dialog before starting the potentially long-running import
        self.dialog.close()

        success = await import_from_csv(
            self.api,
            self.table_name,
            self.uploaded_file_content,
        )

        # If the import was successful and a callback is provided, run it (e.g., to refresh the data table)
        if success and self.on_success:
            await self.on_success()
