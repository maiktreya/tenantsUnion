# build/niceGUI/components/dialogs.py (Corrected)

from typing import Dict, Optional, Callable, Awaitable, Any
from nicegui import ui
from api.client import APIClient
from config import TABLE_INFO
from datetime import date


def _clean_dialog_record(record: Dict) -> Dict:
    """
    Cleans a record from a dialog by converting empty strings to None.
    This helps prevent API errors when inserting data into typed columns
    like INTEGER or BOOLEAN, which cannot accept empty strings.
    """
    cleaned = {}
    for key, value in record.items():
        # Convert any empty string to None, otherwise keep the original value
        cleaned[key] = None if value == "" else value
    return cleaned


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
    with support for custom on_save logic and view-aware field rendering.
    """

    def __init__(
        self,
        api: APIClient,
        table: str,
        record: Optional[Dict] = None,
        mode: str = "create",
        on_success: Optional[Callable] = None,
        on_save: Optional[Callable[[Dict], Awaitable[bool]]] = None,
        custom_options: Optional[Dict[str, Dict]] = None,
        custom_labels: Optional[Dict[str, str]] = None,
        calling_view: str = "default",
        sort_fields: bool = True,
        extra_hidden_fields: Optional[list[str]] = None,
    ):
        self.api = api
        self.table = table
        self.record = record or {}
        self.mode = mode
        self.on_success = on_success
        self.on_save = on_save
        self.custom_options = custom_options or {}
        self.custom_labels = custom_labels or {}
        self.dialog = None
        self.inputs = {}
        self.calling_view = calling_view
        self.sort_fields = sort_fields
        self.extra_hidden_fields = set(extra_hidden_fields or [])


    def _resolve_select_value(self, value: Any, options: Any) -> Any:
        """Return the option matching value, ignoring case when possible."""
        if value is None:
            return None
        try:
            # Direct match first
            if isinstance(options, dict):
                if value in options:
                    return value
                value_str = str(value).lower()
                for opt_value, opt_label in options.items():
                    if isinstance(opt_value, str) and opt_value.lower() == value_str:
                        return opt_value
                    if isinstance(opt_label, str) and opt_label.lower() == value_str:
                        return opt_value
                return None
            if isinstance(options, (list, tuple, set)):
                if value in options:
                    return value
                if isinstance(value, str):
                    value_str = value.lower()
                    for opt in options:
                        if isinstance(opt, str) and opt.lower() == value_str:
                            return opt
                return None
        except Exception:
            return None
        return None

    async def open(self):
        """Open the dialog asynchronously."""
        self.dialog = ui.dialog()
        self.dialog.props("persistent no-esc-dismiss")

        with self.dialog, ui.card().classes("w-96"):
            title = (
                f"Crear nuevo registro en {self.table}"
                if self.mode == "create"
                else f'Editar registro #{self.record.get("id")} de {self.table}'
            )

            with ui.row().classes("items-center justify-between w-full"):
                ui.label(title).classes("text-h6")
                (
                    ui.button(icon="close", on_click=self.dialog.close)
                    .props("flat round dense")
                    .props('aria-label="Cerrar dialogo"')
                )

            await self._create_inputs()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancelar", on_click=self.dialog.close).props("flat")
                ui.button("Guardar", on_click=self._save_handler).props(
                    "color=orange-600"
                )

        self.dialog.open()

    def _get_fields(self) -> list[str]:
        """
        Gets a list of fields for the table, prioritizing TABLE_INFO config.
        For the 'admin' view, it returns all fields.
        """
        table_info = TABLE_INFO.get(self.table, {})
        pk_field = table_info.get("id_field", "id")

        # --- FIX #1: Check for the admin view FIRST ---
        if self.calling_view == "admin":
            visible_fields = table_info.get("fields", [])
            hidden_fields = table_info.get("hidden_fields", [])
            all_fields = sorted(list(set(visible_fields + hidden_fields)))
            if pk_field in all_fields:
                all_fields.remove(pk_field)
            return all_fields

        if "fields" in table_info:
            return table_info.get("fields", [])

        if self.mode == "edit" and self.record:
            fields = list(self.record.keys())
            if pk_field in fields:
                fields.remove(pk_field)
            return fields

        fields_set = set(table_info.get("relations", {}).keys())
        if not fields_set:
            ui.notify(
                f"No fields configured for table '{self.table}' in create mode.",
                type="warning",
            )
        return list(fields_set)

    async def _create_inputs(self):
        """Create input fields dynamically based on TABLE_INFO configuration."""
        table_info = TABLE_INFO.get(self.table, {})
        relations = table_info.get("relations", {})
        field_options = table_info.get("field_options", {})
        fields = self._get_fields()

        # --- FIX #2: Hiding logic is now context-aware ---
        pk_field = table_info.get("id_field", "id")
        if self.calling_view == "admin":
            # The admin view should only hide the primary key and any specifically passed 'extra' fields.
            # It IGNORES the 'hidden_fields' from config.py.
            fields_to_hide = self.extra_hidden_fields.union({pk_field})
        else:
            # All other views respect the 'hidden_fields' list from config.py.
            configured_hidden = set(table_info.get("hidden_fields", []))
            fields_to_hide = configured_hidden.union(self.extra_hidden_fields)

        if self.sort_fields:
            fields = sorted(fields, key=lambda f: (0 if f in relations else 1, f))

        for field in fields:
            value = self.record.get(field)
            label = self.custom_labels.get(field, field.replace("_", " ").title())
            lower_field = field.lower()

            # The corrected hiding logic is applied here.
            if field in fields_to_hide:
                self.inputs[field] = ui.input(value=value).style("display: none")
                continue

            if field in self.custom_options:
                options = self.custom_options[field]
                current_value = self._resolve_select_value(value, options)
                self.inputs[field] = (
                    ui.select(options=options, label=label, value=current_value)
                    .classes("w-full")
                    .props("use-input")
                )
            elif field in relations:
                relation = relations[field]
                view_name = relation['view']
                display_field = relation.get('display_field', '')
                value_field = relation.get('value_field', 'id')
                options_limit = relation.get('options_limit', 2000)
                order_by = relation.get('order_by')
                label_template = relation.get('label_template')
                include_value_prefix = relation.get('include_value_prefix')
                try:
                    options_records = await self.api.get_records(
                        view_name,
                        limit=options_limit,
                        order=order_by,
                    )

                    def build_label(record, option_value):
                        if label_template:
                            try:
                                return label_template.format(**record)
                            except Exception:
                                pass

                        fields_to_join = [
                            part.strip() for part in display_field.split(',') if part.strip()
                        ]
                        parts = [
                            str(record.get(part, '')).strip()
                            for part in fields_to_join
                            if record.get(part) not in (None, '')
                        ]
                        display_text = ' '.join(parts).strip()

                        if display_text:
                            if include_value_prefix or field == 'piso_id':
                                return f"[{option_value}] {display_text}".strip()
                            return display_text

                        return (
                            f"[{option_value}]"
                            if include_value_prefix or field == 'piso_id'
                            else str(option_value)
                        )

                    option_items = []
                    for record in options_records:
                        option_value = record.get(value_field)
                        if option_value is None:
                            continue
                        label_text = build_label(record, option_value)
                        option_items.append((option_value, label_text))

                    option_items.sort(key=lambda item: str(item[1]).lower())
                    options = {value: label for value, label in option_items}
                except Exception as e:
                    ui.notify(
                        f"Error loading options for {field}: {e}", type='negative'
                    )
                    options = {}

                option_values = set(options.keys())

                normalized_value = value
                if isinstance(normalized_value, str):
                    stripped = normalized_value.strip()
                    if stripped in option_values:
                        normalized_value = stripped
                    else:
                        try:
                            converted = int(stripped)
                            if converted in option_values:
                                normalized_value = converted
                        except ValueError:
                            pass
                elif normalized_value is not None and normalized_value not in option_values:
                    str_value = str(normalized_value)
                    if str_value in option_values:
                        normalized_value = str_value

                if normalized_value not in option_values:
                    normalized_value = None

                if field in ['conflicto_id', 'usuario_id'] and self.mode == 'create':
                    self.inputs[field] = ui.input(value=normalized_value).style(
                        'display: none'
                    )
                    continue

                self.inputs[field] = (
                    ui.select(
                        options=options,
                        label=label,
                        value=normalized_value,
                        with_input=True,
                        clearable=True,
                    )
                    .classes('w-full')
                    .props("input-debounce='0' fill-input")
                )
            elif field in field_options:
                options = field_options[field]
                current_value = self._resolve_select_value(value, options)
                self.inputs[field] = ui.select(
                    options=options, label=label, value=current_value
                ).classes("w-full")
            elif "fecha" in lower_field:
                default_value = value
                if self.mode == "create" and not value and field == "fecha_apertura":
                    default_value = date.today().isoformat()

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
        """Central save handler that cleans data before sending to the API."""
        try:
            raw_data = {field: self.inputs[field].value for field in self.inputs}
            cleaned_data = _clean_dialog_record(raw_data)

            final_data = cleaned_data
            if self.mode == "create":
                final_data = {
                    key: value
                    for key, value in cleaned_data.items()
                    if value is not None
                }

            if self.on_save:
                success = await self.on_save(final_data)
                if success:
                    self.dialog.close()
                    if self.on_success:
                        await self.on_success()
                return

            if self.mode == "create":
                result, error_message = await self.api.create_record(
                    self.table, final_data
                )
                if result:
                    ui.notify("Record created successfully", type="positive")
                else:
                    ui.notify(f"Error: {error_message}", type="negative")

            else:
                record_id = self.record.get(
                    TABLE_INFO.get(self.table, {}).get("id_field", "id")
                )
                result = await self.api.update_record(self.table, record_id, final_data)
                if result:
                    ui.notify("Record updated successfully", type="positive")

            if result:
                self.dialog.close()
                if self.on_success:
                    await self.on_success()

        except Exception as e:
            ui.notify(f"Error saving record: {str(e)}", type="negative")
