from typing import Dict, Optional, Callable
from nicegui import ui, app
from api.client import APIClient
from config import TABLE_INFO


class RecordDialog:
    """Dialog for creating/editing records, fields from TABLE_INFO."""

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
        """Open the dialog asynchronously for full dynamic field support."""
        self.dialog = ui.dialog()

        with self.dialog, ui.card().classes("w-96"):
            title = (
                f"Crear nuevo registro en {self.table}"
                if self.mode == "create"
                else f'Editar registro #{self.record.get("id")} de {self.table}'
            )
            ui.label(title).classes("text-h6")

            await self._create_inputs()  # Always async for uniformity

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")
                ui.button(
                    "Guardar", on_click=self._save  # Direct call, no lambda with timer
                ).props("color=orange-600")

        self.dialog.open()

    def _get_fields(self):
        """Get list of fields for the table, using TABLE_INFO and current record."""
        table_info = TABLE_INFO.get(self.table, {})
        relations = table_info.get("relations", {})
        # Try to get fields from first record if any (edit mode), else from relations/child_relations
        fields = set()
        if self.mode == "edit" and self.record:
            fields.update(self.record.keys())
        else:
            # Infer from relations and child_relations (if any)
            if "relations" in table_info:
                fields.update(table_info["relations"].keys())
            # Guess some common fields if not present (name, estado, descripcion, etc)
            for fname in [
                "nombre",
                "descripcion",
                "estado",
                "fecha",
                "causa",
                "ambito",
                "email",
                "alias",
            ]:
                if fname not in fields:
                    fields.add(fname)
            # Remove PKs for create mode
            id_field = table_info.get("id_field", "id")
            if self.mode == "create":
                for key in str(id_field).split(","):
                    if key.strip() in fields:
                        fields.remove(key.strip())
        # Always ensure 'id' is not in create form
        if self.mode == "create" and "id" in fields:
            fields.remove("id")
        return list(fields)

    async def _create_inputs(self):
        """Create input fields based on TABLE_INFO, relations, and record."""
        table_info = TABLE_INFO.get(self.table, {})
        relations = table_info.get("relations", {})
        fields = self._get_fields()

        # Always preserve order: show relations first, then others (alphabetically)
        def field_sort_key(f):
            return (0 if f in relations else 1, f)

        fields = sorted(fields, key=field_sort_key)

        for field in fields:
            value = self.record.get(field, "")
            # If relation, show dropdown
            if field in relations:
                relation = relations[field]
                view_name = relation["view"]
                display_field = relation["display_field"]
                try:
                    options_records = await self.api.get_records(view_name)
                    # Try to support multiple display fields (like "nombre,apellidos")
                    if "," in display_field:

                        def get_disp(r):
                            return " ".join(
                                [str(r.get(df, "")) for df in display_field.split(",")]
                            ).strip()

                    else:

                        def get_disp(r):
                            return str(r.get(display_field, f"ID: {r['id']}"))

                    options = {r["id"]: get_disp(r) for r in options_records}
                except Exception as e:
                    ui.notify(
                        f"Error cargando opciones de {field}: {e}", type="negative"
                    )
                    options = {}
                self.inputs[field] = ui.select(
                    options=options,
                    label=field.replace("_", " ").title(),
                    value=value if self.mode == "edit" else None,
                ).classes("w-full")
            else:
                # Try to infer field type for better UI (int, float, email, textarea)
                lower = field.lower()
                if "nota" in lower or "descripcion" in lower or "comentario" in lower:
                    self.inputs[field] = ui.textarea(
                        label=field.replace("_", " ").title(), value=value
                    ).classes("w-full")
                elif "email" in lower:
                    self.inputs[field] = (
                        ui.input(label=field.replace("_", " ").title(), value=value)
                        .props("type=email")
                        .classes("w-full")
                    )
                elif "fecha" in lower:
                    self.inputs[field] = (
                        ui.input(label=field.replace("_", " ").title(), value=value)
                        .props("type=date")
                        .classes("w-full")
                    )
                elif (
                    isinstance(value, int)
                    or lower.endswith("_id")
                    or lower.startswith("id_")
                ):
                    self.inputs[field] = ui.number(
                        label=field.replace("_", " ").title(),
                        value=value if value != "" else None,
                    ).classes("w-full")
                else:
                    self.inputs[field] = ui.input(
                        label=field.replace("_", " ").title(), value=value
                    ).classes("w-full")

    async def _save(self):
        """Save the record (create or edit)."""
        try:
            data = {
                field: self.inputs[field].value
                for field in self.inputs
                if self.inputs[field].value not in [None, ""]
            }
            # Remove id field for create
            if self.mode == "create":
                data.pop("id", None)
            if self.mode == "create":
                result = await self.api.create_record(self.table, data)
                if result:
                    ui.notify("Registro creado con éxito", type="positive")
                    self.dialog.close()
                    if self.on_success:
                        await self.on_success()
            else:
                changed_data = {
                    field: value
                    for field, value in data.items()
                    if str(value) != str(self.record.get(field, ""))
                }
                if changed_data:
                    result = await self.api.update_record(
                        self.table, self.record.get("id"), changed_data
                    )
                    if result:
                        ui.notify("Registro actualizado con éxito", type="positive")
                        self.dialog.close()
                        if self.on_success:
                            await self.on_success()
                else:
                    ui.notify("No se realizaron cambios", type="info")
        except Exception as e:
            ui.notify(f"Error al guardar: {str(e)}", type="negative")


