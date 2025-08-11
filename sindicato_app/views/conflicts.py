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
        container = ui.column().classes('w-full p-4 gap-4')

        with container:
            ui.label('Gestor de Conflictos').classes('text-h4')

            with ui.row().classes('w-full gap-4'):
                # Left panel - Selection and info
                with ui.column().classes('w-96 gap-4'):
                    # Conflict selector
                    with ui.row().classes('w-full gap-2'):
                        self.conflict_select = ui.select(
                            options={},
                            label='Seleccionar Conflicto',
                            on_change=lambda e: ui.timer(
                                0.1,
                                lambda: self._on_conflict_change(e.value),
                                once=True
                            )
                        ).classes('flex-grow')

                        ui.button(
                            icon='refresh',
                            on_click=lambda: ui.timer(0.1, self._load_conflicts, once=True)
                        ).props('flat')

                    # Add note button
                    ui.button(
                        'Añadir Nota',
                        icon='add_comment',
                        on_click=self._add_note
                    ).props('color=orange-600').classes('w-full')

                    # Conflict info container
                    self.info_container = ui.column().classes('w-full')

                # Right panel - History
                with ui.column().classes('flex-grow'):
                    self.history_container = ui.column().classes('w-full gap-4')

        # Load conflicts on startup
        ui.timer(0.5, self._load_conflicts, once=True)

        return container

    async def _load_conflicts(self):
        """Load all conflicts"""
        try:
            conflicts = await self.api.get_records('conflictos', order='id.asc')
            self.state.set_conflicts(conflicts)

            # Update select options
            options = self.state.get_conflict_options()
            if self.conflict_select:
                self.conflict_select.set_options(options)

            ui.notify(f'Se cargaron {len(conflicts)} conflictos', type='positive')
        except Exception as e:
            ui.notify(f'Error al cargar conflictos: {str(e)}', type='negative')

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
        """Display information about the selected conflict"""
        if not self.info_container or not self.state.selected_conflict:
            return

        self.info_container.clear()
        conflict = self.state.selected_conflict

        with self.info_container:
            ui.label('Información del Conflicto').classes('text-h6 mb-2')

            with ui.card().classes('w-full'):
                info_items = [
                    ('ID', conflict.get('id', 'N/A')),
                    ('Estado', conflict.get('estado', 'N/A')),
                    ('Ámbito', conflict.get('ambito', 'N/A')),
                    ('Causa', conflict.get('causa', 'N/A')),
                    ('Fecha de Apertura', conflict.get('fecha_apertura', 'N/A')),
                    ('Fecha de Cierre', conflict.get('fecha_cierre', 'N/A')),
                    ('Descripción', conflict.get('descripcion', 'N/A'))
                ]

                for label, value in info_items:
                    with ui.row().classes('mb-1'):
                        ui.label(f"{label}:").classes('font-bold w-32')
                        ui.label(str(value) if value else 'N/A').classes('flex-grow')

    async def _load_conflict_history(self):
        """Load history for selected conflict"""
        if not self.history_container or not self.state.selected_conflict:
            return

        self.history_container.clear()

        try:
            history = await self.api.get_records(
                'diario_conflictos',
                {'conflicto_id': f'eq.{self.state.selected_conflict["id"]}'}
            )
            self.state.set_history(history)

            with self.history_container:
                ui.label('Historial').classes('text-h6 mb-2')

                if self.state.history:
                    for entry in self.state.history:
                        self._create_history_entry(entry)
                else:
                    ui.label('No se encontraron entradas en el historial').classes('text-gray-500')

        except Exception as e:
            ui.notify(f'Error al cargar el historial: {str(e)}', type='negative')

    def _create_history_entry(self, entry: dict):
        """Create a history entry card"""
        with ui.card().classes('w-full mb-2'):
            with ui.row().classes('w-full justify-between mb-2'):
                ui.label(
                    entry.get('created_at', 'Sin fecha')
                ).classes('text-caption text-gray-600')

                if entry.get('estado'):
                    ui.label(f"Estado: {entry['estado']}").classes('text-caption')

            if entry.get('causa'):
                with ui.row().classes('mb-1'):
                    ui.label('Causa:').classes('font-semibold mr-2')
                    ui.label(entry['causa'])

            if entry.get('afectada'):
                with ui.row().classes('mb-1'):
                    ui.label('Afectada:').classes('font-semibold mr-2')
                    ui.label(entry['afectada'])

            if entry.get('ambito'):
                with ui.row().classes('mb-1'):
                    ui.label('Ámbito:').classes('font-semibold mr-2')
                    ui.label(entry['ambito'])

    async def _add_note(self):
        """Add a new note to the selected conflict"""
        if not self.state.selected_conflict:
            ui.notify('Por favor, seleccione un conflicto primero', type='warning')
            return

        async def on_note_added():
            """Callback after note is added"""
            await self._load_conflicts()
            await self._on_conflict_change(self.state.selected_conflict['id'])

        dialog = ConflictNoteDialog(
            api=self.api,
            conflict=self.state.selected_conflict,
            on_success=on_note_added
        )
        dialog.open()

    def _clear_displays(self):
        """Clear info and history displays"""
        if self.info_container:
            self.info_container.clear()
        if self.history_container:
            self.history_container.clear()