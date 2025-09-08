# /build/niceGUI/components/relationship_explorer.py

from typing import Dict, List, Set
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
            ui.label(f"Explorador de relaciones de la tabla '{source_name}' (para el registro con ID nº: {record_id})").classes("text-h6 mb-2")
            with ui.row().classes("w-full gap-4 flex-wrap"):
                with ui.column().classes("w-full md:flex-1"):
                    ui.label("Integraciones:").classes("text-h7")
                    await self._display_parent_relations(record, table_info, calling_view)

                with ui.column().classes("w-full md:flex-1"):
                    ui.label("Dependencias:").classes("text-h7")
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
                                if calling_view == 'admin' or key not in hidden_fields:
                                    with ui.row():
                                        ui.label(f"{key}:").classes("font-semibold w-32")
                                        ui.label(str(value) if value not in [None, ""] else "-")
                    except Exception as e:
                        ui.notify(f"Error al cargar padre de '{parent_table}': {e}", type="negative")

    async def _get_replacement_maps(self, records: List[Dict], table_info: Dict) -> Dict:
        """
        Pre-fetches all related records for foreign keys to create replacement maps.
        This is much more performant than fetching one record at a time.
        """
        relations = table_info.get("relations", {})
        if not relations:
            return {}

        replacement_maps = {}
        for fk_field, rel_info in relations.items():
            # Collect all unique IDs for this foreign key from the records
            all_ids: Set[int] = {r.get(fk_field) for r in records if r.get(fk_field) is not None}
            if not all_ids:
                continue

            # Fetch all related records in a single batch
            target_view = rel_info["view"]
            display_field = rel_info["display_field"]
            id_list_str = ",".join(map(str, all_ids))

            related_records = await self.api.get_records(target_view, filters={'id': f'in.({id_list_str})'})

            # Create a simple mapping from ID to the desired display value
            id_to_display_map = {
                r['id']: " ".join(str(r.get(df, "")) for df in display_field.split(",")).strip()
                for r in related_records
            }
            replacement_maps[fk_field] = id_to_display_map

        return replacement_maps

    async def _display_child_relations(self, record_id: int, table_info: Dict, calling_view: str):
        """Fetches and displays child records, replacing foreign keys with display names."""
        child_relations = table_info.get("child_relations", [])
        with ui.card().classes("w-full"):
            if not child_relations:
                ui.label("No hay relaciones hija configuradas.").classes("text-gray-500 p-2")
                return

            for relation in child_relations:
                child_table, fk = relation["table"], relation["foreign_key"]

                try:
                    children = await self.api.get_records(child_table, filters={fk: f"eq.{record_id}"})
                    child_table_info = TABLE_INFO.get(child_table, {})

                    # Pre-fetch replacement data for all foreign keys in the children
                    replacement_maps = await self._get_replacement_maps(children, child_table_info)

                    with ui.expansion(f"Hijos en '{child_table}' ({len(children)})", icon="arrow_downward").classes("w-full"):
                        if not children:
                            ui.label("No se encontraron registros.").classes("text-gray-500 p-2")
                            continue

                        hidden_fields = set(child_table_info.get("hidden_fields", []))
                        if calling_view == 'views':
                            hidden_fields.add(fk)

                        for child in children:
                            with ui.card().classes("w-full my-1"):
                                for key, value in child.items():
                                    if calling_view == 'admin' or key not in hidden_fields:
                                        # If the key is a foreign key with a replacement, show the replacement
                                        if key in replacement_maps:
                                            display_value = replacement_maps[key].get(value, f"ID: {value}")
                                        else:
                                            display_value = value if value not in [None, ""] else "-"

                                        with ui.row():
                                            ui.label(f"{key}:").classes("font-semibold w-32")
                                            ui.label(str(display_value))
                except Exception as e:
                    ui.notify(f"Error al cargar hijos de '{child_table}': {e}", type="negative")