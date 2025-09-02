from typing import Optional, List, Dict
from nicegui import ui
from api.client import APIClient
from state.conflicts_state import ConflictsState
from components.dialogs import ConflictNoteDialog


class ConflictsView:
    """Enhanced conflicts management view with a table-based layout and detail view."""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = ConflictsState()
        self.info_container = None
        self.history_container = None
        self.all_conflicts = []
        self.filtered_conflicts = []
        self.nodos_list = []
        self.filter_nodo = None
        self.filter_estado = None
        self.filter_causa = None
        self.filter_text = None

        # UI elements for view management
        self.conflicts_table = None
        self.list_view_container = None
        self.detail_view_container = None
        self.stats_card = None

    def create(self) -> ui.column:
        """Create the enhanced conflicts view UI with table and detail panels."""
        container = ui.column().classes("w-full p-4 gap-4")

        with container:
            ui.label("Toma de Actas - Gestión de Conflictos").classes("text-h4")

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
                        options={
                            "": "Todos los estados",
                            "Abierto": "Abierto",
                            "En proceso": "En proceso",
                            "Resuelto": "Resuelto",
                            "Cerrado": "Cerrado",
                        },
                        label="Filtrar por Estado",
                        value="",
                        on_change=self._apply_filters,
                    ).classes("w-48")
                    causa_options_list = [
                        "No renovación",
                        "Fianza",
                        "Acoso inmobiliario",
                        "Renta Antigua",
                        "Subida de alquiler",
                        "Individualización Calefacción",
                        "Reparaciones / Habitabilidad",
                        "Venta de la vivienda",
                        "Honorarios",
                        "Requerimiento de la casa para uso propio",
                        "Impago",
                        "Actualización del precio (IPC)",
                        "Negociación del contrato",
                    ]
                    causa_options = {
                        "": "Todas las causas",
                        **{opt: opt for opt in sorted(causa_options_list)},
                    }
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

            # --- LIST VIEW CONTAINER ---
            self.list_view_container = ui.column().classes("w-full gap-4")
            with self.list_view_container:
                with ui.row().classes("w-full justify-between items-center gap-4"):
                    self.stats_card = ui.card().classes("flex-grow p-4")
                    with ui.row().classes("gap-2 items-center"):
                        ui.button(
                            "Crear Conflicto",
                            icon="add_circle",
                            on_click=self._create_conflict,
                        ).props("color=green-600")
                        ui.button(icon="refresh", on_click=self._load_conflicts).props(
                            "flat"
                        ).tooltip("Refrescar lista")

                # Table of conflicts
                table_columns = [
                    {
                        "name": "id",
                        "label": "ID",
                        "field": "id",
                        "sortable": True,
                        "align": "left",
                        "classes": "w-1/12 font-bold",
                    },
                    {
                        "name": "estado",
                        "label": "Estado",
                        "field": "estado",
                        "sortable": True,
                        "align": "center",
                    },
                    {
                        "name": "direccion",
                        "label": "Dirección",
                        "field": lambda r: r.get("piso_direccion")
                        or r.get("bloque_direccion")
                        or "N/A",
                        "sortable": True,
                        "align": "left",
                        "classes": "w-4/12",
                    },
                    {
                        "name": "afiliada",
                        "label": "Afiliada",
                        "field": "afiliada_nombre_completo",
                        "sortable": True,
                        "align": "left",
                        "classes": "w-3/12",
                    },
                    {
                        "name": "causa",
                        "label": "Causa",
                        "field": "causa",
                        "sortable": True,
                        "align": "left",
                        "classes": "w-3/12",
                    },
                    {
                        "name": "fecha_apertura",
                        "label": "Apertura",
                        "field": "fecha_apertura",
                        "sortable": True,
                        "align": "left",
                    },
                ]
                self.conflicts_table = (
                    ui.table(
                        columns=table_columns,
                        rows=[],
                        row_key="id",
                        selection="single",
                        on_select=lambda e: self._on_table_row_select(e.selection),
                    )
                    .classes("w-full")
                    .props("flat bordered dense")
                )

                # Custom slots for better table cell rendering
                with self.conflicts_table.add_slot(
                    "body-cell-estado",
                    """<q-td :props="props" class="text-center"><q-badge :color="{'Abierto':'red', 'En proceso':'orange', 'Resuelto':'green', 'Cerrado':'grey'}[props.value] || 'blue'">{{ props.value }}</q-badge></q-td>""",
                ):
                    pass
                with self.conflicts_table.add_slot(
                    "body-cell-direccion",
                    """<q-td :props="props"><div class="truncate" style="max-width: 350px;" :title="props.value">{{ props.value }}</div></q-td>""",
                ):
                    pass

            # --- DETAIL VIEW CONTAINER (Initially hidden) ---
            self.detail_view_container = (
                ui.column().classes("w-full gap-4").set_visibility(False)
            )
            with self.detail_view_container:
                with ui.row().classes("w-full items-center"):
                    ui.button(
                        "Volver a la lista",
                        icon="arrow_back",
                        on_click=self._show_list_view,
                    ).props("flat")
                    ui.separator().props("vertical spaced")
                    ui.label().bind_text_from(
                        self.state,
                        "selected_conflict",
                        lambda c: (
                            f"Detalles del Conflicto ID: {c['id']}" if c else "Detalles"
                        ),
                    ).classes("text-h6")

                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("w-96 gap-4"):
                        ui.button(
                            "Añadir Nota", icon="add_comment", on_click=self._add_note
                        ).props("color=orange-600").classes("w-full")
                        self.info_container = ui.column().classes("w-full")
                    with ui.column().classes("flex-grow"):
                        self.history_container = ui.column().classes("w-full gap-4")

        ui.timer(0.5, self._initialize_data, once=True)
        return container

    def _show_list_view(self):
        """Switches the view to show the conflicts table."""
        self.state.set_selected_conflict(None)
        if self.conflicts_table:
            self.conflicts_table.selected.clear()
            self.conflicts_table.update()
        self.detail_view_container.set_visibility(False)
        self.list_view_container.set_visibility(True)

    def _show_detail_view(self):
        """Switches the view to show the selected conflict's details."""
        self.list_view_container.set_visibility(False)
        self.detail_view_container.set_visibility(True)

    async def _on_table_row_select(self, selection: List):
        """Handle conflict selection from the table."""
        if not selection:
            return
        conflict_id = selection[0]["id"]
        conflict = self.state.get_conflict_by_id(conflict_id)
        if conflict:
            self.state.set_selected_conflict(conflict)
            await self._display_conflict_info()
            await self._load_conflict_history()
            self._show_detail_view()

    async def _initialize_data(self):
        await self._load_nodos()
        await self._load_conflicts()

    async def _load_nodos(self):
        try:
            nodos = await self.api.get_records("nodos", order="nombre.asc")
            self.nodos_list = nodos
            nodo_options = {
                "": "Todos los nodos",
                **{nodo["id"]: nodo["nombre"] for nodo in nodos},
            }
            if self.filter_nodo:
                self.filter_nodo.set_options(nodo_options)
                self.filter_nodo.value = ""
        except Exception as e:
            ui.notify(f"Error al cargar nodos: {str(e)}", type="negative")

    async def _load_conflicts(self):
        try:
            conflicts = await self.api.get_records(
                "v_conflictos_enhanced", order="id.desc"
            )
            self.all_conflicts = conflicts
            await self._apply_filters()
        except Exception as e:
            ui.notify(f"Error al cargar conflictos: {str(e)}", type="negative")

    async def _apply_filters(self, _=None):
        """Apply all active filters to the conflicts list and update the table."""
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
                if any(
                    search_text in str(c.get(field, "")).lower()
                    for field in [
                        "piso_direccion",
                        "bloque_direccion",
                        "descripcion",
                        "afiliada_nombre_completo",
                        "causa",
                        "resolucion",
                        "id",
                    ]
                )
            ]

        self.filtered_conflicts = filtered
        self.state.set_conflicts(filtered)

        if self.conflicts_table is not None:
            self.conflicts_table.rows = filtered
            self.conflicts_table.update()

        if self.state.selected_conflict and self.state.selected_conflict["id"] not in {
            c["id"] for c in filtered
        }:
            ui.notify(
                "El conflicto seleccionado ha sido ocultado por los filtros.",
                type="info",
            )
            self._show_list_view()

        self._display_statistics()
        if len(filtered) < len(self.all_conflicts):
            ui.notify(
                f"Mostrando {len(filtered)} de {len(self.all_conflicts)} conflictos",
                type="info",
            )

    def _clear_filters(self):
        """Clear all filters and show all conflicts."""
        self.filter_nodo.value = ""
        self.filter_estado.value = ""
        self.filter_causa.value = ""
        self.filter_text.value = ""
        ui.timer(0.1, self._apply_filters, once=True)

    def _display_statistics(self):
        if not self.stats_card:
            return
        self.stats_card.clear()
        with self.stats_card:
            status_counts = {}
            for conflict in self.filtered_conflicts:
                estado = conflict.get("estado", "Sin estado")
                status_counts[estado] = status_counts.get(estado, 0) + 1
            with ui.row().classes("w-full gap-4 flex-wrap items-center"):
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

    async def _display_conflict_info(self):
        """Display enhanced conflict information in the detail view."""
        if not self.info_container or not self.state.selected_conflict:
            return
        self.info_container.clear()
        conflict = self.state.selected_conflict
        with self.info_container:
            with ui.card().classes("w-full mb-2"):
                ui.label("Datos del Conflicto").classes("text-subtitle2 font-bold mb-2")
                if conflict.get("estado"):
                    color = {
                        "Abierto": "red",
                        "En proceso": "orange",
                        "Resuelto": "green",
                        "Cerrado": "gray",
                    }.get(conflict["estado"], "blue")
                    ui.badge(conflict["estado"], color=color).props("outline")
                info_items = [
                    ("ID", "id"),
                    ("Afiliada", "afiliada_nombre_completo"),
                    ("Nº Afiliada", "num_afiliada"),
                    ("Ámbito", "ambito"),
                    ("Causa", "causa"),
                    ("Fecha Apertura", "fecha_apertura"),
                    ("Fecha Cierre", "fecha_cierre"),
                    ("Responsable", "usuario_responsable_alias"),
                ]
                for label, key in info_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        ui.label(str(conflict.get(key) or "N/A")).classes("flex-grow")
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
                    ("Nodo Territorial", "nodo_nombre"),
                    ("Dirección Piso", "piso_direccion"),
                    ("Dirección Bloque", "bloque_direccion"),
                    ("Municipio", "piso_municipio"),
                    ("Código Postal", "piso_cp"),
                ]
                for label, key in location_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        ui.label(str(conflict.get(key) or "N/A")).classes("flex-grow")

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
                    ui.label("No se encontraron entradas en el historial.").classes(
                        "text-gray-500"
                    )
        except Exception as e:
            ui.notify(f"Error al cargar el historial: {str(e)}", type="negative")

    def _create_history_entry(self, entry: dict):
        with ui.card().classes("w-full mb-2"):
            with ui.row().classes("w-full justify-between items-center mb-2"):
                with ui.column():
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("schedule", size="sm").classes("text-gray-500")
                        ui.label(entry.get("created_at", "Sin fecha")).classes(
                            "text-caption text-gray-600"
                        )
                    if entry.get("autor_nota_alias"):
                        with ui.row().classes("items-center gap-2 mt-1"):
                            ui.icon("person", size="sm").classes("text-gray-500")
                            ui.label(f"Por: {entry['autor_nota_alias']}").classes(
                                "text-caption text-blue-600"
                            )
                with ui.row().classes("gap-2"):
                    ui.button(
                        icon="edit", on_click=lambda e=entry: self._edit_note(e)
                    ).props("size=sm flat dense").tooltip("Editar nota")
                    ui.button(
                        icon="delete", on_click=lambda e=entry: self._delete_note(e)
                    ).props("size=sm flat dense color=negative").tooltip(
                        "Eliminar nota"
                    )
            with ui.row().classes("gap-2 mb-2"):
                if entry.get("estado"):
                    ui.badge(
                        f"Estado: {entry['estado']}",
                        color={
                            "Abierto": "red",
                            "En proceso": "orange",
                            "Resuelto": "green",
                            "Cerrado": "gray",
                        }.get(entry["estado"], "blue"),
                    ).props("outline")
                if entry.get("accion_nombre"):
                    ui.badge(f"Acción: {entry['accion_nombre']}", color="purple").props(
                        "outline"
                    )
                if entry.get("ambito"):
                    ui.badge(f"Ámbito: {entry['ambito']}", color="indigo").props(
                        "outline"
                    )
            if entry.get("notas"):
                ui.separator().classes("my-2")
                with ui.row().classes("w-full"):
                    ui.icon("notes", size="sm").classes("text-gray-500 mt-1")
                    with ui.column().classes("flex-grow ml-2"):
                        ui.label("Nota:").classes("font-semibold text-sm")
                        ui.label(entry["notas"]).classes(
                            "text-gray-700 whitespace-pre-wrap"
                        )

    async def _add_note(self):
        if not self.state.selected_conflict:
            ui.notify("Por favor, seleccione un conflicto primero.", type="warning")
            return
        dialog = ConflictNoteDialog(
            api=self.api,
            conflict=self.state.selected_conflict,
            on_success=self._on_note_added,
            mode="create",
        )
        await dialog.open()

    async def _on_note_added(self):
        """Callback after a note is successfully added."""
        await self._load_conflicts()
        # Find the currently selected conflict in the new list to refresh its data
        if self.state.selected_conflict:
            new_conflict_data = self.state.get_conflict_by_id(
                self.state.selected_conflict["id"]
            )
            if new_conflict_data:
                self.state.set_selected_conflict(new_conflict_data)
                await self._display_conflict_info()  # Refresh info panel
            await self._load_conflict_history()  # Refresh history panel

    async def _create_conflict(self):
        from components.dialogs import EnhancedRecordDialog

        dialog = EnhancedRecordDialog(
            api=self.api,
            table="conflictos",
            mode="create",
            on_success=self._load_conflicts,
        )
        await dialog.open()

    async def _edit_note(self, note: dict):
        dialog = ConflictNoteDialog(
            api=self.api,
            conflict=self.state.selected_conflict,
            record=note,
            on_success=self._load_conflict_history,
            mode="edit",
        )
        await dialog.open()

    async def _delete_note(self, note: dict):
        note_id = note.get("id")
        with ui.dialog() as dialog, ui.card():
            ui.label(f"¿Eliminar nota #{note_id}?").classes("text-h6")
            ui.label("Esta acción no se puede deshacer.").classes(
                "text-body2 text-gray-600"
            )
            if note.get("notas"):
                ui.separator().classes("my-2")
                note_preview = (
                    note["notas"][:100] + "..."
                    if len(note["notas"]) > 100
                    else note["notas"]
                )
                ui.label(f'Nota: "{note_preview}"').classes(
                    "text-caption text-gray-500"
                )
            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancelar", on_click=dialog.close).props("flat")

                async def confirm_delete():
                    if await self.api.delete_record("diario_conflictos", note_id):
                        ui.notify("Nota eliminada.", type="positive")
                        dialog.close()
                        await self._load_conflict_history()

                ui.button("Eliminar", on_click=confirm_delete).props("color=negative")
        await dialog
