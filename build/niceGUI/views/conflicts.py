from typing import Optional, List, Dict, Awaitable, Callable
from datetime import date
from nicegui import ui, app
from collections import Counter

from api.client import APIClient
from state.app_state import AppState
from components.base_view import BaseView
from components.dialogs import EnhancedRecordDialog, ConfirmationDialog
from config import TABLE_INFO


class ConflictsView(BaseView):
    """Enhanced conflicts management view using the centralized AppState."""

    def __init__(self, api_client: APIClient, state: AppState):
        self.api = api_client
        self.state = state.conflicts
        self.global_state = state
        self.selected_conflict: Optional[Dict] = None
        self.history: List[Dict] = []
        self.conflict_select = None
        self.info_container = None
        self.history_container = None
        self.filter_nodo = None
        self.filter_estado = None
        self.filter_causa = None
        self.filter_text = None

    def create(self) -> ui.column:
        """Create the enhanced conflicts view UI"""
        container = ui.column().classes("w-full p-4 gap-4")

        with container:
            ui.label("Toma de Actas - Gestión de Conflictos").classes(
                "text-h6 font-italic"
            )

            nodo_options = {
                "": "Todos los nodos",
                **{nodo["id"]: nodo["nombre"] for nodo in self.global_state.all_nodos},
            }
            conflict_options = TABLE_INFO.get("conflictos", {}).get("field_options", {})
            estado_opts_list = conflict_options.get("estado", [])
            causa_opts_list = conflict_options.get("causa", [])
            estado_options = {
                "": "Todos los estados",
                **{opt: opt for opt in estado_opts_list},
            }
            causa_options = {
                "": "Todas las causas",
                **{opt: opt for opt in causa_opts_list},
            }

            with ui.expansion("Filtros", icon="filter_list").classes(
                "w-full mb-4"
            ).props("default-opened"):
                with ui.row().classes("w-full gap-4 flex-wrap items-center"):
                    self.filter_nodo = ui.select(
                        options=nodo_options,
                        label="Filtrar por Nodo",
                        on_change=self._apply_filters,
                        clearable=True,
                    ).classes("w-64")
                    self.filter_estado = ui.select(
                        options=estado_options,
                        label="Filtrar por Estado",
                        value="",
                        on_change=self._apply_filters,
                    ).classes("w-48")
                    self.filter_causa = ui.select(
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
                                clearable=True,
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

        ui.timer(0.5, self._load_conflicts, once=True)
        return container

    async def _load_conflicts(self):
        try:
            conflicts = await self.api.get_records(
                "v_conflictos_enhanced", order="id.desc"
            )
            self.state.set_records(conflicts)
            await self._apply_filters()
        except Exception as e:
            ui.notify(f"Error loading conflicts: {str(e)}", type="negative")

    def _get_conflict_options(self, conflicts: List[Dict]) -> Dict[int, str]:
        return {
            c["id"]: c.get("conflict_label", f"ID {c.get('id', 'N/A')}")
            for c in conflicts
        }

    async def _apply_filters(self, _=None):
        """Updates the generic state's filters and refreshes the UI."""
        filters = {
            "nodo_id": (
                self.filter_nodo.value
                if self.filter_nodo and self.filter_nodo.value
                else None
            ),
            "estado": (
                self.filter_estado.value
                if self.filter_estado and self.filter_estado.value
                else None
            ),
            "causa": (
                self.filter_causa.value
                if self.filter_causa and self.filter_causa.value
                else None
            ),
            "global_search": (
                self.filter_text.value
                if self.filter_text and self.filter_text.value
                else None
            ),
        }
        self.state.filters = {k: v for k, v in filters.items() if v is not None}
        self.state.apply_filters_and_sort()

        options = self._get_conflict_options(self.state.filtered_records)
        if self.conflict_select:
            self.conflict_select.set_options(options)
            current_selection_id = (
                self.selected_conflict.get("id") if self.selected_conflict else None
            )
            if current_selection_id not in options:
                self.selected_conflict = None
                self.state.selected_item.set(None)
                self.conflict_select.value = None
                self._clear_displays()
        self._display_statistics()

    def _clear_filters(self):
        self.filter_nodo.value = None
        self.filter_estado.value = ""
        self.filter_causa.value = None
        self.filter_text.value = ""
        ui.timer(0.1, self._apply_filters, once=True)

    def _display_statistics(self):
        """Calculates and displays statistics for the filtered conflicts."""
        if not self.stats_card:
            return
        self.stats_card.clear()
        with self.stats_card:
            ui.label("Estadísticas").classes("text-h6 mb-2")
            all_estados = [
                str(conflict.get("estado", "Sin estado"))
                for conflict in self.state.filtered_records
            ]
            status_counts = Counter(all_estados)

            with ui.row().classes("w-full gap-4 flex-wrap"):
                ui.chip(
                    f"Total: {len(self.state.filtered_records)}",
                    color="blue",
                    icon="inventory",
                )
                for estado, count in sorted(status_counts.items()):
                    color = {
                        "Abierto": "red",
                        "Victoria": "green",
                        "Cerrado": "gray",
                    }.get(estado, "blue")
                    ui.chip(f"{estado}: {count}", color=color)

    async def _on_conflict_change(self, conflict_id: Optional[int]):
        """Handles selection from the dropdown."""
        if not conflict_id:
            self.selected_conflict = None
            self.state.selected_item.set(None)
            self._clear_displays()
            return
        conflict = next(
            (c for c in self.state.records if c.get("id") == conflict_id), None
        )
        if conflict:
            self.selected_conflict = conflict
            self.state.selected_item.set(conflict)
            await self._display_conflict_info()
            await self._load_conflict_history()

    async def _display_conflict_info(self):
        if not self.info_container or not self.selected_conflict:
            return
        self.info_container.clear()
        conflict = self.selected_conflict
        with self.info_container:
            ui.label("Información del Conflicto").classes("text-h6 mb-2")
            with ui.card().classes("w-full mb-2"):
                ui.label("Datos del Conflicto").classes("text-subtitle2 font-bold mb-2")
                if conflict.get("estado"):
                    color = {
                        "Abierto": "red",
                        "Victoria": "green",
                        "Cerrado": "gray",
                    }.get(conflict["estado"], "blue")
                    ui.badge(conflict["estado"], color=color).props("outline")
                info_items = [
                    ("Ámbito", conflict.get("ambito")),
                    ("Contacto", conflict.get("afiliada_nombre_completo")),
                    ("Causa", conflict.get("causa")),
                    ("Fecha Apertura", conflict.get("fecha_apertura")),
                    ("Fecha Cierre", conflict.get("fecha_cierre")),
                    ("Tarea Actual", conflict.get("tarea_actual")),
                ]
                for label, value in info_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        ui.label(
                            str(value) if value not in [None, ""] else "-"
                        ).classes("flex-grow")
                if conflict.get("descripcion"):
                    ui.separator().classes("my-2")
                    ui.label("Descripción:").classes("font-bold")
                    ui.label(conflict["descripcion"]).classes("text-gray-700")
                if conflict.get("resolucion"):
                    ui.separator().classes("my-2")
                    ui.label("Resolución:").classes("font-bold")
                    ui.label(conflict["resolucion"]).classes("text-green-700")
            with ui.card().classes("w-full"):
                ui.label("Información de Ubicación").classes(
                    "text-subtitle2 font-bold mb-2"
                )
                location_items = [
                    ("Nodo Territorial", conflict.get("nodo_nombre")),
                    ("Dirección Piso", conflict.get("piso_direccion")),
                    ("Dirección Bloque", conflict.get("bloque_direccion")),
                ]
                for label, value in location_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        ui.label(
                            str(value) if value not in [None, ""] else "-"
                        ).classes("flex-grow")

    async def _load_conflict_history(self):
        if not self.history_container or not self.selected_conflict:
            return
        self.history_container.clear()
        try:
            history_records = await self.api.get_records(
                "v_diario_conflictos_con_afiliada",
                {"conflicto_id": f'eq.{self.selected_conflict["id"]}'},
                order="created_at.desc",
            )
            self.history = history_records
            with self.history_container:
                ui.label("Historial del conflicto").classes("text-h6 mb-2")
                if self.history:
                    for entry in self.history:
                        self._create_history_entry(entry)
                else:
                    ui.label("No se encontraron entradas en el historial").classes(
                        "text-gray-500"
                    )
        except Exception as e:
            ui.notify(f"Error loading history: {str(e)}", type="negative")

    def _create_history_entry(self, entry: dict):
        title = f"{entry.get('created_at', 'Sin fecha').split('T')[0]}"
        if entry.get("usuario_alias"):
            title += f" |-----| AUTOR: {entry['usuario_alias']}"
        if entry.get("accion"):
            title += f" | ACCION: {entry['tarea_actual']}"
        if entry.get("tarea_actual"):
            title += f" | TAREA: {entry['tarea_actual']}"
        with ui.card().classes("w-full mb-2"):
            with ui.expansion(title).classes("w-full"):
                with ui.element("div").classes("p-2"):
                    with ui.row().classes("w-full gap-2 items-center"):
                        ui.icon("schedule", size="sm").classes("text-gray-500")
                        ui.label(entry.get("created_at", "").split(".")[0]).classes(
                            "text-caption text-gray-600"
                        )
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
                    if entry.get("accion"):
                        ui.separator().classes("my-2")
                        with ui.row().classes("w-full items-start"):
                            ui.icon("flag", size="sm").classes("text-gray-500 mt-1")
                            with ui.column().classes("flex-grow ml-2"):
                                ui.label("Acción:").classes("font-semibold text-sm")
                                ui.label(entry["accion"]).classes(
                                    "text-gray-700 whitespace-pre-wrap"
                                )
                    if entry.get("notas"):
                        ui.separator().classes("my-2")
                        with ui.row().classes("w-full items-start"):
                            ui.icon("notes", size="sm").classes("text-gray-500 mt-1")
                            with ui.column().classes("flex-grow ml-2"):
                                ui.label("Notas:").classes("font-semibold text-sm")
                                ui.label(entry["notas"]).classes(
                                    "text-gray-700 whitespace-pre-wrap"
                                )
                    if entry.get("tarea_actual"):
                        ui.separator().classes("my-2")
                        with ui.row().classes("w-full items-start"):
                            ui.icon("task", size="sm").classes("text-gray-500 mt-1")
                            with ui.column().classes("flex-grow ml-2"):
                                ui.label("Tarea Actual:").classes(
                                    "font-semibold text-sm"
                                )
                                ui.label(entry["tarea_actual"]).classes(
                                    "text-gray-700 whitespace-pre-wrap"
                                )

    async def _add_note(self):
        if not self.selected_conflict:
            return ui.notify(
                "Por favor, seleccione un conflicto primero.", type="warning"
            )
        initial_record = {
            "conflicto_id": self.selected_conflict["id"],
            "usuario_id": app.storage.user.get("user_id"),
            "estado": self.selected_conflict.get("estado"),
        }
        dialog = EnhancedRecordDialog(
            api=self.api,
            table="diario_conflictos",
            mode="create",
            record=initial_record,
            on_success=self._on_note_saved,
            on_save=self._save_note_handler(None),
            custom_labels={"estado": "Estado Conflicto"},
            sort_fields=False,
            extra_hidden_fields=["conflicto_id", "usuario_id"],
        )
        await dialog.open()

    async def _create_conflict(self):
        dialog = EnhancedRecordDialog(
            api=self.api,
            table="conflictos",
            mode="create",
            on_success=self._load_conflicts,
            sort_fields=False,
            custom_options={"afiliada_id": self.global_state.all_afiliadas_options},
            custom_labels={"afiliada_id": "Contacto:"},
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
            custom_labels={"estado": "Estado Conflicto"},
            sort_fields=False,
            extra_hidden_fields=["conflicto_id", "usuario_id"],
        )
        await dialog.open()

    def _save_note_handler(
        self, record: Optional[Dict]
    ) -> Callable[[Dict], Awaitable[bool]]:
        async def _handler(data: Dict) -> bool:
            user_id = app.storage.user.get("user_id")
            if not user_id:
                ui.notify("Error: Usuario no identificado.", type="negative")
                return False
            data["conflicto_id"] = self.selected_conflict["id"]
            data["usuario_id"] = user_id

            if record:
                result = await self.api.update_record(
                    "diario_conflictos", record["id"], data
                )
                success = result is not None
            else:
                result, error = await self.api.create_record("diario_conflictos", data)
                success = result is not None

            if not success:
                return False

            conflict_update = {}
            if data.get("tarea_actual"):
                conflict_update["tarea_actual"] = data.get("tarea_actual")
            if data.get("estado"):
                if data["estado"] == "Cerrado":
                    conflict_update["estado"] = "Cerrado"
                    conflict_update["fecha_cierre"] = date.today().isoformat()
                else:
                    conflict_update["estado"] = data["estado"]
            if conflict_update:
                await self.api.update_record(
                    "conflictos", self.selected_conflict["id"], conflict_update
                )
            return True

        return _handler

    async def _on_note_saved(self):
        await self._load_conflicts()
        if self.selected_conflict:
            await self._on_conflict_change(self.selected_conflict["id"])

    def _delete_note(self, note: dict):
        async def _confirm_delete():
            if await self.api.delete_record("diario_conflictos", note["id"]):
                ui.notify("Nota eliminada con éxito.", type="positive")
                await self._load_conflict_history()

        ConfirmationDialog(
            title="Eliminar Nota",
            message=f"¿Estás seguro de que quieres eliminar la nota #{note.get('id')}?",
            on_confirm=_confirm_delete,
            confirm_button_text="Eliminar",
            confirm_button_color="negative",
        )

    def _clear_displays(self):
        if self.info_container:
            self.info_container.clear()
        if self.history_container:
            self.history_container.clear()
