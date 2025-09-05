# /build/niceGUI/components/relationship_explorer.py

from typing import Dict
from nicegui import ui
from api.client import APIClient
from config import TABLE_INFO, VIEW_INFO  # Ensure VIEW_INFO is imported


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
        Displays the parent and child relationships for a given record. This version has
        corrected logic to prevent duplicate rendering.
        """
        self.container.clear()

        base_table_name = source_name
        if is_view:
            view_config = VIEW_INFO.get(source_name, {})
            # Prioritize the explicit 'base_table' link from config.
            # If not present, we cannot reliably find relationships for this view.
            base_table_name = view_config.get("base_table")
            if not base_table_name:
                return  # Exit cleanly if view is not configured for relationship exploration

        table_info = TABLE_INFO.get(base_table_name, {})
        if not table_info:
            return  # Exit if the determined base table has no metadata

        # Find the primary key for the record
        primary_key_name = table_info.get("id_field", "id")
        record_id = record.get(primary_key_name) or record.get("id")

        if record_id is None:
            ui.notify(
                f"Could not find a primary key ('{primary_key_name}' or 'id') in the record from '{source_name}'.",
                type="warning",
            )
            return

        # Render the content exactly once within the cleared container
        with self.container:
            ui.label(
                f"Relationships for record from '{source_name}' (ID: {record_id})"
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
