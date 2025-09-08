# /build/niceGUI/components/relationship_explorer.py

from typing import Dict
from nicegui import ui
from api.client import APIClient
from config import TABLE_INFO, VIEW_INFO


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

    async def show_details(self, record: Dict, source_name: str, calling_view: str):
        """
        Displays parent/child relationships.
        Args:
            record: The data record that was clicked.
            source_name: The name of the table or view the record is from.
            calling_view: A string ('admin' or 'views') to control field visibility.
        """
        self.container.clear()

        # Determine if the source is a view to find the base table
        is_view = calling_view == 'views'
        base_table_name = source_name
        if is_view:
            base_table_name = VIEW_INFO.get(source_name, {}).get("base_table", source_name)

        table_info = TABLE_INFO.get(base_table_name, {})
        primary_key_name = table_info.get("id_field", "id")
        record_id = record.get(primary_key_name) or record.get("id")

        if record_id is None:
            ui.notify(f"Could not find primary key in record from '{source_name}'.", type="warning")
            return

        with self.container:
            ui.label(f"Relationships for record from '{source_name}' (ID: {record_id})").classes("text-h5 mb-2")
            with ui.row().classes("w-full gap-4 flex-wrap"):
                with ui.column().classes("w-full md:flex-1"):
                    ui.label("Registros Padre:").classes("text-h6")
                    await self._display_parent_relations(record, table_info, calling_view)

                with ui.column().classes("w-full md:flex-1"):
                    ui.label("Registros Hijos:").classes("text-h6")
                    await self._display_child_relations(record_id, table_info, calling_view)

    async def _display_parent_relations(self, record: Dict, table_info: Dict, calling_view: str):
        """Fetches and displays parent records, respecting the calling view context."""
        parent_relations = table_info.get("relations", {})
        with ui.card().classes("w-full"):
            if not parent_relations or not any(record.get(fk) for fk in parent_relations):
                ui.label("No se encontraron registros padre.").classes("text-gray-500 p-2")
                return

            for fk_field, rel_info in parent_relations.items():
                if parent_id := record.get(fk_field):
                    parent_table = rel_info["view"]
                    hidden_fields = TABLE_INFO.get(parent_table, {}).get("hidden_fields", [])

                    try:
                        parents = await self.api.get_records(parent_table, filters={"id": f"eq.{parent_id}"})
                        if not parents: continue

                        with ui.expansion(f"Padre en '{parent_table}' (ID: {parent_id})", icon="arrow_upward").classes("w-full"):
                            for key, value in parents[0].items():
                                # In 'admin' view, show all fields. Otherwise, hide configured fields.
                                if calling_view == 'admin' or key not in hidden_fields:
                                    with ui.row():
                                        ui.label(f"{key}:").classes("font-semibold w-32")
                                        ui.label(str(value) if value not in [None, ""] else "-")
                    except Exception as e:
                        ui.notify(f"Error al cargar padre de '{parent_table}': {e}", type="negative")

    async def _display_child_relations(self, record_id: int, table_info: Dict, calling_view: str):
        """Fetches and displays child records, respecting the calling view context."""
        child_relations = table_info.get("child_relations", [])
        with ui.card().classes("w-full"):
            if not child_relations:
                ui.label("No hay relaciones hija configuradas.").classes("text-gray-500 p-2")
                return

            for relation in child_relations:
                child_table, fk = relation["table"], relation["foreign_key"]

                hidden_fields = set(TABLE_INFO.get(child_table, {}).get("hidden_fields", []))
                # In views, also hide the foreign key linking back to the parent.
                if calling_view == 'views':
                    hidden_fields.add(fk)

                try:
                    children = await self.api.get_records(child_table, filters={fk: f"eq.{record_id}"})
                    with ui.expansion(f"Hijos en '{child_table}' ({len(children)})", icon="arrow_downward").classes("w-full"):
                        if not children:
                            ui.label("No se encontraron registros.").classes("text-gray-500 p-2")
                            continue

                        for child in children:
                            with ui.card().classes("w-full my-1"):
                                for key, value in child.items():
                                    # In 'admin' view, show all fields. Otherwise, respect the hidden set.
                                    if calling_view == 'admin' or key not in hidden_fields:
                                        with ui.row():
                                            ui.label(f"{key}:").classes("font-semibold w-32")
                                            ui.label(str(value) if value not in [None, ""] else "-")
                except Exception as e:
                    ui.notify(f"Error al cargar hijos de '{child_table}': {e}", type="negative")