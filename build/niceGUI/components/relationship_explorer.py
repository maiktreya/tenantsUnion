from typing import Dict, List, Set, Optional
from nicegui import ui
from api.client import APIClient
from config import TABLE_INFO, VIEW_INFO


class RelationshipExplorer:
    """
    A reusable component to display multi-level parent and child relationships for a given record,
    driven by a nested configuration in TABLE_INFO.
    """

    def __init__(self, api_client: APIClient, container: ui.column):
        """
        Args:
            api_client: The API client for database operations.
            container: The NiceGUI container where the details will be rendered.
        """
        self.api = api_client
        self.container = container
        self.calling_view = "admin"  # Default view context

    async def show_details(self, record: Dict, source_name: str, calling_view: str):
        """
        Displays a multi-level tree of parent and child relationships.

        Args:
            record: The data record that was clicked.
            source_name: The name of the table or view the record is from.
            calling_view: A string ('admin' or 'views') to control field visibility.
        """
        self.container.clear()
        self.calling_view = calling_view

        # Determine the base table if the source is a view
        base_table_name = (
            VIEW_INFO.get(source_name, {}).get("base_table", source_name)
            if self.calling_view == "views"
            else source_name
        )
        table_info = TABLE_INFO.get(base_table_name, {})
        primary_key_name = table_info.get("id_field", "id")
        record_id = record.get(primary_key_name)

        if record_id is None:
            ui.notify(
                f"Could not find primary key in record from '{source_name}'.",
                type="warning",
            )
            return

        with self.container:
            ui.label(
                f"Explorador de Relaciones para '{base_table_name}' (ID: {record_id})"
            ).classes("text-h6 mb-2")
            with ui.row().classes("w-full gap-4 flex-wrap"):

                # Display Parent (Upstream) Relationships
                with ui.column().classes("w-full md:flex-1"):
                    ui.label("Genealogía (Padres):").classes("text-lg font-semibold")
                    with ui.card().classes("w-full"):
                        parent_relations = table_info.get("relations", {})
                        if not parent_relations:
                            ui.label("No hay relaciones padre configuradas.").classes(
                                "text-gray-500 p-2"
                            )
                        else:
                            await self._render_parent_level(record, parent_relations, 0)

                # Display Child (Downstream) Relationships
                with ui.column().classes("w-full md:flex-1"):
                    ui.label("Dependencias (Hijos):").classes("text-lg font-semibold")
                    with ui.card().classes("w-full"):
                        child_relations = table_info.get("child_relations", [])
                        if not child_relations:
                            ui.label("No hay relaciones hija configuradas.").classes(
                                "text-gray-500 p-2"
                            )
                        else:
                            await self._render_child_level(
                                record_id, child_relations, 0
                            )

    async def _render_parent_level(
        self, child_record: Dict, relations: Dict, level: int
    ):
        """Recursively fetches and displays parent and grandparent records."""
        indent_class = f"pl-{level * 4}"  # Indent deeper for each level
        if not any(child_record.get(fk) for fk in relations):
            ui.label("No se encontraron registros padre.").classes(
                f"text-gray-500 p-2 {indent_class}"
            )
            return

        for fk_field, rel_info in relations.items():
            parent_id = child_record.get(fk_field)
            if not parent_id:
                continue

            parent_table = rel_info.get("view")
            if not parent_table:
                continue

            try:
                parents = await self.api.get_records(
                    parent_table, filters={"id": f"eq.{parent_id}"}
                )
                if not parents:
                    continue

                parent_record = parents[0]
                parent_info = TABLE_INFO.get(parent_table, {})
                hidden_fields = set(parent_info.get("hidden_fields", []))

                with ui.expansion(
                    f"Padre en '{parent_table}' (ID: {parent_id})", icon="arrow_upward"
                ).classes(f"w-full {indent_class}"):
                    # Display the fields of the current parent
                    self._display_record_fields(parent_record, hidden_fields)

                    # --- RECURSIVE CALL for Grandparents ---
                    if "relations" in rel_info and rel_info["relations"]:
                        await self._render_parent_level(
                            parent_record, rel_info["relations"], level + 1
                        )

            except Exception as e:
                ui.notify(
                    f"Error al cargar padre de '{parent_table}': {e}", type="negative"
                )

    async def _render_child_level(
        self, parent_id: int, relations: List[Dict], level: int
    ):
        """Recursively fetches and displays child and grandchild records."""
        indent_class = f"pl-{level * 4}"  # Indent deeper for each level

        for relation in relations:
            child_table = relation["table"]
            fk = relation["foreign_key"]
            child_table_info = TABLE_INFO.get(child_table, {})
            hidden_fields = set(child_table_info.get("hidden_fields", []))

            try:
                children = await self.api.get_records(
                    child_table, filters={fk: f"eq.{parent_id}"}
                )

                with ui.expansion(
                    f"Hijos en '{child_table}' ({len(children)})", icon="arrow_downward"
                ).classes(f"w-full {indent_class}"):
                    if not children:
                        ui.label("No se encontraron registros.").classes(
                            "text-gray-500 p-2"
                        )
                        continue

                    # Pre-fetch data for replacing foreign keys with readable names
                    replacement_maps = await self._get_replacement_maps(
                        children, child_table_info
                    )

                    for child in children:
                        child_id = child.get(child_table_info.get("id_field", "id"))
                        card_title = f"{child_table.rstrip('s')} ID: {child_id}"

                        with ui.card().classes("w-full my-1"):
                            ui.label(card_title).classes("text-md font-semibold mb-2")
                            self._display_record_fields(
                                child, hidden_fields, replacement_maps
                            )

                        # --- RECURSIVE CALL for Grandchildren ---
                        if (
                            "child_relations" in relation
                            and relation["child_relations"]
                            and child_id
                        ):
                            await self._render_child_level(
                                child_id, relation["child_relations"], level + 1
                            )

            except Exception as e:
                ui.notify(
                    f"Error al cargar hijos de '{child_table}': {e}", type="negative"
                )

    def _display_record_fields(
        self,
        record: Dict,
        hidden_fields: Set[str],
        replacement_maps: Optional[Dict] = None,
    ):
        """Helper to consistently display the key-value pairs of a record."""
        replacement_maps = replacement_maps or {}
        for key, value in record.items():
            if self.calling_view == "admin" or key not in hidden_fields:
                display_value = value
                # If the key is a foreign key with a replacement, show the readable name
                if key in replacement_maps and value is not None:
                    display_value = replacement_maps[key].get(value, f"ID: {value}")
                elif value in [None, ""]:
                    display_value = "-"

                with ui.row().classes("w-full text-sm"):
                    ui.label(f"{key}:").classes("font-semibold w-32 opacity-70")
                    ui.label(str(display_value))

    async def _get_replacement_maps(
        self, records: List[Dict], table_info: Dict
    ) -> Dict:
        """
        Pre-fetches all related records for foreign keys to create replacement maps.
        This is much more performant than fetching one record at a time.
        """
        relations = table_info.get("relations", {})
        if not relations:
            return {}

        replacement_maps = {}
        for fk_field, rel_info in relations.items():
            all_ids: Set[int] = {
                r.get(fk_field) for r in records if r.get(fk_field) is not None
            }
            if not all_ids:
                continue

            target_view = rel_info["view"]
            display_field = rel_info["display_field"]
            id_list_str = ",".join(map(str, all_ids))

            related_records = await self.api.get_records(
                target_view, filters={"id": f"in.({id_list_str})"}
            )

            # Create a mapping from ID to the desired display value
            id_to_display_map = {
                r["id"]: " ".join(
                    str(r.get(df, "")) for df in display_field.split(",")
                ).strip()
                for r in related_records
            }
            replacement_maps[fk_field] = id_to_display_map

        return replacement_maps
