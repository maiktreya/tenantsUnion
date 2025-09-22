import csv
import io
from typing import List, Dict
from nicegui import ui


def export_to_csv(records: List[Dict], filename: str):
    """Export records to CSV file"""
    if not records:
        ui.notify("No hay datos para exportar", type="warning")
        return

    try:
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

        # Get CSV content
        csv_content = output.getvalue()

        # Trigger download
        ui.download(csv_content.encode("utf-8"), filename)
        ui.notify(f"Se exportaron {len(records)} registros", type="positive")

    except Exception as e:
        ui.notify(f"Error al exportar: {str(e)}", type="negative")


def export_to_json(records: List[Dict], filename: str):
    """Export records to JSON file"""
    import json

    if not records:
        ui.notify("No hay datos para exportar", type="warning")
        return

    try:
        # Create JSON content
        json_content = json.dumps(records, indent=2, ensure_ascii=False)

        # Trigger download
        ui.download(json_content.encode("utf-8"), filename)
        ui.notify(f"Se exportaron {len(records)} registros", type="positive")

    except Exception as e:
        ui.notify(f"Error al exportar: {str(e)}", type="negative")
