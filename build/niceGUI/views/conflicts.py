# build/niceGUI/views/conflicts.py

from typing import Optional, List, Dict, Awaitable, Callable
from nicegui import ui, app
from api.client import APIClient
from state.conflicts_state import ConflictsState
from components.dialogs import EnhancedRecordDialog, ConfirmationDialog
from datetime import date

# Import TABLE_INFO to be the single source of truth for options
from config import TABLE_INFO


class ConflictsView:
    """Enhanced conflicts management view with address display and node filtering"""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = ConflictsState()
        self.conflict_select = None
        self.info_container = None
        self.history_container = None
        self.all_conflicts = []
        self.filtered_conflicts = []
        self.nodos_list = []
        self.filter_nodo = None
        self.filter_estado = None
        self.filter_causa = None
        self.filter_text = None

    def create(self) -> ui.column:
        """Create the enhanced conflicts view UI"""
        container = ui.column().classes("w-full p-4 gap-4")

        with container:
            ui.label("Toma de Actas - Gestión de Conflictos").classes("text-h4")

            # --- REFACTORED: Get options directly from TABLE_INFO ---
            conflict_options = TABLE_INFO.get("conflictos", {}).get("field_options", {})
            estado_opts_list = conflict_options.get("estado", [])
            causa_opts_list = conflict_options.get("causa", [])

            # --- REFACTORED: Build options dictionaries dynamically ---
            estado_options = {"": "Todos los estados"}
            estado_options.update({opt: opt for opt in estado_opts_list})

            causa_options = {"": "Todas las causas"}
            causa_options.update({opt: opt for opt in causa_opts_list})
            # --- END REFACTOR ---

            # Filter Section
            with ui.expansion("Filtros", icon="filter_list").classes(
                "w-full mb-4"
            ).props("default-opened"):
                with ui.row().classes("w-full gap-4 flex-wrap items-center"):
                    self.filter_nodo = ui.select(
                        options={},
                        label="Filtrar por Nodo",
                        on_change=self._apply_filters,
                        clearable=True,
                    ).classes("w-64")
                    self.filter_estado = ui.select(
                        # Use the dynamically generated options
                        options=estado_options,
                        label="Filtrar por Estado",
                        value="",
                        on_change=self._apply_filters,
                    ).classes("w-48")
                    self.filter_causa = ui.select(
                        # Use the dynamically generated options
                        options=causa_options,
                        label="Filtrar por Causa",
                        on_change=self._apply_filters,
                        clearable=True,
                    ).classes("w-64")
                    self.filter_text = (
                        ui.input(label="Búsqueda global", on_change=self._apply_filters)
                        .classes("flex-grow min-w-[16rem]")
                        .props("clearable")
                    )
                    ui.button(
                        "Limpiar Filtros",
                        icon="clear_all",
                        on_click=self._clear_filters,
                    ).props("flat color=orange-600")

            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("w-96 gap-4"):
                    with ui.row().classes("w-full gap-2"):
                        self.conflict_select = (
                            ui.select(
                                options={},
                                label="Seleccionar Conflicto",
                                on_change=lambda e: self._on_conflict_change(e.value),
                            )
                            .classes("flex-grow")
                            .props("use-input")
                        )
                        ui.button(icon="refresh", on_click=self._load_conflicts).props(
                            "flat"
                        )
                    self.stats_card = ui.card().classes("w-full p-4")
                    self._display_statistics()
                    with ui.row().classes("w-full gap-2"):
                        ui.button(
                            "Añadir Nota", icon="add_comment", on_click=self._add_note
                        ).props("color=orange-600").classes("flex-grow")
                        ui.button(
                            "Crear Conflicto",
                            icon="add_circle",
                            on_click=self._create_conflict,
                        ).props("color=green-600").classes("flex-grow")
                    self.info_container = ui.column().classes("w-full")
                with ui.column().classes("flex-grow"):
                    self.history_container = ui.column().classes("w-full gap-4")

        ui.timer(0.5, self._initialize_data, once=True)
        return container

    async def _initialize_data(self):
        await self._load_nodos()
        await self._load_conflicts()

    async def _load_nodos(self):
        try:
            nodos = await self.api.get_records("nodos", order="nombre.asc")
            self.nodos_list = nodos
            nodo_options = {"": "Todos los nodos"}
            for nodo in nodos:
                nodo_options[nodo["id"]] = nodo["nombre"]
            if self.filter_nodo:
                self.filter_nodo.set_options(nodo_options)
        except Exception as e:
            ui.notify(f"Error loading nodes: {str(e)}", type="negative")

    async def _load_conflicts(self):
        try:
            conflicts = await self.api.get_records(
                "v_conflictos_enhanced", order="id.desc"
            )
            self.all_conflicts = conflicts
            self.state.set_conflicts(conflicts)
            await self._apply_filters()
            self._display_statistics()
        except Exception as e:
            ui.notify(f"Error loading conflicts: {str(e)}", type="negative")

    def _get_conflict_options(self, conflicts: List[Dict]) -> Dict[int, str]:
        options = {}
        for conflict in conflicts:
            label = conflict.get("conflict_label", f"ID {conflict.get('id', 'N/A')}")
            options[conflict["id"]] = label
        return options

    async def _apply_filters(self, _=None):
        filtered = self.all_conflicts.copy()
        if self.filter_nodo and self.filter_nodo.value:
            filtered = [
                c for c in filtered if c.get("nodo_id") == self.filter_nodo.value
            ]
        if self.filter_estado and self.filter_estado.value:
            filtered = [
                c for c in filtered if c.get("estado") == self.filter_estado.value
            ]
        if self.filter_causa and self.filter_causa.value:
            filtered = [
                c for c in filtered if c.get("causa") == self.filter_causa.value
            ]
        if self.filter_text and self.filter_text.value:
            search_text = self.filter_text.value.lower()
            filtered = [
                c
                for c in filtered
                if any(search_text in str(val).lower() for val in c.values() if val)
            ]
        self.filtered_conflicts = filtered
        self.state.set_conflicts(filtered)
        options = self._get_conflict_options(filtered)
        if self.conflict_select:
            self.conflict_select.set_options(options)
            if self.state.selected_conflict_id.value not in options:
                self.conflict_select.value = None
                self.state.set_selected_conflict(None)
                self._clear_displays()
        self._display_statistics()

    def _clear_filters(self):
        self.filter_nodo.value = None
        self.filter_estado.value = ""
        self.filter_causa.value = None
        self.filter_text.value = ""
        ui.timer(0.1, self._apply_filters, once=True)

    def _display_statistics(self):
        if not self.stats_card:
            return
        self.stats_card.clear()
        with self.stats_card:
            ui.label("Estadísticas").classes("text-h6 mb-2")
            status_counts = {}
            for conflict in self.filtered_conflicts:
                estado = conflict.get("estado", "Sin estado")
                status_counts[estado] = status_counts.get(estado, 0) + 1
            with ui.row().classes("w-full gap-4 flex-wrap"):
                ui.chip(
                    f"Total: {len(self.filtered_conflicts)}",
                    color="blue",
                    icon="inventory",
                )
                for estado, count in sorted(status_counts.items()):
                    color = {
                        "Abierto": "red",
                        "En proceso": "orange",
                        "Resuelto": "green",
                        "Cerrado": "gray",
                    }.get(estado, "blue")
                    ui.chip(f"{estado}: {count}", color=color)

    async def _on_conflict_change(self, conflict_id: Optional[int]):
        if not conflict_id:
            self.state.set_selected_conflict(None)
            self._clear_displays()
            return
        conflict = self.state.get_conflict_by_id(conflict_id)
        if conflict:
            self.state.set_selected_conflict(conflict)
            await self._display_conflict_info()
            await self._load_conflict_history()

    async def _display_conflict_info(self):
        """[RESTORED] Display enhanced conflict information"""
        if not self.info_container or not self.state.selected_conflict:
            return

        self.info_container.clear()
        conflict = self.state.selected_conflict

        with self.info_container:
            ui.label("Información del Conflicto").classes("text-h6 mb-2")
            with ui.card().classes("w-full mb-2"):
                ui.label("Datos del Conflicto").classes("text-subtitle2 font-bold mb-2")
                if conflict.get("estado"):
                    color_map = {
                        "Abierto": "red",
                        "En proceso": "orange",
                        "Resuelto": "green",
                        "Cerrado": "gray",
                    }
                    color = color_map.get(conflict["estado"], "blue")
                    ui.badge(conflict["estado"], color=color).props("outline")

                info_items = [
                    ("ID", conflict.get("id")),
                    ("Afiliada", conflict.get("afiliada_nombre_completo")),
                    ("Nº Afiliada", conflict.get("num_afiliada")),
                    ("Ámbito", conflict.get("ambito")),
                    ("Causa", conflict.get("causa")),
                    ("Fecha Apertura", conflict.get("fecha_apertura")),
                    ("Fecha Cierre", conflict.get("fecha_cierre")),
                    ("Responsable", conflict.get("usuario_responsable_alias")),
                    ("Tarea Actual", conflict.get("tarea_actual")),
                ]

                for label, value in info_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        display_value = (
                            value if value is not None and value != "" else "-"
                        )
                        ui.label(str(display_value)).classes("flex-grow")

                if conflict.get("descripcion"):
                    ui.separator().classes("my-2")
                    ui.label("Descripción:").classes("font-bold")
                    ui.label(conflict.get("descripcion")).classes("text-gray-700")

                if conflict.get("resolucion"):
                    ui.separator().classes("my-2")
                    ui.label("Resolución:").classes("font-bold")
                    ui.label(conflict.get("resolucion")).classes("text-green-700")

            with ui.card().classes("w-full"):
                ui.label("Información de Ubicación").classes(
                    "text-subtitle2 font-bold mb-2"
                )
                location_items = [
                    ("Nodo Territorial", conflict.get("nodo_nombre")),
                    ("Dirección Piso", conflict.get("piso_direccion")),
                    ("Dirección Bloque", conflict.get("bloque_direccion")),
                    ("Municipio", conflict.get("piso_municipio")),
                    ("Código Postal", conflict.get("piso_cp")),
                ]
                for label, value in location_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        display_value = (
                            value if value is not None and value != "" else "-"
                        )
                        ui.label(str(display_value)).classes("flex-grow")

    async def _load_conflict_history(self):
        if not self.history_container or not self.state.selected_conflict:
            return
        self.history_container.clear()
        try:
            history = await self.api.get_records(
                "v_diario_conflictos_con_afiliada",
                {"conflicto_id": f'eq.{self.state.selected_conflict["id"]}'},
                order="created_at.desc",
            )
            self.state.set_history(history)
            with self.history_container:
                ui.label("Historial de Notas").classes("text-h6 mb-2")
                if self.state.history:
                    for entry in self.state.history:
                        self._create_history_entry(entry)
                else:
                    ui.label("No se encontraron entradas en el historial").classes(
                        "text-gray-500"
                    )
        except Exception as e:
            ui.notify(f"Error loading history: {str(e)}", type="negative")

    def _create_history_entry(self, entry: dict):
        """[RESTORED] Create a collapsible history entry card."""
        title_text = f"Nota #{entry.get('id', 'N/A')} - {entry.get('created_at', 'Sin fecha').split('T')[0]}"
        if entry.get("autor_nota_alias"):
            title_text += f" | Autor: {entry['autor_nota_alias']}"

        with ui.card().classes("w-full mb-2"):
            with ui.expansion(title_text).classes("w-full"):
                with ui.element("div").classes("p-2"):
                    with ui.row().classes("w-full gap-2 items-center"):
                        ui.icon("schedule", size="sm").classes("text-gray-500")
                        ui.label(
                            entry.get("created_at", "Sin fecha").split(".")[0]
                        ).classes("text-caption text-gray-600")
                        ui.space()
                        ui.button(
                            icon="edit", on_click=lambda e=entry: self._edit_note(e)
                        ).props("size=sm flat dense").tooltip("Editar nota")
                        ui.button(
                            icon="delete", on_click=lambda e=entry: self._delete_note(e)
                        ).props("size=sm flat dense color=negative").tooltip(
                            "Eliminar nota"
                        )
                with ui.card_section().classes("w-full"):
                    if entry.get("notas"):
                        ui.separator().classes("my-2")
                        with ui.row().classes("w-full"):
                            ui.icon("notes", size="sm").classes("text-gray-500 mt-1")
                            with ui.column().classes("flex-grow ml-2"):
                                ui.label("Notas:").classes("font-semibold text-sm")
                                ui.label(entry["notas"]).classes(
                                    "text-gray-700 whitespace-pre-wrap"
                                )
                    if entry.get("tarea_actual"):
                        ui.separator().classes("my-2")
                        with ui.row().classes("w-full"):
                            ui.icon("task", size="sm").classes("text-gray-500 mt-1")
                            with ui.column().classes("flex-grow ml-2"):
                                ui.label("Tarea Actual:").classes(
                                    "font-semibold text-sm"
                                )
                                ui.label(entry["tarea_actual"]).classes(
                                    "text-gray-700 whitespace-pre-wrap"
                                )

    async def _add_note(self):
        if not self.state.selected_conflict:
            ui.notify("Please select a conflict first", type="warning")
            return
        dialog = EnhancedRecordDialog(
            api=self.api,
            table="diario_conflictos",
            mode="create",
            on_success=self._on_note_saved,
            on_save=self._save_note_handler(None),
        )
        await dialog.open()

    async def _create_conflict(self):
        dialog = EnhancedRecordDialog(
            api=self.api,
            table="conflictos",
            mode="create",
            on_success=self._load_conflicts,
        )
        await dialog.open()

    async def _edit_note(self, note: dict):
        dialog = EnhancedRecordDialog(
            api=self.api,
            table="diario_conflictos",
            record=note,
            mode="edit",
            on_success=self._on_note_saved,
            on_save=self._save_note_handler(note),
        )
        await dialog.open()

    def _save_note_handler(
        self, record: Optional[Dict]
    ) -> Callable[[Dict], Awaitable[bool]]:
        """Returns an async function to handle the custom save logic for notes."""

        async def _handler(data: Dict) -> bool:
            user_id = app.storage.user.get("user_id")
            if not user_id:
                ui.notify("Error: User not identified", type="negative")
                return False

            data["conflicto_id"] = self.state.selected_conflict["id"]
            data["usuario_id"] = user_id

            if record:  # Edit mode
                result = await self.api.update_record(
                    "diario_conflictos", record["id"], data
                )
            else:  # Create mode
                result = await self.api.create_record("diario_conflictos", data)

            if not result:
                return False

            # Update parent conflict status
            conflict_update = {"tarea_actual": data.get("tarea_actual")}
            if data.get("estado") == "Cerrado":
                conflict_update["estado"] = "Cerrado"
                conflict_update["fecha_cierre"] = date.today().isoformat()

            # Also update the state if it's not being closed
            elif data.get("estado"):
                conflict_update["estado"] = data.get("estado")

            await self.api.update_record(
                "conflictos", self.state.selected_conflict["id"], conflict_update
            )
            return True

        return _handler

    async def _on_note_saved(self):
        """Callback after a note is successfully saved."""
        await self._load_conflicts()
        if self.state.selected_conflict:
            await self._on_conflict_change(self.state.selected_conflict["id"])

    def _delete_note(self, note: dict):
        async def _confirm_delete():
            success = await self.api.delete_record("diario_conflictos", note["id"])
            if success:
                ui.notify("Note deleted successfully", type="positive")
                await self._load_conflict_history()

        ConfirmationDialog(
            title="Delete Note",
            message=f"Are you sure you want to delete note #{note.get('id')}?",
            on_confirm=_confirm_delete,
            confirm_button_text="Delete",
            confirm_button_color="negative",
        )

    def _clear_displays(self):
        if self.info_container:
            self.info_container.clear()
        if self.history_container:
            self.history_container.clear()
