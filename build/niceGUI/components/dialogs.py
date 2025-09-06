# build/niceGUI/components/dialogs.py

from typing import Dict, Optional, Callable, Awaitable
from nicegui import ui, app
from api.client import APIClient
from config import TABLE_INFO
from datetime import date


class ConfirmationDialog:
    """A reusable dialog for confirming actions."""

    def __init__(
        self,
        title: str,
        message: str,
        on_confirm: Callable[[], Awaitable[None]],
        confirm_button_text: str = "Confirmar",
        confirm_button_color: str = "primary",
    ):
        self.dialog = ui.dialog()
        with self.dialog, ui.card():
            ui.label(title).classes("text-h6")
            ui.label(message).classes("text-body2 text-gray-600")
            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")

                async def handle_confirm():
                    await on_confirm()
                    self.dialog.close()

                ui.button(
                    confirm_button_text,
                    on_click=handle_confirm,
                    color=confirm_button_color,
                )
        self.dialog.open()


class EnhancedRecordDialog:
    """
    Enhanced dialog for creating/editing records, driven by TABLE_INFO,
    with support for custom on_save logic.
    """

    def __init__(
        self,
        api: APIClient,
        table: str,
        record: Optional[Dict] = None,
        mode: str = "create",
        on_success: Optional[Callable] = None,
        on_save: Optional[Callable[[Dict], Awaitable[bool]]] = None,
    ):
        self.api = api
        self.table = table
        self.record = record or {}
        self.mode = mode
        self.on_success = on_success
        self.on_save = on_save
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
                ui.button("Guardar", on_click=self._save_handler).props(
                    "color=orange-600"
                )

        self.dialog.open()

    def _get_fields(self):
        """Get list of fields for the table, prioritizing explicit 'fields' list."""
        table_info = TABLE_INFO.get(self.table, {})
        if "fields" in table_info:
            return table_info["fields"]
        if self.mode == "edit" and self.record:
            fields = list(self.record.keys())
            pk_field = TABLE_INFO.get(self.table, {}).get("id_field", "id")
            if pk_field in fields:
                fields.remove(pk_field)
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
        field_options = table_info.get("field_options", {})
        fields = self._get_fields()

        fields = sorted(fields, key=lambda f: (0 if f in relations else 1, f))

        for field in fields:
            value = self.record.get(field)
            label = field.replace("_", " ").title()
            lower_field = field.lower()

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
                        get_disp = lambda r: str(
                            r.get(display_field, f"ID: {r.get('id')}")
                        )
                    options = {r["id"]: get_disp(r) for r in options_records}
                except Exception as e:
                    ui.notify(
                        f"Error loading options for {field}: {e}", type="negative"
                    )
                    options = {}

                current_value = value
                if current_value not in options:
                    current_value = None

                # Hide pre-filled fields in create mode for a cleaner UI
                if field in ["conflicto_id", "usuario_id"] and self.mode == "create":
                    self.inputs[field] = ui.input(value=current_value).style(
                        "display: none"
                    )
                    continue

                self.inputs[field] = (
                    ui.select(options=options, label=label, value=current_value)
                    .classes("w-full")
                    .props("use-input")
                )

            elif field in field_options:
                options = field_options[field]
                current_value = value

                if current_value not in options:
                    current_value = None

                self.inputs[field] = ui.select(
                    options=options, label=label, value=current_value
                ).classes("w-full")

            elif "fecha" in lower_field:
                default_value = value
                if self.mode == "create" and not value and field == "fecha_apertura":
                    default_value = date.today().isoformat()
                elif self.mode == "create" and not value:
                    default_value = None
                with ui.input(label=label, value=default_value) as input_field:
                    with input_field.add_slot("append"):
                        ui.icon("edit_calendar").on(
                            "click", lambda: menu.open()
                        ).classes("cursor-pointer")
                    with ui.menu() as menu:
                        ui.date().bind_value(input_field)
                self.inputs[field] = input_field
            elif any(
                substr in lower_field
                for substr in ["nota", "descripcion", "resolucion"]
            ):
                self.inputs[field] = ui.textarea(label=label, value=value).classes(
                    "w-full"
                )
            else:
                self.inputs[field] = ui.input(label=label, value=value or "").classes(
                    "w-full"
                )

    async def _save_handler(self):
        """Central save handler that uses a custom callback if provided."""
        try:
            data = {
                field: self.inputs[field].value
                for field in self.inputs
                if self.inputs[field].value is not None
            }

            if self.on_save:
                success = await self.on_save(data)
                if success:
                    self.dialog.close()
                    if self.on_success:
                        await self.on_success()
                return

            if self.mode == "create":
                result = await self.api.create_record(self.table, data)
                if result:
                    ui.notify("Record created successfully", type="positive")
            else:
                record_id = self.record.get(
                    TABLE_INFO.get(self.table, {}).get("id_field", "id")
                )
                result = await self.api.update_record(self.table, record_id, data)
                if result:
                    ui.notify("Record updated successfully", type="positive")

            if result:
                self.dialog.close()
                if self.on_success:
                    await self.on_success()

        except Exception as e:
            ui.notify(f"Error saving record: {str(e)}", type="negative")
