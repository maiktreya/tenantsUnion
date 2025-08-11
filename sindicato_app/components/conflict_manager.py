from typing import Optional, List, Dict
from nicegui import ui
from api.client import APIClient

class ConflictManager:
    """Self-contained conflict management component"""

    def __init__(self, api_client: APIClient):
        # Dependencies
        self.api_client = api_client

        # Internal state
        self.conflicts: List[Dict] = []
        self.selected_conflict: Optional[Dict] = None
        self.history: List[Dict] = []

        # UI references
        self.container = None
        self.conflict_select = None
        self.info_container = None
        self.history_container = None

    def mount(self) -> ui.column:
        """Mount the component"""
        self.container = ui.column().classes('w-full p-4 gap-4')
        self._render()
        ui.timer(0.5, self._load_conflicts, once=True)
        return self.container

    def _render(self):
        """Render the component"""
        if not self.container:
            return

        self.container.clear()

        with self.container:
            ui.label('Conflict Manager').classes('text-h5')

            with ui.row().classes('w-full gap-4'):
                # Left panel
                with ui.column().classes('w-96 gap-4'):
                    # Conflict selector
                    self.conflict_select = ui.select(
                        options={},
                        label='Select Conflict',
                        on_change=lambda e: self._on_conflict_change(e.value) if e.value else None
                    ).classes('w-full')

                    # Action buttons
                    with ui.row().classes('gap-2'):
                        ui.button(
                            'Add Note',
                            icon='add_comment',
                            on_click=self._show_add_note_dialog
                        ).props('color=primary')

                        ui.button(
                            'Refresh',
                            icon='refresh',
                            on_click=self._load_conflicts
                        ).props('flat')

                    # Info container
                    self.info_container = ui.column().classes('w-full')

                # Right panel - History
                self.history_container = ui.column().classes('flex-grow')

    async def _load_conflicts(self):
        """Load conflicts using API client"""
        try:
            # Load data
            data = await self.api_client.get('/conflictos')

            # Validate response
            if data is None:
                ui.notify('No data received from API', type='warning')
                self.conflicts = []
                return

            if not isinstance(data, list):
                ui.notify(f'Unexpected data type: {type(data)}', type='warning')
                self.conflicts = []
                return

            self.conflicts = data
            ui.notify(f'Loaded {len(self.conflicts)} conflicts', type='positive')

            # Debug: Print first conflict structure
            if self.conflicts:
                print(f"First conflict structure: {self.conflicts[0].keys() if self.conflicts[0] else 'Empty'}")

            # Update select options
            if self.conflicts:
                options = {}
                for i, conflict in enumerate(self.conflicts):
                    try:
                        # Handle different possible structures
                        if conflict is None:
                            print(f"Warning: Conflict at index {i} is None")
                            continue

                        if not isinstance(conflict, dict):
                            print(f"Warning: Conflict at index {i} is not a dict: {type(conflict)}")
                            continue

                        # Try to get ID with fallbacks
                        conflict_id = conflict.get('id') or conflict.get('ID') or conflict.get('conflicto_id')

                        if conflict_id is None:
                            print(f"Warning: No ID found for conflict at index {i}: {list(conflict.keys())[:5]}")
                            continue

                        # Try to get description with fallbacks
                        description = (
                            conflict.get('descripcion') or
                            conflict.get('description') or
                            conflict.get('desc') or
                            conflict.get('nombre') or
                            conflict.get('name') or
                            f"Conflict {conflict_id}"
                        )

                        # Create option
                        options[conflict_id] = f"ID {conflict_id}: {str(description)[:50]}"

                    except Exception as e:
                        print(f"Error processing conflict at index {i}: {e}")
                        continue

                if options:
                    self.conflict_select.set_options(options)
                    print(f"Successfully set {len(options)} options")
                else:
                    self.conflict_select.set_options({})
                    ui.notify('No valid conflicts found to display', type='warning')
            else:
                self.conflict_select.set_options({})
                ui.notify('No conflicts found', type='info')

        except Exception as e:
            ui.notify(f'Error loading conflicts: {str(e)}', type='negative')
            print(f"Full error loading conflicts: {e}")
            import traceback
            traceback.print_exc()
            self.conflicts = []
            self.conflict_select.set_options({})

    async def _on_conflict_change(self, conflict_id: Optional[int]):
        """Handle conflict selection"""
        if conflict_id is None:
            self.selected_conflict = None
            self._clear_displays()
            return

        print(f"Selected conflict ID: {conflict_id}")

        # Find selected conflict
        self.selected_conflict = None
        for c in self.conflicts:
            if c and isinstance(c, dict):
                c_id = c.get('id') or c.get('ID') or c.get('conflicto_id')
                if c_id == conflict_id:
                    self.selected_conflict = c
                    break

        if self.selected_conflict:
            self._display_conflict_info()
            await self._load_history()
        else:
            ui.notify(f'Conflict with ID {conflict_id} not found', type='warning')

    def _display_conflict_info(self):
        """Display conflict information"""
        if not self.info_container or not self.selected_conflict:
            return

        self.info_container.clear()

        with self.info_container:
            ui.label('Conflict Information').classes('text-h6 mb-2')

            with ui.card().classes('w-full'):
                # Display each field
                for key, value in self.selected_conflict.items():
                    if value is not None:  # Only show non-null values
                        with ui.row().classes('gap-2 mb-1'):
                            ui.label(f'{key.replace("_", " ").title()}:').classes('font-bold w-32 text-sm')
                            # Handle long text
                            value_str = str(value)
                            if len(value_str) > 100:
                                value_str = value_str[:100] + '...'
                            ui.label(value_str).classes('text-gray-700 text-sm')

    async def _load_history(self):
        """Load conflict history using API client"""
        if not self.selected_conflict:
            return

        try:
            conflict_id = (
                self.selected_conflict.get('id') or
                self.selected_conflict.get('ID') or
                self.selected_conflict.get('conflicto_id')
            )

            print(f"Loading history for conflict ID: {conflict_id}")

            # Load history
            data = await self.api_client.get(
                '/diario_conflictos',
                params={'conflicto_id': f'eq.{conflict_id}'}
            )

            # Validate response
            if isinstance(data, list):
                self.history = data
            else:
                self.history = []

            print(f"Loaded {len(self.history)} history entries")
            self._display_history()

        except Exception as e:
            ui.notify(f'Error loading history: {str(e)}', type='negative')
            print(f"Full error loading history: {e}")
            self.history = []
            self._display_history()

    def _display_history(self):
        """Display conflict history"""
        if not self.history_container:
            return

        self.history_container.clear()

        with self.history_container:
            ui.label('History').classes('text-h6 mb-2')

            if not self.history:
                ui.label('No history available').classes('text-gray-500')
                return

            # Create scrollable area for history
            with ui.scroll_area().classes('w-full h-96'):
                for entry in self.history:
                    if not isinstance(entry, dict):
                        continue

                    with ui.card().classes('w-full mb-2'):
                        # Date and user info
                        with ui.row().classes('justify-between items-center'):
                            date_str = entry.get('created_at') or entry.get('fecha') or 'No date'
                            ui.label(str(date_str)).classes('text-sm text-gray-600')

                            if entry.get('usuario'):
                                ui.label(f"By: {entry['usuario']}").classes('text-sm text-gray-600')

                        # Note content
                        note_text = (
                            entry.get('causa') or
                            entry.get('nota') or
                            entry.get('descripcion') or
                            entry.get('comentario') or
                            'No content'
                        )
                        ui.label(str(note_text)).classes('mt-2')

    def _show_add_note_dialog(self):
        """Show dialog to add note"""
        if not self.selected_conflict:
            ui.notify('Please select a conflict first', type='warning')
            return

        conflict_id = (
            self.selected_conflict.get('id') or
            self.selected_conflict.get('ID') or
            self.selected_conflict.get('conflicto_id')
        )

        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('Add Note').classes('text-h6')

            ui.label(f"For Conflict ID: {conflict_id}").classes('text-sm text-gray-600 mb-2')

            note_input = ui.textarea('Note', placeholder='Enter your note here...').classes('w-full')

            with ui.row().classes('gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button(
                    'Save',
                    on_click=lambda: self._save_note(note_input.value, dialog)
                ).props('color=primary')

        dialog.open()

    async def _save_note(self, note: str, dialog):
        """Save note using API client"""
        if not note or not note.strip():
            ui.notify('Note cannot be empty', type='warning')
            return

        try:
            conflict_id = (
                self.selected_conflict.get('id') or
                self.selected_conflict.get('ID') or
                self.selected_conflict.get('conflicto_id')
            )

            # Save note
            await self.api_client.post(
                '/diario_conflictos',
                {
                    'conflicto_id': conflict_id,
                    'causa': note.strip()
                }
            )

            ui.notify('Note added successfully', type='positive')
            dialog.close()

            # Reload history
            await self._load_history()

        except Exception as e:
            ui.notify(f'Error saving note: {str(e)}', type='negative')
            print(f"Full error saving note: {e}")

    def _clear_displays(self):
        """Clear display containers"""
        if self.info_container:
            self.info_container.clear()
        if self.history_container:
            self.history_container.clear()