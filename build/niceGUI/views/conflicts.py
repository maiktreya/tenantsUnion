from typing import Optional, List, Dict
from nicegui import ui
from api.client import APIClient
from state.conflicts_state import ConflictsState
from components.dialogs import ConflictNoteDialog


class ConflictsView:
    """Enhanced conflicts management view with address display and node filtering"""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = ConflictsState()
        self.conflict_select = None
        self.info_container = None
        self.history_container = None
        self.all_conflicts = []  # Store all conflicts for filtering
        self.filtered_conflicts = []  # Store filtered results
        self.nodos_list = []  # Store available nodes
        self.filter_nodo = None
        self.filter_estado = None
        self.filter_causa = None  # New filter for 'causa'
        self.filter_text = None

    def create(self) -> ui.column:
        """Create the enhanced conflicts view UI"""
        container = ui.column().classes("w-full p-4 gap-4")

        with container:
            ui.label("Toma de Actas - Gestión de Conflictos").classes("text-h4")

            # Filter Section
            with ui.expansion("Filtros", icon="filter_list").classes(
                "w-full mb-4"
            ).props("default-opened"):
                with ui.row().classes("w-full gap-4 flex-wrap items-center"):
                    # Node filter
                    self.filter_nodo = ui.select(
                        options={},
                        label="Filtrar por Nodo",
                        on_change=self._apply_filters,
                        clearable=True,
                    ).classes("w-64")

                    # State filter
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

                    # --- NEW: Causa filter based on your CSV ---
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
                    # Create a sorted dictionary for the options
                    causa_options = {"": "Todas las causas"}
                    causa_options.update(
                        {opt: opt for opt in sorted(causa_options_list)}
                    )

                    self.filter_causa = ui.select(
                        options=causa_options,
                        label="Filtrar por Causa",
                        on_change=self._apply_filters,
                        clearable=True,
                    ).classes("w-64")
                    # --- END NEW FILTER ---

                    # Text search (now searches everything)
                    self.filter_text = (
                        ui.input(label="Búsqueda global", on_change=self._apply_filters)
                        .classes("flex-grow min-w-[16rem]")
                        .props("clearable")
                    )

                    # Clear filters button
                    ui.button(
                        "Limpiar Filtros",
                        icon="clear_all",
                        on_click=self._clear_filters,
                    ).props("flat color=orange-600")

            with ui.row().classes("w-full gap-4"):
                # Left panel - Selection and info
                with ui.column().classes("w-96 gap-4"):
                    # Conflict selector with enhanced display
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

                    # Statistics card
                    self.stats_card = ui.card().classes("w-full p-4")
                    self._display_statistics()

                    # Action buttons
                    with ui.row().classes("w-full gap-2"):
                        ui.button(
                            "Añadir Nota", icon="add_comment", on_click=self._add_note
                        ).props("color=orange-600").classes("flex-grow")

                        ui.button(
                            "Crear Conflicto",
                            icon="add_circle",
                            on_click=self._create_conflict,
                        ).props("color=green-600").classes("flex-grow")

                    # Conflict info container
                    self.info_container = ui.column().classes("w-full")

                # Right panel - History
                with ui.column().classes("flex-grow"):
                    self.history_container = ui.column().classes("w-full gap-4")

        # Load data on startup
        ui.timer(0.5, self._initialize_data, once=True)

        return container

    async def _initialize_data(self):
        """Initialize all necessary data"""
        await self._load_nodos()
        await self._load_conflicts()

    async def _load_nodos(self):
        """Load available nodes for filtering"""
        try:
            nodos = await self.api.get_records("nodos", order="nombre.asc")
            self.nodos_list = nodos

            # Update filter options
            nodo_options = {"": "Todos los nodos"}
            for nodo in nodos:
                nodo_options[nodo["id"]] = nodo["nombre"]

            if self.filter_nodo:
                self.filter_nodo.set_options(nodo_options)
                self.filter_nodo.value = ""

        except Exception as e:
            ui.notify(f"Error al cargar nodos: {str(e)}", type="negative")

    async def _load_conflicts(self):
        """Load all conflicts with enhanced information"""
        try:
            # Use the enhanced view for complete information
            conflicts = await self.api.get_records(
                "v_conflictos_enhanced", order="id.desc"
            )

            self.all_conflicts = conflicts
            self.filtered_conflicts = conflicts
            self.state.set_conflicts(conflicts)

            # Apply existing filters if any
            await self._apply_filters()

            self._display_statistics()

        except Exception as e:
            ui.notify(f"Error al cargar conflictos: {str(e)}", type="negative")

    def _get_conflict_options(self, conflicts: List[Dict]) -> Dict[int, str]:
        """Generate conflict options with address for select dropdown"""
        options = {}
        for conflict in conflicts:
            # Use the pre-computed label from the view, or build it
            if conflict.get("conflict_label"):
                label = conflict["conflict_label"]
            else:
                # Fallback label construction
                conflict_id = conflict["id"]
                direccion = (
                    conflict.get("piso_direccion")
                    or conflict.get("bloque_direccion")
                    or "Sin dirección"
                )
                afiliada = conflict.get("afiliada_nombre_completo", "Sin afiliada")
                estado = conflict.get("estado", "")

                label = f"ID {conflict_id} - {direccion}"
                if afiliada != "Sin afiliada":
                    label += f" | {afiliada}"
                if estado:
                    label += f" [{estado}]"

            options[conflict["id"]] = label

        return options

    async def _apply_filters(self, _=None):
        """Apply all active filters to the conflicts list"""
        filtered = self.all_conflicts.copy()

        # Filter by node
        if self.filter_nodo and self.filter_nodo.value:
            nodo_id = self.filter_nodo.value
            filtered = [c for c in filtered if c.get("nodo_id") == nodo_id]

        # Filter by state
        if self.filter_estado and self.filter_estado.value:
            estado = self.filter_estado.value
            filtered = [c for c in filtered if c.get("estado") == estado]

        # --- NEW: Filter by causa ---
        if self.filter_causa and self.filter_causa.value:
            causa = self.filter_causa.value
            filtered = [c for c in filtered if c.get("causa") == causa]

        # Filter by text search (searches multiple fields)
        if self.filter_text and self.filter_text.value:
            search_text = self.filter_text.value.lower()
            filtered = [
                c
                for c in filtered
                if (
                    search_text in str(c.get("piso_direccion", "")).lower()
                    or search_text in str(c.get("bloque_direccion", "")).lower()
                    or search_text in str(c.get("descripcion", "")).lower()
                    or search_text in str(c.get("afiliada_nombre_completo", "")).lower()
                    or search_text in str(c.get("causa", "")).lower()
                    or search_text in str(c.get("resolucion", "")).lower()
                    or search_text in str(c.get("id", "")).lower()
                )
            ]

        self.filtered_conflicts = filtered
        self.state.set_conflicts(filtered)

        # Update select options
        options = self._get_conflict_options(filtered)
        if self.conflict_select:
            self.conflict_select.set_options(options)

            # Clear selection if current selection is filtered out
            if self.state.selected_conflict_id.value not in options:
                self.conflict_select.value = None
                self.state.set_selected_conflict(None)
                self._clear_displays()

        self._display_statistics()

        # Show filter results
        total = len(self.all_conflicts)
        filtered_count = len(filtered)
        if filtered_count < total:
            ui.notify(f"Mostrando {filtered_count} de {total} conflictos", type="info")

    def _clear_filters(self):
        """Clear all filters and show all conflicts"""
        if self.filter_nodo:
            self.filter_nodo.value = ""
        if self.filter_estado:
            self.filter_estado.value = ""
        if self.filter_causa:  # --- NEW ---
            self.filter_causa.value = ""
        if self.filter_text:
            self.filter_text.value = ""

        # Use a small timer to ensure value propagation before applying filters
        ui.timer(0.1, self._apply_filters, once=True)

    def _display_statistics(self):
        """Display conflict statistics in the stats card"""
        if not self.stats_card:
            return

        self.stats_card.clear()

        with self.stats_card:
            ui.label("Estadísticas").classes("text-h6 mb-2")

            total = len(self.filtered_conflicts)

            # Count by status
            status_counts = {}
            for conflict in self.filtered_conflicts:
                estado = conflict.get("estado", "Sin estado")
                status_counts[estado] = status_counts.get(estado, 0) + 1

            # Display counts
            with ui.row().classes("w-full gap-4 flex-wrap"):
                ui.chip(f"Total: {total}", color="blue", icon="inventory")

                for estado, count in sorted(status_counts.items()):
                    color_map = {
                        "Abierto": "red",
                        "En proceso": "orange",
                        "Resuelto": "green",
                        "Cerrado": "gray",
                    }
                    color = color_map.get(estado, "blue")
                    ui.chip(f"{estado}: {count}", color=color)

    async def _on_conflict_change(self, conflict_id: Optional[int]):
        """Handle conflict selection change"""
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
        """Display enhanced conflict information"""
        if not self.info_container or not self.state.selected_conflict:
            return

        self.info_container.clear()
        conflict = self.state.selected_conflict

        with self.info_container:
            ui.label("Información del Conflicto").classes("text-h6 mb-2")

            # Main conflict information card
            with ui.card().classes("w-full mb-2"):
                ui.label("Datos del Conflicto").classes("text-subtitle2 font-bold mb-2")

                # Status badge
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
                    ("ID", conflict.get("id", "N/A")),
                    ("Afiliada", conflict.get("afiliada_nombre_completo", "N/A")),
                    ("Nº Afiliada", conflict.get("num_afiliada", "N/A")),
                    ("Ámbito", conflict.get("ambito", "N/A")),
                    ("Causa", conflict.get("causa", "N/A")),
                    ("Fecha Apertura", conflict.get("fecha_apertura", "N/A")),
                    ("Fecha Cierre", conflict.get("fecha_cierre", "N/A")),
                    ("Responsable", conflict.get("usuario_responsable_alias", "N/A")),
                ]

                for label, value in info_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        ui.label(str(value) if value else "N/A").classes("flex-grow")

                # Description
                if conflict.get("descripcion"):
                    ui.separator().classes("my-2")
                    ui.label("Descripción:").classes("font-bold")
                    ui.label(conflict.get("descripcion")).classes("text-gray-700")

                # Resolution
                if conflict.get("resolucion"):
                    ui.separator().classes("my-2")
                    ui.label("Resolución:").classes("font-bold")
                    ui.label(conflict.get("resolucion")).classes("text-green-700")

            # Location card with complete information
            with ui.card().classes("w-full"):
                ui.label("Información de Ubicación").classes(
                    "text-subtitle2 font-bold mb-2"
                )

                location_items = [
                    ("Nodo Territorial", conflict.get("nodo_nombre", "N/A")),
                    ("Dirección Piso", conflict.get("piso_direccion", "N/A")),
                    ("Dirección Bloque", conflict.get("bloque_direccion", "N/A")),
                    ("Municipio", conflict.get("piso_municipio", "N/A")),
                    ("Código Postal", conflict.get("piso_cp", "N/A")),
                ]

                for label, value in location_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        ui.label(str(value) if value else "N/A").classes("flex-grow")

    async def _load_conflict_history(self):
        """Load history for selected conflict"""
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
            ui.notify(f"Error al cargar el historial: {str(e)}", type="negative")

    def _create_history_entry(self, entry: dict):
        """Create history entry card"""
        with ui.card().classes("w-full mb-2"):
            # Header
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

                # Actions
                with ui.row().classes("gap-2"):
                    ui.button(
                        icon="edit", on_click=lambda e=entry: self._edit_note(e)
                    ).props("size=sm flat dense").tooltip("Editar nota")

                    ui.button(
                        icon="delete", on_click=lambda e=entry: self._delete_note(e)
                    ).props("size=sm flat dense color=negative").tooltip(
                        "Eliminar nota"
                    )

            # Badges
            with ui.row().classes("gap-2 mb-2"):
                if entry.get("estado"):
                    color_map = {
                        "Abierto": "red",
                        "En proceso": "orange",
                        "Resuelto": "green",
                        "Cerrado": "gray",
                    }
                    color = color_map.get(entry["estado"], "blue")
                    ui.badge(f"Estado: {entry['estado']}", color=color).props("outline")

                if entry.get("accion_nombre"):
                    ui.badge(f"Acción: {entry['accion_nombre']}", color="purple").props(
                        "outline"
                    )

                if entry.get("ambito"):
                    ui.badge(f"Ámbito: {entry['ambito']}", color="indigo").props(
                        "outline"
                    )

            # Note content
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
        """Add a new note to the selected conflict"""
        if not self.state.selected_conflict:
            ui.notify("Por favor, seleccione un conflicto primero", type="warning")
            return

        async def on_note_added():
            await self._load_conflicts()
            await self._on_conflict_change(self.state.selected_conflict["id"])

        dialog = ConflictNoteDialog(
            api=self.api,
            conflict=self.state.selected_conflict,
            on_success=on_note_added,
            mode="create",
        )
        await dialog.open()

    async def _create_conflict(self):
        """Open dialog to create a new conflict"""
        from components.dialogs import EnhancedRecordDialog

        async def on_conflict_created():
            await self._load_conflicts()
            ui.notify("Conflicto creado exitosamente", type="positive")

        dialog = EnhancedRecordDialog(
            api=self.api,
            table="conflictos",
            mode="create",
            on_success=on_conflict_created,
        )
        await dialog.open()

    async def _edit_note(self, note: dict):
        """Edit an existing note"""

        async def on_note_updated():
            await self._load_conflict_history()

        dialog = ConflictNoteDialog(
            api=self.api,
            conflict=self.state.selected_conflict,
            record=note,
            on_success=on_note_updated,
            mode="edit",
        )
        await dialog.open()

    async def _delete_note(self, note: dict):
        """Delete a note with confirmation"""
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

                async def confirm():
                    success = await self.api.delete_record("diario_conflictos", note_id)
                    if success:
                        ui.notify("Nota eliminada con éxito", type="positive")
                        dialog.close()
                        await self._load_conflict_history()

                ui.button("Eliminar", on_click=confirm).props("color=negative")

        dialog.open()

    def _clear_displays(self):
        """Clear info and history displays"""
        if self.info_container:
            self.info_container.clear()
        if self.history_container:
            self.history_container.clear()
