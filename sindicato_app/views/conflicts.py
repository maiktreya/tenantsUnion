from typing import Optional
from nicegui import ui
from api.client import APIClient
from state.conflicts_state import ConflictsState
from components.dialogs import ConflictNoteDialog


class ConflictsView:
    """Conflicts management view"""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.state = ConflictsState()
        self.conflict_select = None
        self.info_container = None
        self.history_container = None

    def create(self) -> ui.column:
        """Create the conflicts view UI"""
        container = ui.column().classes("w-full p-4 gap-4")

        with container:
            ui.label("Toma de actas").classes("text-h4")

            with ui.row().classes("w-full gap-4"):
                # Left panel - Selection and info
                with ui.column().classes("w-96 gap-4"):
                    # Conflict selector
                    with ui.row().classes("w-full gap-2"):
                        self.conflict_select = ui.select(
                            options={},
                            label="Seleccionar Conflicto",
                            on_change=lambda e: ui.timer(
                                0.1,
                                lambda: self._on_conflict_change(e.value),
                                once=True,
                            ),
                        ).classes("flex-grow")

                        ui.button(
                            icon="refresh",
                            on_click=lambda: ui.timer(
                                0.1, self._load_conflicts, once=True
                            ),
                        ).props("flat")

                    # Add note button
                    ui.button(
                        "Añadir Nota", icon="add_comment", on_click=self._add_note
                    ).props("color=orange-600").classes("w-full")

                    # Conflict info container
                    self.info_container = ui.column().classes("w-full")

                # Right panel - History
                with ui.column().classes("flex-grow"):
                    self.history_container = ui.column().classes("w-full gap-4")

        # Load conflicts on startup
        ui.timer(0.5, self._load_conflicts, once=True)

        return container

    async def _load_conflicts(self):
        """Load all conflicts"""
        try:
            # Fetch from the view that includes nodo information
            conflicts = await self.api.get_records(
                "v_conflictos_con_nodo", order="id.desc"
            )
            self.state.set_conflicts(conflicts)

            # Update select options
            options = self.state.get_conflict_options()
            if self.conflict_select:
                self.conflict_select.set_options(options)

            # ui.notify(f"Se cargaron {len(conflicts)} conflictos", type="positive")
        except Exception as e:
            ui.notify(f"Error al cargar conflictos: {str(e)}", type="negative")

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
        """Display information about the selected conflict with location details"""
        if not self.info_container or not self.state.selected_conflict:
            return

        self.info_container.clear()
        conflict = self.state.selected_conflict

        with self.info_container:
            ui.label("Información del Conflicto").classes("text-h6 mb-2")

            # Main conflict information card
            with ui.card().classes("w-full mb-2"):
                ui.label("Datos del Conflicto").classes("text-subtitle2 font-bold mb-2")

                info_items = [
                    ("ID", conflict.get("id", "N/A")),
                    ("Estado", conflict.get("estado", "N/A")),
                    ("Afiliada", conflict.get("afiliada_nombre_completo", "N/A")),
                    ("Ámbito", conflict.get("ambito", "N/A")),
                    ("Causa", conflict.get("causa", "N/A")),
                    ("Fecha de Apertura", conflict.get("fecha_apertura", "N/A")),
                    ("Fecha de Cierre", conflict.get("fecha_cierre", "N/A")),
                    ("Usuario Responsable", conflict.get("usuario_responsable_alias", "N/A")),
                ]

                for label, value in info_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        ui.label(str(value) if value else "N/A").classes("flex-grow")

                # Description in a separate section if it exists
                if conflict.get("descripcion"):
                    ui.separator().classes("my-2")
                    ui.label("Descripción:").classes("font-bold")
                    ui.label(conflict.get("descripcion")).classes("text-gray-700")

            # Location information card
            with ui.card().classes("w-full"):
                ui.label("Información de Ubicación").classes("text-subtitle2 font-bold mb-2")

                # Try to get additional location info if the affiliate has a piso_id
                location_items = [
                    ("Nodo Territorial", conflict.get("nodo_nombre", "N/A")),
                    ("Dirección del Piso", conflict.get("direccion_piso", "N/A")),
                ]

                # If we have a piso direction, try to extract more info
                if conflict.get("direccion_piso"):
                    try:
                        # Try to fetch piso details for CP and municipality
                        if conflict.get("afiliada_id"):
                            afiliada_records = await self.api.get_records(
                                "afiliadas",
                                {"id": f"eq.{conflict['afiliada_id']}"}
                            )
                            if afiliada_records and afiliada_records[0].get("piso_id"):
                                piso_records = await self.api.get_records(
                                    "pisos",
                                    {"id": f"eq.{afiliada_records[0]['piso_id']}"}
                                )
                                if piso_records:
                                    piso = piso_records[0]
                                    location_items.extend([
                                        ("Municipio", piso.get("municipio", "N/A")),
                                        ("Código Postal", piso.get("cp", "N/A")),
                                    ])

                                    # Try to get block info
                                    if piso.get("bloque_id"):
                                        bloque_records = await self.api.get_records(
                                            "bloques",
                                            {"id": f"eq.{piso['bloque_id']}"}
                                        )
                                        if bloque_records:
                                            location_items.append(
                                                ("Bloque", bloque_records[0].get("direccion", "N/A"))
                                            )
                    except Exception as e:
                        print(f"Error fetching location details: {e}")

                for label, value in location_items:
                    with ui.row().classes("mb-1"):
                        ui.label(f"{label}:").classes("font-bold w-32")
                        ui.label(str(value) if value else "N/A").classes("flex-grow")

    async def _load_conflict_history(self):
        """Load history for selected conflict with user and note details"""
        if not self.history_container or not self.state.selected_conflict:
            return

        self.history_container.clear()

        try:
            # Fetch from the view that includes user and action information
            history = await self.api.get_records(
                "v_diario_conflictos_con_afiliada",
                {"conflicto_id": f'eq.{self.state.selected_conflict["id"]}'},
                order="created_at.desc"
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
        """Create an enhanced history entry card with notes and user info"""
        with ui.card().classes("w-full mb-2"):
            # Header with timestamp and actions
            with ui.row().classes("w-full justify-between items-center mb-2"):
                with ui.column():
                    # Timestamp and author
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("schedule", size="sm").classes("text-gray-500")
                        ui.label(entry.get("created_at", "Sin fecha")).classes(
                            "text-caption text-gray-600"
                        )

                    # Author of the note
                    if entry.get("autor_nota_alias"):
                        with ui.row().classes("items-center gap-2 mt-1"):
                            ui.icon("person", size="sm").classes("text-gray-500")
                            ui.label(f"Por: {entry['autor_nota_alias']}").classes(
                                "text-caption text-blue-600"
                            )

                # Edit and delete buttons
                with ui.row().classes("gap-2"):
                    ui.button(
                        icon="edit",
                        on_click=lambda e=entry: self._edit_note(e)
                    ).props("size=sm flat dense").tooltip("Editar nota")

                    ui.button(
                        icon="delete",
                        on_click=lambda e=entry: self._delete_note(e)
                    ).props("size=sm flat dense color=negative").tooltip("Eliminar nota")

            # Status badges
            with ui.row().classes("gap-2 mb-2"):
                if entry.get("estado"):
                    color_map = {
                        "Abierto": "red",
                        "En proceso": "orange",
                        "Resuelto": "green",
                        "Cerrado": "gray"
                    }
                    color = color_map.get(entry["estado"], "blue")
                    ui.badge(f"Estado: {entry['estado']}", color=color).props("outline")

                if entry.get("accion_nombre"):
                    ui.badge(f"Acción: {entry['accion_nombre']}", color="purple").props("outline")

                if entry.get("ambito"):
                    ui.badge(f"Ámbito: {entry['ambito']}", color="indigo").props("outline")

            # Main note content
            if entry.get("notas"):
                ui.separator().classes("my-2")
                with ui.row().classes("w-full"):
                    ui.icon("notes", size="sm").classes("text-gray-500 mt-1")
                    with ui.column().classes("flex-grow ml-2"):
                        ui.label("Nota:").classes("font-semibold text-sm")
                        ui.label(entry["notas"]).classes("text-gray-700 whitespace-pre-wrap")

            # Show affiliate name if different from main conflict
            if entry.get("afiliada_nombre_completo") and entry.get("afiliada_nombre_completo") != self.state.selected_conflict.get("afiliada_nombre_completo"):
                ui.separator().classes("my-2")
                with ui.row().classes("items-center gap-2"):
                    ui.icon("person_outline", size="sm").classes("text-gray-500")
                    ui.label(f"Afiliada: {entry['afiliada_nombre_completo']}").classes("text-caption")

    async def _add_note(self):
        """Add a new note to the selected conflict"""
        if not self.state.selected_conflict:
            ui.notify("Por favor, seleccione un conflicto primero", type="warning")
            return

        async def on_note_added():
            """Callback after note is added"""
            await self._load_conflicts()
            await self._on_conflict_change(self.state.selected_conflict["id"])

        dialog = ConflictNoteDialog(
            api=self.api,
            conflict=self.state.selected_conflict,
            on_success=on_note_added,
            mode="create",
        )
        await dialog.open()

    async def _edit_note(self, note: dict):
        """Edit an existing note"""

        async def on_note_updated():
            """Callback after note is updated"""
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

            # Show a preview of the note
            if note.get("notas"):
                ui.separator().classes("my-2")
                note_preview = note["notas"][:100] + "..." if len(note["notas"]) > 100 else note["notas"]
                ui.label(f'Nota: "{note_preview}"').classes("text-caption text-gray-500")

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