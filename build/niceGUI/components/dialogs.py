# enhanced_dialogs.py

from typing import Dict, Optional, Callable
from nicegui import ui, app
from api.client import APIClient  # Assuming your APIClient is here
from config import TABLE_INFO      # Assuming your TABLE_INFO config is here

# --- EXAMPLE TABLE_INFO STRUCTURE ---
# To make this new dialog work, your TABLE_INFO should be structured
# like this, with a 'fields' list defining what to show in the form.

# TABLE_INFO = {
#     'my_table': {
#         'id_field': 'id',
#         'fields': ['nombre', 'descripcion', 'fecha_inicio', 'cliente_id'],
#         'relations': {
#             'cliente_id': {
#                 'view': 'clientes_view',      # The API view to query for options
#                 'display_field': 'nombre',    # The field to show in the dropdown
#             }
#         }
#     },
#     # ... other tables
# }

class RecordDialog:
    """
    Dialog for creating/editing records. Fields are now driven exclusively
    by the 'fields' list in the TABLE_INFO configuration for predictability.
    Relational fields are now filterable comboboxes for improved UX.
    """

    def __init__(
        self,
        api: APIClient,
        table: str,
        record: Optional[Dict] = None,
        mode: str = "create",
        on_success: Optional[Callable] = None,
    ):
        self.api = api
        self.table = table
        self.record = record or {}
        self.mode = mode
        self.on_success = on_success
        self.dialog = None
        self.inputs = {}

    async def open(self):
        """Opens the dialog asynchronously."""
        self.dialog = ui.dialog()

        with self.dialog, ui.card().classes("w-96"):
            title = (
                f"Crear nuevo registro en {self.table}"
                if self.mode == "create"
                else f'Editar registro #{self.record.get("id")} de {self.table}'
            )
            ui.label(title).classes("text-h6")

            await self._create_inputs()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")
                ui.button("Guardar", on_click=self._save).props("color=orange-600")

        self.dialog.open()

    def _get_fields(self) -> list:
        """
        Gets the list of fields to display, using the 'fields' key
        in TABLE_INFO as the single source of truth.
        """
        table_info = TABLE_INFO.get(self.table, {})

        # The 'fields' list in TABLE_INFO is now mandatory for clarity.
        if 'fields' not in table_info:
            ui.notify(f"Configuration error: No 'fields' list defined for table '{self.table}'.", type='negative')
            return []

        fields = set(table_info['fields'])
        id_field = table_info.get("id_field", "id")

        # In create mode, always remove the primary key field(s).
        if self.mode == "create":
            for key in str(id_field).split(","):
                fields.discard(key.strip()) # Use discard to avoid errors if key isn't present.

        return list(fields)

    async def _create_inputs(self):
        """
        Creates input fields based on TABLE_INFO. Relational fields
        are now rendered as server-side filterable dropdowns.
        """
        table_info = TABLE_INFO.get(self.table, {})
        relations = table_info.get("relations", {})
        fields = self._get_fields()

        # Sort fields to show relations first, then others alphabetically.
        fields.sort(key=lambda f: (0 if f in relations else 1, f))

        for field in fields:
            value = self.record.get(field)

            # --- RENDER RELATIONAL FIELDS (FOREIGN KEYS) ---
            if field in relations:
                relation = relations[field]
                view_name = relation["view"]
                display_field = relation["display_field"]

                # Helper to format the display label from a record object.
                def get_disp_label(r):
                    if "," in display_field:
                        return " ".join(str(r.get(df.strip(), "")) for df in display_field.split(",")).strip()
                    return str(r.get(display_field, f"ID: {r['id']}"))

                # Create a select element with input enabled for filtering.
                select_element = ui.select(
                    options={},
                    label=field.replace("_", " ").title(),
                    value=value,
                    with_input=True,
                ).classes("w-full")
                self.inputs[field] = select_element

                async def update_options(e):
                    """Event handler for the 'filter' event, called when the user types."""
                    search_term = e.args or ""
                    try:
                        # Fetch filtered records from the API.
                        # Your API must support a search parameter (e.g., 'q', 'search').
                        params = {'search': search_term} if search_term else {}
                        records = await self.api.get_records(view_name, params=params)
                        new_options = {r["id"]: get_disp_label(r) for r in records}
                        select_element.set_options(new_options, clear=True)
                    except Exception as ex:
                        ui.notify(f"Error filtering options: {ex}", type="negative")

                select_element.on('filter', update_options)

                # In edit mode, pre-load the currently selected record's option.
                if self.mode == 'edit' and value is not None:
                    try:
                        initial_record = await self.api.get_record(view_name, value)
                        if initial_record:
                            select_element.set_options({initial_record['id']: get_disp_label(initial_record)})
                            select_element.set_value(value)
                    except Exception as e:
                        ui.notify(f"Could not load initial value for {field}: {e}", type='warning')

            # --- RENDER STANDARD FIELDS ---
            else:
                lower = field.lower()
                # Infer common input types based on field name or value type.
                if "nota" in lower or "descripcion" in lower or "comentario" in lower:
                    self.inputs[field] = ui.textarea(label=field.replace("_", " ").title(), value=value or '').classes("w-full")
                elif "email" in lower:
                    self.inputs[field] = ui.input(label=field.replace("_", " ").title(), value=value or '').props("type=email").classes("w-full")
                elif "fecha" in lower:
                    with ui.input(label=field.replace("_", " ").title(), value=str(value or '')[:10]).classes('w-full') as date_input:
                        with date_input.add_slot('append'):
                            ui.icon('edit_calendar').on('click', lambda: menu.open()).classes('cursor-pointer')
                        with ui.menu() as menu:
                            ui.date().bind_value(date_input)
                    self.inputs[field] = date_input
                elif isinstance(value, int) or isinstance(value, float):
                    self.inputs[field] = ui.number(label=field.replace("_", " ").title(), value=value).classes("w-full")
                else:
                    self.inputs[field] = ui.input(label=field.replace("_", " ").title(), value=value or '').classes("w-full")

    async def _save(self):
        """Saves the record (create or update) to the database via the API."""
        try:
            data = {field: self.inputs[field].value for field in self.inputs}

            # Filter out empty values, but allow False and 0
            payload = {k: v for k, v in data.items() if v is not None and v != ''}

            if self.mode == "create":
                result = await self.api.create_record(self.table, payload)
                ui.notify("Registro creado con éxito", type="positive")
            else:
                record_id = self.record.get("id")
                # Send only the fields that have actually changed.
                changed_data = {
                    k: v for k, v in payload.items()
                    if str(v) != str(self.record.get(k, ''))
                }
                if not changed_data:
                    ui.notify("No se realizaron cambios", type="info")
                    self.dialog.close()
                    return

                result = await self.api.update_record(self.table, record_id, changed_data)
                ui.notify("Registro actualizado con éxito", type="positive")

            self.dialog.close()
            if self.on_success:
                await self.on_success()

        except Exception as e:
            ui.notify(f"Error al guardar: {e}", type="negative")

