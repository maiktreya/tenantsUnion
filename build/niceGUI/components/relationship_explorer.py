# /build/niceGUI/components/relationship_explorer.py

from typing import Dict
from nicegui import ui
from api.client import APIClient
from config import TABLE_INFO


class RelationshipExplorer:
    """A reusable component to display parent and child relationships for a given record."""

    def __init__(self, api_client: APIClient, container: ui.column):
        """
        Args:
            api_client: The API client for database operations.
            container: The NiceGUI container where the details will be rendered.
        """
        self.api = api_client
        self.container = container

    async def show_details(self, record: Dict, source_name: str, is_view: bool):
        """
        Displays the parent and child relationships for a given record.

        Args:
            record: The data record that was clicked.
            source_name: The name of the table or view the record belongs to.
            is_view: A boolean indicating if the source is a view.
        """
        self.container.clear()

        # Determine the base table and its configuration
        base_table_name = (
            source_name[2:] if is_view and source_name.startswith("v_") else source_name
        )
        table_info = TABLE_INFO.get(base_table_name, {})

        # Find the primary key for the record
        primary_key_name = table_info.get("id_field", "id")
        record_id = record.get(primary_key_name) or record.get("id")

        if record_id is None:
            ui.notify(
                f"La vista '{source_name}' no contiene un campo '{primary_key_name}' o 'id' para buscar relaciones.",
                type="warning",
            )
            return

        with self.container:
            ui.label(
                f"Relaciones para el registro de '{source_name}' (ID: {record_id})"
            ).classes("text-h5 mb-2")
            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("w-1/2"):
                    await self._display_parent_relations(record, table_info)
                with ui.column().classes("w-1/2"):
                    await self._display_child_relations(record_id, table_info)

    async def _display_parent_relations(self, record: Dict, table_info: Dict):
        """Fetches and displays parent records."""
        parent_relations = table_info.get("relations")
        if not parent_relations:
            return

        ui.label("Registros Padre:").classes("text-h6")
        with ui.card().classes("w-full"):
            for fk_field, rel_info in parent_relations.items():
                parent_id = record.get(fk_field)
                if parent_id is None:
                    continue
                parent_table = rel_info["view"]
                try:
                    parents = await self.api.get_records(
                        parent_table, filters={"id": f"eq.{parent_id}"}
                    )
                    if not parents:
                        continue
                    with ui.expansion(
                        f"Padre en '{parent_table}' (ID: {parent_id})",
                        icon="arrow_upward",
                    ).classes("w-full"):
                        for key, value in parents[0].items():
                            with ui.row():
                                ui.label(f"{key}:").classes("font-semibold w-32")
                                # MODIFIED: Coerce None and empty strings to '-'
                                display_value = (
                                    value if value is not None and value != "" else "-"
                                )
                                ui.label(str(display_value))
                except Exception as e:
                    ui.notify(
                        f"Error al cargar padre de '{parent_table}': {str(e)}",
                        type="negative",
                    )

    async def _display_child_relations(self, record_id: int, table_info: Dict):
        """Fetches and displays child records."""
        child_relations = table_info.get("child_relations", [])
        child_relations = (
            [child_relations] if isinstance(child_relations, dict) else child_relations
        )
        if not child_relations:
            return

        ui.label("Registros Hijos:").classes("text-h6")
        with ui.card().classes("w-full"):
            for relation in child_relations:
                child_table, fk = relation["table"], relation["foreign_key"]
                try:
                    children = await self.api.get_records(
                        child_table, filters={fk: f"eq.{record_id}"}
                    )
                    with ui.expansion(
                        f"Hijos en '{child_table}' ({len(children)})",
                        icon="arrow_downward",
                    ).classes("w-full"):
                        if not children:
                            ui.label("No se encontraron registros.").classes(
                                "text-gray-500 p-2"
                            )
                            continue
                        for child in children:
                            with ui.card().classes("w-full my-1"):
                                for key, value in child.items():
                                    with ui.row():
                                        ui.label(f"{key}:").classes(
                                            "font-semibold w-32"
                                        )
                                        # MODIFIED: Coerce None and empty strings to '-'
                                        display_value = (
                                            value
                                            if value is not None and value != ""
                                            else "-"
                                        )
                                        ui.label(str(display_value))
                except Exception as e:
                    ui.notify(
                        f"Error al cargar hijos de '{child_table}': {str(e)}",
                        type="negative",
                    )