class EnhancedRecordDialog(RecordDialog):
    """
    This class is kept for backwards compatibility; it is just an alias for the fully dynamic RecordDialog now.
    """

    pass


class ConflictNoteDialog:
    """
    Dialog para añadir o editar notas en conflictos, compatible con la nueva tabla diario_conflictos.
    (This could be further enhanced; here, we keep your custom logic.)
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

        # Cargar acciones
        try:
            acciones = await self.api.get_records("acciones", order="id.asc")
            self.acciones_options = {
                accion["id"]: accion.get("nombre", f"Acción #{accion['id']}")
                for accion in acciones
            }
        except Exception as e:
            ui.notify(f"Error al cargar acciones: {e}", type="negative")
            self.acciones_options = {}

        self.dialog = ui.dialog()

        with self.dialog, ui.card().classes("w-96"):
            title = (
                f'Añadir Nota al Conflicto #{self.conflict["id"]}'
                if self.mode == "create"
                else f'Editar Nota #{self.record.get("id")}'
            )
            ui.label(title).classes("text-h6")

            # Inputs de la nueva estructura
            initial_estado = (
                self.record.get("estado")
                if self.mode == "edit"
                else self.conflict.get("estado", "")
            )
            estado_input = ui.select(
                options=["Abierto", "En proceso", "Resuelto", "Cerrado"],
                label="Estado",
                value=initial_estado,
            ).classes("w-full")

            accion_input = ui.select(
                options=self.acciones_options,
                label="Acción realizada",
                value=self.record.get("accion_id") if self.mode == "edit" else None,
            ).classes("w-full")

            notas_input = ui.textarea(
                "Actualización/Notas", value=self.record.get("notas", "")
            ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")

                async def save_note():
                    try:
                        user_id = app.storage.user.get("user_id")
                        if not user_id:
                            ui.notify("Error: usuario no identificado", type="negative")
                            return

                        note_data = {
                            "conflicto_id": self.conflict["id"],
                            "accion_id": accion_input.value,
                            "usuario_id": user_id,
                            "estado": estado_input.value or None,
                            "notas": notas_input.value or None,
                        }

                        note_data = {
                            k: v for k, v in note_data.items() if v is not None
                        }

                        if self.mode == "create":
                            result = await self.api.create_record(
                                "diario_conflictos", note_data
                            )
                        else:
                            result = await self.api.update_record(
                                "diario_conflictos", self.record["id"], note_data
                            )

                        if result:
                            # Si cambiamos el estado, también actualizar el conflicto principal
                            conflict_update_data = {}
                            new_estado = estado_input.value
                            if new_estado and new_estado != self.conflict.get("estado"):
                                conflict_update_data["estado"] = new_estado
                            if new_estado == "Cerrado":
                                conflict_update_data["fecha_cierre"] = (
                                    datetime.now().strftime("%Y-%m-%d")
                                )
                            if conflict_update_data:
                                await self.api.update_record(
                                    "conflictos",
                                    self.conflict["id"],
                                    conflict_update_data,
                                )

                            ui.notify(
                                f"Nota {'añadida' if self.mode == 'create' else 'actualizada'} con éxito",
                                type="positive",
                            )
                            self.dialog.close()
                            if self.on_success:
                                await self.on_success()
                        else:
                            ui.notify("Error al guardar la nota", type="negative")
                    except Exception as e:
                        ui.notify(
                            f"Error al guardar la nota: {str(e)}", type="negative"
                        )

                ui.button(
                    "Guardar", on_click=save_note  # Fixed: call save_note directly
                ).props("color=orange-600")

        self.dialog.open()