class EnhancedRecordDialog(RecordDialog):
    """
    This class is kept for backwards compatibility; it is just an alias
    for the fully dynamic RecordDialog now.
    """
    pass


class ConflictNoteDialog:
    """
    Dialog for adding or editing conflict notes. This is a specialized
    dialog and does not use the dynamic generation of RecordDialog.
    (No changes were needed here as its logic is specific).
    """
    def __init__(
        self,
        api: APIClient,
        conflict: Dict,
        on_success: Optional[Callable] = None,
        record: Optional[Dict] = None,
        mode: str = "create",
    ):
        self.api = api
        self.conflict = conflict
        self.on_success = on_success
        self.record = record or {}
        self.mode = mode
        self.dialog = None
        self.acciones_options = {}

    async def open(self):
        from datetime import datetime

        try:
            acciones = await self.api.get_records("acciones", order="id.asc")
            self.acciones_options = {a["id"]: a.get("nombre", f"Acción #{a['id']}") for a in acciones}
        except Exception as e:
            ui.notify(f"Error al cargar acciones: {e}", type="negative")

        self.dialog = ui.dialog()
        with self.dialog, ui.card().classes("w-96"):
            title = f'Añadir Nota al Conflicto #{self.conflict["id"]}' if self.mode == "create" else f'Editar Nota #{self.record.get("id")}'
            ui.label(title).classes("text-h6")

            initial_estado = self.record.get("estado") if self.mode == "edit" else self.conflict.get("estado", "")
            estado_input = ui.select(options=["Abierto", "En proceso", "Resuelto", "Cerrado"], label="Estado", value=initial_estado).classes("w-full")
            accion_input = ui.select(options=self.acciones_options, label="Acción realizada", value=self.record.get("accion_id")).classes("w-full")
            notas_input = ui.textarea("Actualización/Notas", value=self.record.get("notas", "")).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")

                async def save_note():
                    try:
                        user_id = app.storage.user.get("user_id")
                        if not user_id:
                            raise ValueError("Usuario no identificado.")

                        note_data = {
                            "conflicto_id": self.conflict["id"],
                            "accion_id": accion_input.value,
                            "usuario_id": user_id,
                            "estado": estado_input.value,
                            "notas": notas_input.value,
                        }
                        payload = {k: v for k, v in note_data.items() if v is not None}

                        if self.mode == "create":
                            await self.api.create_record("diario_conflictos", payload)
                        else:
                            await self.api.update_record("diario_conflictos", self.record["id"], payload)

                        # Also update the parent conflict's status if changed.
                        new_estado = estado_input.value
                        if new_estado and new_estado != self.conflict.get("estado"):
                            conflict_update = {"estado": new_estado}
                            if new_estado == "Cerrado":
                                conflict_update["fecha_cierre"] = datetime.now().strftime("%Y-%m-%d")
                            await self.api.update_record("conflictos", self.conflict["id"], conflict_update)

                        ui.notify(f"Nota {'añadida' if self.mode == 'create' else 'actualizada'} con éxito", type="positive")
                        self.dialog.close()
                        if self.on_success:
                            await self.on_success()
                    except Exception as e:
                        ui.notify(f"Error al guardar la nota: {e}", type="negative")

                ui.button("Guardar", on_click=save_note).props("color=orange-600")

        self.dialog.open()