from typing import Dict, Optional, Callable
from nicegui import ui, app
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
    """Dialog para añadir o editar notas en conflictos, compatible con la nueva tabla diario_conflictos"""

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
        """Abre el diálogo (ahora async porque carga acciones)"""
        from datetime import datetime

        # Cargar acciones
        try:
            acciones = await self.api.get_records("acciones", order="id.asc")
            self.acciones_options = {accion["id"]: accion.get("nombre", f"Acción #{accion['id']}") for accion in acciones}
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
            # Estado
            initial_estado = self.record.get("estado") if self.mode == "edit" else self.conflict.get("estado", "")
            estado_input = ui.select(
                options=["Abierto", "En proceso", "Resuelto", "Cerrado"],
                label="Estado",
                value=initial_estado,
            ).classes("w-full")

            # Ámbito
            ambito_input = ui.input(
                "Ámbito",
                value=self.record.get("ambito") if self.mode == "edit" else self.conflict.get("ambito", ""),
            ).classes("w-full")

            # Acción (nuevo campo obligatorio)
            accion_input = ui.select(
                options=self.acciones_options,
                label="Acción realizada",
                value=self.record.get("accion_id") if self.mode == "edit" else None,
            ).classes("w-full")

            # Afiliada (puede venir del conflicto o de la nota previa)
            afiliada_input = ui.number(
                "ID Afiliada (opcional)",
                value=(
                    self.record.get("afiliada_id")
                    if self.mode == "edit"
                    else self.conflict.get("afiliada_id", "")
                ),
                ).classes("w-full")

            # Notas (nuevo campo obligatorio)
            notas_input = ui.textarea(
                "Actualización/Notas",
                value=self.record.get("notas", "")
            ).classes("w-full")

            # Botones
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")

                async def save_note():
                    try:
                        # Usuario actual
                        user_id = app.storage.user.get("user_id")
                        if not user_id:
                            ui.notify("Error: usuario no identificado", type="negative")
                            return

                        note_data = {
                            "conflicto_id": self.conflict["id"],
                            "accion_id": accion_input.value,
                            "usuario_id": user_id,
                            "estado": estado_input.value or None,
                            "ambito": ambito_input.value or None,
                            "notas": notas_input.value or None,
                        }


                        note_data = {k: v for k, v in note_data.items() if v is not None}

                        # Guardar la nota (insertar o editar)
                        if self.mode == "create":
                            result = await self.api.create_record("diario_conflictos", note_data)
                        else:
                            result = await self.api.update_record("diario_conflictos", self.record["id"], note_data)

                        if result:

                            result = await self.api.create_record("diario_conflictos", note_data)
                            # Si cambiamos el estado general, actualizamos el conflicto principal
                            conflict_update_data = {}
                            new_estado = estado_input.value
                            if new_estado and new_estado != self.conflict.get("estado"):
                                conflict_update_data["estado"] = new_estado
                            # Si cerramos, guardamos la fecha
                            if new_estado == "Cerrado":
                                conflict_update_data["fecha_cierre"] = datetime.now().strftime("%Y-%m-%d")
                            if conflict_update_data:
                                await self.api.update_record("conflictos", self.conflict["id"], conflict_update_data)

                            ui.notify(
                                f"Nota {'añadida' if self.mode == 'create' else 'actualizada'} con éxito",
                                type="positive",
                            )
                            self.dialog.close()
                            if self.on_success:
                                await self.on_success()
                        else:
                            print("DEBUG note_data:", note_data)
                            ui.notify("Error al guardar la nota", type="negative")
                    except Exception as e:
                        ui.notify(f"Error al guardar la nota: {str(e)}", type="negative")

                ui.button(
                    "Guardar", on_click=lambda: ui.timer(0.1, save_note, once=True)
                ).props("color=orange-600")

        self.dialog.open()