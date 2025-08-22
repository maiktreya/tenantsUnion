from typing import Dict, Optional, Callable
from nicegui import ui
from api.client import APIClient
from config import TABLE_INFO  # Import TABLE_INFO to get relation metadata


class RecordDialog:
    """Dialog for creating/editing records"""

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

    def open(self):
        """Open the dialog"""
        self.dialog = ui.dialog()

        with self.dialog, ui.card().classes("w-96"):
            title = (
                f"Crear nuevo registro en {self.table}"
                if self.mode == "create"
                else f'Editar registro #{self.record.get("id")} de {self.table}'
            )
            ui.label(title).classes("text-h6")

            self._create_inputs()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")
                ui.button(
                    "Guardar", on_click=lambda: ui.timer(0.1, self._save, once=True)
                ).props("color=orange-600")

        self.dialog.open()

    def _create_inputs(self):
        """Create input fields based on record structure"""
        if self.mode == "edit":
            fields = {k: v for k, v in self.record.items() if k != "id"}
        else:
            fields = self._get_table_fields()

        for field_name, field_value in fields.items():
            value = str(field_value) if field_value is not None else ""
            self.inputs[field_name] = ui.input(
                field_name, value=value if self.mode == "edit" else ""
            ).classes("w-full")

    def _get_table_fields(self) -> Dict:
        """Get fields for the table (simplified version)"""
        common_fields = {
            "nombre": "",
            "descripcion": "",
            "estado": "",
            "fecha": "",
        }
        table_fields = {
            "empresas": {"nombre": "", "tipo": "", "direccion": ""},
            "usuarios": {"nombre": "", "email": "", "rol": ""},
            "conflictos": {"descripcion": "", "estado": "", "causa": "", "ambito": ""},
            "facturacion": {"monto": "", "fecha": "", "concepto": ""},
        }
        return table_fields.get(self.table, common_fields)

    async def _save(self):
        """Save the record"""
        try:
            data = {
                field: self.inputs[field].value
                for field in self.inputs
                if self.inputs[field].value
            }

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
                        self.table, self.record["id"], changed_data
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
    """Dialog with dropdown support for foreign keys, inheriting from RecordDialog."""

    async def open(self):
        """Asynchronously open the dialog and create the inputs."""
        self.dialog = ui.dialog()

        with self.dialog, ui.card().classes("w-96"):
            title = (
                f"Crear nuevo registro en {self.table}"
                if self.mode == "create"
                else f'Editar registro #{self.record.get("id")} de {self.table}'
            )
            ui.label(title).classes("text-h6")

            await self._create_inputs()  # This now needs to be awaited

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")
                ui.button(
                    "Guardar", on_click=lambda: ui.timer(0.1, self._save, once=True)
                ).props("color=orange-600")

        self.dialog.open()

    async def _create_inputs(self):
        """Create input fields, using dropdowns for foreign keys."""
        table_info = TABLE_INFO.get(self.table, {})
        relations = table_info.get("relations", {})

        # Use existing record fields in edit mode, otherwise get schema
        if self.mode == "edit":
            fields = {k: v for k, v in self.record.items() if k != "id"}
        else:
            # This logic can be enhanced to fetch schema from DB in a real app
            fields = self._get_table_fields()
            # Ensure relational fields are present even if not in the basic schema
            for field in relations:
                if field not in fields:
                    fields[field] = None

        for field_name in fields.keys():
            if field_name in relations:
                relation_info = relations[field_name]
                view_name = relation_info["view"]
                display_field = relation_info["display_field"]

                try:
                    options_records = await self.api.get_records(view_name)
                    options = {
                        record["id"]: record.get(display_field, f"ID: {record['id']}")
                        for record in options_records
                    }

                    self.inputs[field_name] = ui.select(
                        options,
                        label=field_name.replace("_", " ").title(),
                        value=(
                            self.record.get(field_name) if self.mode == "edit" else None
                        ),
                    ).classes("w-full")
                except Exception as e:
                    ui.notify(
                        f"Error al cargar opciones para {field_name}: {e}",
                        type="negative",
                    )
                    # Fallback to a simple input on error
                    self.inputs[field_name] = ui.number(
                        label=field_name, value=self.record.get(field_name)
                    ).classes("w-full")

            else:
                value = self.record.get(field_name)
                value_str = str(value) if value is not None else ""
                self.inputs[field_name] = ui.input(
                    label=field_name.replace("_", " ").title(), value=value_str
                ).classes("w-full")


class ConflictNoteDialog:
    """Dialog for adding notes to conflicts"""

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

    def open(self):
        """Open the dialog"""
        from datetime import datetime

        self.dialog = ui.dialog()

        with self.dialog, ui.card().classes("w-96"):
            title = (
                f'Añadir Nota al Conflicto #{self.conflict["id"]}'
                if self.mode == "create"
                else f'Editar Nota #{self.record.get("id")}'
            )
            ui.label(title).classes("text-h6")

            # Input fields
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

            ambito_input = ui.input(
                "Ámbito",
                value=(
                    self.record.get("ambito")
                    if self.mode == "edit"
                    else self.conflict.get("ambito", "")
                ),
            ).classes("w-full")

            afectada_input = ui.input(
                "Afectada",
                value=(
                    self.record.get("afectada")
                    if self.mode == "edit"
                    else self.conflict.get("afiliada_id", "")
                ),
            ).classes("w-full")

            notas_input = ui.textarea(
                "Actualización/Notas", value=self.record.get("causa", "")
            ).classes("w-full")

            # Action buttons
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")

                async def save_note():
                    try:
                        note_data = {
                            "conflicto_id": self.conflict["id"],
                            "estado": estado_input.value or None,
                            "ambito": ambito_input.value or None,
                            "afectada": afectada_input.value or None,
                            "causa": notas_input.value or None,
                        }
                        if self.mode == "create":
                            note_data["created_at"] = datetime.now().isoformat()

                        note_data = {
                            k: v for k, v in note_data.items() if v is not None
                        }

                        # Save the diary note (create or update)
                        if self.mode == "create":
                            result = await self.api.create_record(
                                "diario_conflictos", note_data
                            )
                        else:
                            result = await self.api.update_record(
                                "diario_conflictos", self.record["id"], note_data
                            )

                        # --- MODIFIED SECTION START ---
                        if result:
                            conflict_update_data = {}
                            new_estado = estado_input.value

                            # Check if the conflict's main status needs updating
                            if new_estado and new_estado != self.conflict.get("estado"):
                                conflict_update_data["estado"] = new_estado

                            # If the new status is "Cerrado", set the closing date
                            if new_estado == "Cerrado":
                                conflict_update_data["fecha_cierre"] = (
                                    datetime.now().strftime("%Y-%m-%d")
                                )

                            # If there's anything to update in the main conflict record, make the API call
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
                        # --- MODIFIED SECTION END ---

                    except Exception as e:
                        ui.notify(
                            f"Error al guardar la nota: {str(e)}", type="negative"
                        )

                ui.button(
                    "Guardar", on_click=lambda: ui.timer(0.1, save_note, once=True)
                ).props("color=orange-600")

        self.dialog.open()
