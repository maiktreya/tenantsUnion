# build/niceGUI/views/conflicts.py

from typing import Optional, List, Dict, Awaitable, Callable
from datetime import date
import unicodedata  # <-- Added for tilde normalization
from nicegui import ui, app
from collections import Counter

from api.client import APIClient
from state.app_state import AppState, GenericViewState
from components.base_view import BaseView
from components.dialogs import EnhancedRecordDialog, ConfirmationDialog
from config import TABLE_INFO


class ConflictsView(BaseView):
    """Enhanced conflicts management view using client-side (per-tab) state."""

    def __init__(self, api_client: APIClient, state: AppState):
        self.api = api_client
        self.global_state = state  
        if "conflicts_view_state" not in app.storage.client:
            client_state = GenericViewState()  
            client_state.history = []  
            app.storage.client["conflicts_view_state"] = client_state
        self.state: GenericViewState = app.storage.client["conflicts_view_state"]
        
        # Cache for holding unfiltered select options to keep track during text filtering
        self.unfiltered_conflict_options: Dict[int, str] = {} 
        
        self.history_container = None
        self.info_container = None
        self.conflict_select = None
        self.stats_card = None
        self.filter_nodo = None
        self.filter_estado = None
        self.filter_causa = None
        self.filter_ambito = None  
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
            ambito_opts_list = conflict_options.get("ambito", [])  
            
            estado_options = {
                "": "Todos los estados",
                **{opt: opt for opt in estado_opts_list},
            }
            causa_options = {
                "": "Todas las causas",
                **{opt: opt for opt in causa_opts_list},
            }
            ambito_options = {  
                "": "Todos los ámbitos",
                **{opt: opt for opt in ambito_opts_list},
            }

            with ui.expansion("Filtros", icon="filter_list").classes(
                "w-full mb-4"
            ).props("default-opened"):
                with ui.row().classes("w-full gap-4 flex-wrap items-center"):
                    self.filter_nodo = ui.select(
                        options=nodo_options,
                        label="Filtrar por Nodo",
                        value=self.state.filters.get("nodo_id"),
                        on_change=self._apply_filters,
                        clearable=True,
                    ).classes("w-64")
                    self.filter_estado = ui.select(
                        options=estado_options,
                        label="Filtrar por Estado",
                        value=self.state.filters.get("estado", ""),
                        on_change=self._apply_filters,
                    ).classes("w-48")
                    self.filter_causa = ui.select(
                        options=causa_options,
                        label="Filtrar por Causa",
                        value=self.state.filters.get("causa"),
                        on_change=self._apply_filters,
                        clearable=True,
                    ).classes("w-64")
                    self.filter_ambito = ui.select(  
                        options=ambito_options,
                        label="Filtrar por Ámbito",
                        value=self.state.filters.get("ambito"),
                        on_change=self._apply_filters,
                        clearable=True,
                    ).classes("w-48")
                    self.filter_text = (
                        ui.input(
                            label="Búsqueda global",
                            value=self.state.filters.get("global_search"),
                            on_change=self._apply_filters,
                        )
                        .classes("flex-grow min-w-[16rem]")
                        .props("clearable")
                    )
                    ui.button(
                        "Limpiar Filtros",
                        icon="clear_all",
                        on_click=self._clear_filters,
                    ).props("flat color=orange-600")

            # Enhanced full-width conflict selector bar with custom tilde-insensitive event filters
            with ui.row().classes("w-full gap-2 items-center"):
                self.conflict_select = (
                    ui.select(
                        options={},
                        label="Seleccionar Conflicto",
                        value=self.state.selected_item.value,
                        on_change=lambda e: self._on_conflict_change(e.value),
                        clearable=True,
                    )
                    .classes("flex-grow")
                    .props("use-input")
                    .on("input-value", self._filter_conflict_options)
                    .on("focus", lambda: self.conflict_select.set_options(self.unfiltered_conflict_options))
                )
                ui.button(icon="refresh", on_click=self._load_conflicts).props("flat")

            with ui.row().classes("w-full gap-4 items-start flex-wrap md:flex-nowrap"):
                with ui.column().classes("w-full md:w-96 md:shrink-0 gap-4"):
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
                with ui.column().classes("w-full md:flex-grow"):
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

            if self.state.selected_item.value:
                await self._on_conflict_change(self.state.selected_item.value.get("id"))

        except Exception as e:
            ui.notify(f"Error loading conflicts: {str(e)}", type="negative")

    def _get_conflict_options(self, conflicts: List[Dict]) -> Dict[int, str]:
        options = {}
        for c in conflicts:
            ambito = c.get("ambito") or "Sin ámbito"
            nodo = c.get("nodo_nombre") or "Sin nodo"
            nombre = c.get("afiliada_nombre_completo") or "Sin afiliada"
            direccion = c.get("piso_direccion") or c.get("bloque_direccion") or "Sin dirección"
            
            fecha_raw = c.get("fecha_apertura")
            fecha = str(fecha_raw).split("T")[0] if fecha_raw else "Sin fecha"
            
            act_raw = c.get("ultima_actualizacion")
            actualizado = str(act_raw).split("T")[0] if act_raw else "Sin act."
            
            options[c["id"]] = f"[{ambito}] [{nodo}] (Apertura: {fecha} | Act: {actualizado}) {nombre}, {direccion}"
            
        return options

    def _normalize_string(self, text: str) -> str:
        """Helper method to remove accents/tildes and convert to lowercase."""
        if not text:
            return ""
        normalized = unicodedata.normalize("NFD", str(text).lower())
        return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

    def _filter_conflict_options(self, e):
        """Filters options accent-insensitively from Python side as the user types."""
        needle = self._normalize_string(e.args).strip()
        if not needle:
            self.conflict_select.set_options(self.unfiltered_conflict_options)
            return
            
        filtered = {
            k: v for k, v in self.unfiltered_conflict_options.items()
            if needle in self._normalize_string(v)
        }
        self.conflict_select.set_options(filtered)

    async def _apply_filters(self, _=None):
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
            "ambito": (  
                self.filter_ambito.value
                if self.filter_ambito and self.filter_ambito.value
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
        self.unfiltered_conflict_options = options  # Update cache
        
        if self.conflict_select:
            self.conflict_select.set_options(options)
            current_selection_id = (
                self.state.selected_item.value.get("id")
                if self.state.selected_item.value
                else None
            )
            if current_selection_id and current_selection_id not in options:
                self.state.selected_item.set(None)
                self.conflict_select.value = None
                self._clear_displays()

        self._display_statistics()

    def _clear_filters(self):
        self.filter_nodo.value = None
        self.filter_estado.value = ""
        self.filter_causa.value = None
        self.filter_ambito.value = None  
        self.filter_text.value = ""
        ui.timer(0.1, self._apply_filters, once=True)

    def _display_statistics(self):
        if not self.stats_card:
            return
        self.stats_card.clear()
        with self.stats_card:
            ui.label("Estadísticas").classes("text-h6 mb-2")
            status_counts = Counter(
                (c.get("estado") or "Sin estado") for c in self.state.filtered_records
            )
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
        if not conflict_id:
            self.state.selected_item.set(None)
            self._clear_displays()
            return
        conflict = next(
            (c for c in self.state.records if c.get("id") == conflict_id), None
        )
        if conflict:
            self.state.selected_item.set(conflict)
            # Restore the complete options list on selection change so the full list is ready when reopened
            self.conflict_select.set_options(self.unfiltered_conflict_options)
            await self._display_conflict_info()
            await self._load_conflict_history()

    async def _display_conflict_info(self):
        selected_conflict = self.state.selected_item.value
        if not self.info_container or not selected_conflict:
            return
        self.info_container.clear()
        with self.info_container:
            ui.label("Información del Conflicto").classes("text-h6 mb-2")
            with ui.card().classes("w-full mb-2"):
                ui.label("Datos del Conflicto").classes("text-subtitle2 font-bold mb-2")
                if selected_conflict.get("estado"):
                    color = {
                        "Abierto": "red",
                        "Victoria": "green",
                        "Cerrado": "gray",
                    }.get(selected_conflict["estado"], "blue")
                    ui.badge(selected_conflict["estado"], color=color).props("outline")
                info_items = [
                    ("Ámbito", selected_conflict.get("ambito")),
                    ("Contacto", selected_conflict.get("afiliada_nombre_completo")),
                    ("Causa", selected_conflict.get("causa")),
                    ("Fecha Apertura", selected_conflict.get("fecha_apertura")),
                    ("Fecha Cierre", selected_conflict.get("fecha_cierre")),
                    ("Tarea Actual", selected_conflict.get("tarea_actual")),
                ]
                for label, value in info_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        ui.label(
                            str(value) if value not in [None, ""] else "-"
                        ).classes("flex-grow")
                if selected_conflict.get("descripcion"):
                    ui.separator().classes("my-2")
                    ui.label("Descripción:").classes("font-bold")
                    ui.label(selected_conflict["descripcion"]).classes("text-gray-700")
                if selected_conflict.get("resolucion"):
                    ui.separator().classes("my-2")
                    ui.label("Resolución:").classes("font-bold")
                    ui.label(selected_conflict["resolucion"]).classes("text-green-700")
            with ui.card().classes("w-full"):
                ui.label("Información de Ubicación").classes(
                    "text-subtitle2 font-bold mb-2"
                )
                location_items = [
                    ("Nodo Territorial", selected_conflict.get("nodo_nombre")),
                    ("Dirección Piso", selected_conflict.get("piso_direccion")),
                    ("Dirección Bloque", selected_conflict.get("bloque_direccion")),
                ]
                for label, value in location_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        ui.label(
                            str(value) if value not in [None, ""] else "-"
                        ).classes("flex-grow")

    async def _load_conflict_history(self):
        selected_conflict = self.state.selected_item.value
        if not self.history_container or not selected_conflict:
            return
        self.history_container.clear()
        try:
            history_records = await self.api.get_records(
                "v_diario_conflictos_con_afiliada",
                {"conflicto_id": f'eq.{selected_conflict["id"]}'},
                order="created_at.desc",
            )
            self.state.history = history_records
            with self.history_container:
                ui.label("Historial del conflicto").classes(
                    "text-subtitle1 font-semibold mb-2"
                )
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
        title = f"{entry.get('created_at', 'Sin fecha').split('T')[0]}"
        if entry.get("usuario_alias"):
            title += f" |-----| AUTOR: {entry['usuario_alias']}"
        if entry.get("accion"):
            title += f" | ACCION: {entry['accion']}"
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
        selected_conflict = self.state.selected_item.value
        if not selected_conflict:
            return ui.notify(
                "Por favor, seleccione un conflicto primero.", type="warning"
            )
        initial_record = {
            "conflicto_id": selected_conflict["id"],
            "usuario_id": app.storage.user.get("user_id"),
            "estado": selected_conflict.get("estado"),
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
        class ConflictCreateDialog(EnhancedRecordDialog):
            async def _create_inputs(self_dialog):
                await super()._create_inputs()
                self_dialog.inputs["primera_tarea"] = ui.textarea(
                    label="Primera Tarea (se añadirá al diario automáticamente)", 
                    value=""
                ).classes("w-full")

        async def _handle_save(data: dict) -> bool:
            missing_fields = []
            if not data.get("ambito"):
                missing_fields.append("Ámbito")
            if not data.get("afiliada_id"):
                missing_fields.append("Contacto")
            if not data.get("descripcion") or str(data.get("descripcion")).strip() == "":
                missing_fields.append("Descripción")
                
            if missing_fields:
                ui.notify(
                    f"Faltan campos obligatorios: {', '.join(missing_fields)}", 
                    type="warning",
                    position="top"
                )
                return False 
            primera_tarea = data.pop("primera_tarea", None)
            data["estado"] = "Abierto"
            if primera_tarea:
                data["tarea_actual"] = primera_tarea
            result, error = await self.api.create_record("conflictos", data)
            if not result:
                ui.notify(f"Error al crear conflicto: {error}", type="negative")
                return False
            if primera_tarea:
                user_id = app.storage.user.get("user_id")
                nota_data = {
                    "conflicto_id": result["id"],
                    "usuario_id": user_id,
                    "estado": "Abierto", 
                    "tarea_actual": primera_tarea,
                    "accion": "Inicio del conflicto", 
                    "notas": "Generado automáticamente al abrir el conflicto."
                }
                note_result, note_error = await self.api.create_record("diario_conflictos", nota_data)
                if not note_result:
                    ui.notify(f"Conflicto creado, pero falló la nota: {note_error}", type="warning")
                    return True 
                
            ui.notify("Conflicto creado con éxito.", type="positive")
            return True

        dialog = ConflictCreateDialog(
            api=self.api,
            table="conflictos",
            mode="create",
            record={"ambito": "Afiliada"}, 
            on_success=self._load_conflicts,
            on_save=_handle_save, 
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
            selected_conflict = self.state.selected_item.value
            user_id = app.storage.user.get("user_id")
            if not user_id or not selected_conflict:
                ui.notify(
                    "Error: Usuario o conflicto no identificado.", type="negative"
                )
                return False
            data["conflicto_id"] = selected_conflict["id"]
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
                if data["estado"] in ["Cerrado", "Victoria"]:
                    conflict_update["estado"] = data["estado"]
                    conflict_update["fecha_cierre"] = date.today().isoformat()
                else:
                    conflict_update["estado"] = data["estado"]
                    conflict_update["fecha_cierre"] = None  
            if conflict_update:
                await self.api.update_record(
                    "conflictos", selected_conflict["id"], conflict_update
                )
            return True

        return _handler

    async def _on_note_saved(self):
        await self._load_conflicts()
        if self.state.selected_item.value:
            await self._on_conflict_change(self.state.selected_item.value["id"])

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