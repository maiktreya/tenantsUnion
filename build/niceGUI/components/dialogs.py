from typing import Dict, Optional, Callable
from nicegui import ui, app
from api.client import APIClient
from config import TABLE_INFO
from datetime import date


class RecordDialog:
    """Dialog for creating/editing records, driven by TABLE_INFO."""

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
        """Open the dialog asynchronously."""
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

    def _get_fields(self):
        """Get list of fields for the table, prioritizing explicit 'fields' list."""
        table_info = TABLE_INFO.get(self.table, {})
        if "fields" in table_info:
            return table_info["fields"]
        if self.mode == "edit" and self.record:
            fields = list(self.record.keys())
            if "id" in fields:
                fields.remove("id")
            return fields
        fields = set()
        if "relations" in table_info:
            fields.update(table_info["relations"].keys())
        if not fields:
            ui.notify(
                f"No fields configured for table '{self.table}' in create mode.",
                type="warning",
            )
        return list(fields)

    async def _create_inputs(self):
        """Create input fields dynamically based on TABLE_INFO configuration."""
        table_info = TABLE_INFO.get(self.table, {})
        relations = table_info.get("relations", {})
        field_options = table_info.get("field_options", {})  # Get predefined options
        fields = self._get_fields()

        fields = sorted(fields, key=lambda f: (0 if f in relations else 1, f))

        for field in fields:
            value = self.record.get(field, "")
            lower = field.lower()

            # 1. Foreign Key Relation -> Searchable Dropdown
            if field in relations:
                relation = relations[field]
                view_name = relation["view"]
                display_field = relation["display_field"]
                try:
                    options_records = await self.api.get_records(view_name, limit=2000)
                    if "," in display_field:
                        get_disp = lambda r: " ".join(
                            [str(r.get(df, "")) for df in display_field.split(",")]
                        ).strip()
                    else:
                        get_disp = lambda r: str(r.get(display_field, f"ID: {r['id']}"))
                    options = {r["id"]: get_disp(r) for r in options_records}
                except Exception as e:
                    ui.notify(
                        f"Error cargando opciones de {field}: {e}", type="negative"
                    )
                    options = {}
                self.inputs[field] = (
                    ui.select(
                        options=options,
                        label=field.replace("_", " ").title(),
                        value=value if value in options else None,
                    )
                    .classes("w-full")
                    .props("use-input")
                )

            # 2. Predefined Options from config.py -> Dropdown
            elif field in field_options:
                options = field_options[field]
                select_value = value if value in options else None
                self.inputs[field] = ui.select(
                    options=options,
                    label=field.replace("_", " ").title(),
                    value=select_value,
                ).classes("w-full")

            # 3. Date Field -> Date Input with Default
            elif "fecha" in lower:
                default_value = value
                if self.mode == "create" and field == "fecha_apertura":
                    default_value = date.today().isoformat()
                with ui.input(
                    label=field.replace("_", " ").title(), value=default_value
                ) as input_field:
                    with input_field.add_slot("append"):
                        ui.icon("edit_calendar").on(
                            "click", lambda: menu.open()
                        ).classes("cursor-pointer")
                    with ui.menu() as menu:
                        ui.date().bind_value(input_field)
                self.inputs[field] = input_field

            # 4. Text Area for long text
            elif "nota" in lower or "descripcion" in lower or "resolucion" in lower:
                self.inputs[field] = ui.textarea(
                    label=field.replace("_", " ").title(), value=value
                ).classes("w-full")

            # 5. Default -> Plain Text Input
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
            if self.mode == "create":
                data.pop("id", None)
                result = await self.api.create_record(self.table, data)
                if result:
                    ui.notify("Registro creado con éxito", type="positive")
                    if self.on_success:
                        await self.on_success()
                    self.dialog.close()
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
                        if self.on_success:
                            await self.on_success()
                        self.dialog.close()
                else:
                    ui.notify("No se realizaron cambios", type="info")
        except Exception as e:
            ui.notify(f"Error al guardar: {str(e)}", type="negative")


class EnhancedRecordDialog(RecordDialog):
    pass


class ConflictNoteDialog:
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

    async def open(self):
        self.dialog = ui.dialog()

        with self.dialog, ui.card().classes("w-96"):
            title = (
                f'Añadir Nota al Conflicto #{self.conflict["id"]}'
                if self.mode == "create"
                else f'Editar Nota #{self.record.get("id")}'
            )
            ui.label(title).classes("text-h6")

            # --- FIX START ---
            # Get field options directly from the central configuration
            diario_info = TABLE_INFO.get("diario_conflictos", {})
            field_options = diario_info.get("field_options", {})
            estado_options = field_options.get("estado", [])
            accion_options = field_options.get("accion", [])
            # --- FIX END ---

            initial_estado = (
                self.record.get("estado")
                if self.mode == "edit"
                else self.conflict.get("estado", "")
            )
            estado_input = ui.select(
                options=estado_options,
                label="Estado",
                value=initial_estado,
            ).classes("w-full")

            # --- FIX: Use new options and field name "accion" ---
            accion_input = ui.select(
                options=accion_options,
                label="Acción realizada",
                value=self.record.get("accion") if self.mode == "edit" else None,
            ).classes("w-full")

            notas_input = ui.textarea(
                "Actualización/Notas", value=self.record.get("notas", "")
            ).classes("w-full")

            tarea_actual_input = ui.input(
                "Tarea Actual", value=self.record.get("tarea_actual", "")
            ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")

                async def save_note():
                    try:
                        user_id = app.storage.user.get("user_id")
                        if not user_id:
                            ui.notify("Error: usuario no identificado", type="negative")
                            return

                        # --- FIX: Use "accion" field instead of "accion_id" ---
                        note_data = {
                            "conflicto_id": self.conflict["id"],
                            "accion": accion_input.value,
                            "usuario_id": user_id,
                            "estado": estado_input.value or None,
                            "notas": notas_input.value or None,
                            "tarea_actual": tarea_actual_input.value or None,
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
                            # Update the parent conflict
                            conflict_update_data = {}
                            conflict_update_data["tarea_actual"] = (
                                tarea_actual_input.value or None
                            )

                            new_estado = estado_input.value
                            if (
                                new_estado == "Cerrado"
                                and self.conflict.get("estado") != "Cerrado"
                            ):
                                conflict_update_data["fecha_cierre"] = (
                                    date.today().isoformat()
                                )
                                conflict_update_data["estado"] = "Cerrado"
                            elif (
                                new_estado != "Cerrado"
                                and self.conflict.get("estado") == "Cerrado"
                            ):
                                conflict_update_data["fecha_cierre"] = None
                                conflict_update_data["estado"] = new_estado

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
                            if self.on_success:
                                await self.on_success()
                            self.dialog.close()
                    except Exception as e:
                        ui.notify(
                            f"Error al guardar la nota: {str(e)}", type="negative"
                        )

                ui.button("Guardar", on_click=save_note).props("color=orange-600")

        self.dialog.open()
