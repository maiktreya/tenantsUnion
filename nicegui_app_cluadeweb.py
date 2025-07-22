#!/usr/bin/env python3
"""
NiceGUI Frontend for PostgREST API
Provides admin CRUD operations and conflict note-taking interface
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional

import httpx
from nicegui import ui, app
from nicegui.events import ValueChangeEventArguments


# Configuration
API_BASE_URL = "http://localhost:3001"
APP_PORT = 8081


class APIClient:
    """Client for PostgREST API operations"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get_tables(self) -> List[str]:
        """Get list of available tables"""
        # Define tables based on the schema provided
        tables = [
            'entramado_empresas',
            'empresas',
            'bloques',
            'pisos',
            'usuarios',
            'afiliadas',
            'facturacion',
            'asesorias',
            'conflictos',
            'diario_conflictos'
        ]
        return tables

    async def get_records(self, table: str, limit: int = 100) -> List[Dict]:
        """Get records from a table"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{table}",
                    params={"limit": limit}
                )
                return response.json() if response.status_code == 200 else []
            except Exception:
                return []

    async def create_record(self, table: str, data: Dict) -> bool:
        """Create a new record"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{table}",
                    json=data,
                    headers={"Content-Type": "application/json", "Prefer": "return=minimal"}
                )
                return response.status_code == 201
            except Exception:
                return False

    async def update_record(self, table: str, record_id: int, data: Dict) -> bool:
        """Update a record"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"{self.base_url}/{table}",
                    json=data,
                    headers={"Content-Type": "application/json", "Prefer": "return=minimal"},
                    params={"id": f"eq.{record_id}"}
                )
                return response.status_code == 204
            except Exception:
                return False

    async def delete_record(self, table: str, record_id: int) -> bool:
        """Delete a record"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    f"{self.base_url}/{table}",
                    params={"id": f"eq.{record_id}"}
                )
                return response.status_code == 204
            except Exception:
                return False

    async def get_conflicts(self) -> List[Dict]:
        """Get all conflicts for the notes interface"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/conflictos")
                return response.json() if response.status_code == 200 else []
            except Exception:
                return []

    async def create_conflict_note(self, conflict_id: int, note_data: Dict) -> bool:
        """Create a new conflict diary entry"""
        note_data['conflicto_id'] = conflict_id
        return await self.create_record('diario_conflictos', note_data)


# Global API client
api_client = APIClient(API_BASE_URL)


class AdminPage:
    """Admin page for CRUD operations"""

    def __init__(self):
        self.current_table = None
        self.records = []
        self.selected_record = None
        self.edit_dialog = None

    def create_page(self):
        """Create the admin page UI"""
        with ui.card().classes('w-full max-w-6xl mx-auto'):
            ui.label('Admin Panel - Database Management').classes('text-2xl font-bold mb-4')

            # Table selection
            with ui.row().classes('w-full gap-4 mb-4'):
                self.table_select = ui.select(
                    options=[],
                    label='Select Table',
                    on_change=self.on_table_change
                ).classes('flex-grow')

                ui.button('Refresh Tables', on_click=self.refresh_tables).classes('bg-blue-500')

            # Records display
            self.records_container = ui.column().classes('w-full')

            # Load tables on startup
            ui.timer(0.1, self.refresh_tables, once=True)

    async def refresh_tables(self):
        """Refresh the list of available tables"""
        tables = await api_client.get_tables()
        self.table_select.options = tables
        self.table_select.update()

    async def on_table_change(self, e: ValueChangeEventArguments):
        """Handle table selection change"""
        self.current_table = e.value
        if self.current_table:
            await self.load_records()

    async def load_records(self):
        """Load records for the selected table"""
        if not self.current_table:
            return

        self.records = await api_client.get_records(self.current_table)
        self.display_records()

    def display_records(self):
        """Display records in a table"""
        self.records_container.clear()

        with self.records_container:
            ui.button('Add New Record', on_click=self.show_add_dialog).classes('bg-green-500 mb-4')

            if not self.records:
                ui.label('No records found').classes('text-gray-500')
                return

            # Get column names
            columns = list(self.records[0].keys()) if self.records else []

            # Add actions column
            display_columns = columns + ['actions']

            # Prepare rows with actions
            display_rows = []
            for record in self.records:
                row = dict(record)
                row['actions'] = ''  # Placeholder for actions
                display_rows.append(row)

            # Create table
            with ui.table(
                columns=[{'name': col, 'label': col.replace('_', ' ').title(), 'field': col} for col in display_columns],
                rows=display_rows,
                row_key='id'
            ).classes('w-full') as table:

                # Add action buttons
                def create_action_slot(record_data):
                    with ui.row():
                        ui.button('Edit', on_click=lambda r=record_data: self.show_edit_dialog_direct(r)).props('size=sm color=primary')
                        ui.button('Delete', on_click=lambda r=record_data: self.delete_record_direct(r)).props('size=sm color=negative').classes('ml-1')

                table.add_slot('body-cell-actions', '''
                    <q-td key="actions" :props="props">
                        <q-btn size="sm" color="primary" label="Edit" @click="$parent.$emit('edit-record', props.row)" />
                        <q-btn size="sm" color="negative" label="Delete" @click="$parent.$emit('delete-record', props.row)" class="ml-2" />
                    </q-td>
                ''')

                table.on('edit-record', lambda e: self.show_edit_dialog_direct(e.args))
                table.on('delete-record', lambda e: self.delete_record_direct(e.args))

    def show_edit_dialog_direct(self, record):
        """Show dialog for editing a record - direct call"""
        self.show_record_dialog(record, is_edit=True)

    async def delete_record_direct(self, record):
        """Delete a record - direct call"""
        record_id = record['id']

        success = await api_client.delete_record(self.current_table, record_id)

        if success:
            ui.notify("Record deleted successfully", color='positive')
            await self.load_records()
        else:
            ui.notify("Failed to delete record", color='negative')

    def show_add_dialog(self):
        """Show dialog for adding a new record"""
        if not self.current_table:
            ui.notify("Please select a table first", color='warning')
            return

        # Create a sample record structure based on current table
        sample_record = {}
        if self.records:
            sample_record = {k: '' for k in self.records[0].keys()}
        else:
            # Basic structure for empty tables
            sample_record = {'id': '', 'name': ''}

        self.show_record_dialog(sample_record, is_edit=False)

    def show_edit_dialog(self, event):
        """Show dialog for editing a record"""
        record = event.args
        self.show_record_dialog(record, is_edit=True)

    def show_record_dialog(self, record: Dict, is_edit: bool):
        """Show dialog for adding/editing a record"""
        title = f"{'Edit' if is_edit else 'Add'} {self.current_table.title()} Record"

        with ui.dialog().classes('w-96') as dialog:
            with ui.card():
                ui.label(title).classes('text-lg font-bold mb-4')

                inputs = {}

                # Use existing record structure or sample from loaded records
                fields_to_show = list(record.keys()) if record else []
                if not fields_to_show and self.records:
                    fields_to_show = list(self.records[0].keys())

                for field in fields_to_show:
                    if field == 'id' and not is_edit:
                        continue  # Skip ID for new records

                    value = str(record.get(field, '')) if record.get(field) is not None else ''
                    inputs[field] = ui.input(
                        label=field.replace('_', ' ').title(),
                        value=value
                    ).classes('w-full mb-2')

                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500')
                    ui.button(
                        'Save',
                        on_click=lambda: self.save_record(dialog, inputs, record if is_edit else None)
                    ).classes('bg-green-500')

        dialog.open()

    async def save_record(self, dialog, inputs: Dict, existing_record: Optional[Dict]):
        """Save a record (create or update)"""
        data = {}
        for field, input_widget in inputs.items():
            value = input_widget.value.strip() if input_widget.value else None
            if value:  # Only include non-empty values
                # Try to convert to appropriate type
                try:
                    if value.isdigit():
                        data[field] = int(value)
                    elif value.replace('.', '').isdigit():
                        data[field] = float(value)
                    else:
                        data[field] = value
                except ValueError:
                    data[field] = value

        success = False
        if existing_record:  # Update
            record_id = existing_record['id']
            success = await api_client.update_record(self.current_table, record_id, data)
        else:  # Create
            success = await api_client.create_record(self.current_table, data)

        if success:
            ui.notify(f"Record {'updated' if existing_record else 'created'} successfully", color='positive')
            await self.load_records()
            dialog.close()
        else:
            ui.notify(f"Failed to {'update' if existing_record else 'create'} record", color='negative')

    async def delete_record(self, event):
        """Delete a record"""
        record = event.args
        await self.delete_record_direct(record)


class NotesPage:
    """Notes page for conflict logging"""

    def __init__(self):
        self.conflicts = []
        self.selected_conflict = None

    def create_page(self):
        """Create the notes page UI"""
        with ui.card().classes('w-full max-w-4xl mx-auto'):
            ui.label('Conflict Notes - Diario de Conflictos').classes('text-2xl font-bold mb-4')

            # Conflict selection
            with ui.row().classes('w-full gap-4 mb-4'):
                self.conflict_select = ui.select(
                    options=[],
                    label='Select Conflict',
                    on_change=self.on_conflict_change
                ).classes('flex-grow')

                ui.button('Refresh Conflicts', on_click=self.refresh_conflicts).classes('bg-blue-500')

            # Selected conflict info
            self.conflict_info = ui.column().classes('w-full mb-4')

            # Note form
            self.note_form = ui.column().classes('w-full')

            # Load conflicts on startup
            ui.timer(0.1, self.refresh_conflicts, once=True)

    async def refresh_conflicts(self):
        """Refresh the list of conflicts"""
        self.conflicts = await api_client.get_conflicts()

        # Create options with conflict info
        options = {}
        for conflict in self.conflicts:
            descripcion = conflict.get('descripcion') or 'Sin descripción'
            # Safely truncate description
            desc_preview = descripcion[:50] + "..." if len(descripcion) > 50 else descripcion

            label = f"ID {conflict['id']}: {desc_preview}"
            if conflict.get('fecha_apertura'):
                label += f" ({conflict['fecha_apertura']})"
            options[conflict['id']] = label

        self.conflict_select.options = options
        self.conflict_select.update()

    def on_conflict_change(self, e: ValueChangeEventArguments):
        """Handle conflict selection change"""
        conflict_id = e.value
        self.selected_conflict = next((c for c in self.conflicts if c['id'] == conflict_id), None)
        self.display_conflict_info()
        self.display_note_form()

    def display_conflict_info(self):
        """Display information about the selected conflict"""
        self.conflict_info.clear()

        if not self.selected_conflict:
            return

        with self.conflict_info:
            ui.label('Conflict Information').classes('text-lg font-semibold mb-2')

            with ui.card().classes('w-full bg-gray-50'):
                info_items = [
                    ('ID', self.selected_conflict['id']),
                    ('Estado', self.selected_conflict.get('estado', 'N/A')),
                    ('Ámbito', self.selected_conflict.get('ambito', 'N/A')),
                    ('Causa', self.selected_conflict.get('causa', 'N/A')),
                    ('Fecha Apertura', self.selected_conflict.get('fecha_apertura', 'N/A')),
                    ('Fecha Cierre', self.selected_conflict.get('fecha_cierre', 'N/A')),
                    ('Descripción', self.selected_conflict.get('descripcion', 'N/A'))
                ]

                for label, value in info_items:
                    with ui.row().classes('mb-1'):
                        ui.label(f"{label}:").classes('font-medium w-32')
                        ui.label(str(value)).classes('flex-grow')

    def display_note_form(self):
        """Display the form for adding notes"""
        self.note_form.clear()

        if not self.selected_conflict:
            with self.note_form:
                ui.label('Please select a conflict to add notes').classes('text-gray-500')
            return

        with self.note_form:
            ui.label('Add New Note').classes('text-lg font-semibold mb-4')

            with ui.card().classes('w-full'):
                self.estado_input = ui.input(label='Estado').classes('w-full mb-2')
                self.ambito_input = ui.input(label='Ámbito').classes('w-full mb-2')
                self.afectada_input = ui.input(label='Afectada').classes('w-full mb-2')
                self.causa_input = ui.textarea(label='Causa').classes('w-full mb-2')

                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Clear Form', on_click=self.clear_form).classes('bg-gray-500')
                    ui.button('Save Note', on_click=self.save_note).classes('bg-green-500')

    def clear_form(self):
        """Clear the note form"""
        self.estado_input.value = ''
        self.ambito_input.value = ''
        self.afectada_input.value = ''
        self.causa_input.value = ''

    async def save_note(self):
        """Save a new note to diario_conflictos"""
        if not self.selected_conflict:
            ui.notify("Please select a conflict first", color='negative')
            return

        note_data = {
            'estado': self.estado_input.value.strip() if self.estado_input.value else None,
            'ambito': self.ambito_input.value.strip() if self.ambito_input.value else None,
            'afectada': self.afectada_input.value.strip() if self.afectada_input.value else None,
            'causa': self.causa_input.value.strip() if self.causa_input.value else None,
        }

        # Remove empty values
        note_data = {k: v for k, v in note_data.items() if v}

        if not note_data:
            ui.notify("Please fill in at least one field", color='warning')
            return

        success = await api_client.create_conflict_note(self.selected_conflict['id'], note_data)

        if success:
            ui.notify("Note saved successfully", color='positive')
            self.clear_form()
        else:
            ui.notify("Failed to save note", color='negative')


# Main application
@ui.page('/')
def main_page():
    """Main page with navigation"""
    with ui.header():
        ui.label('Sindicato Database Manager').classes('text-h5')

    with ui.tabs() as tabs:
        admin_tab = ui.tab('Admin')
        notes_tab = ui.tab('Notes')

    with ui.tab_panels(tabs, value=admin_tab):
        with ui.tab_panel(admin_tab):
            admin_page = AdminPage()
            admin_page.create_page()

        with ui.tab_panel(notes_tab):
            notes_page = NotesPage()
            notes_page.create_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host='0.0.0.0',
        port=APP_PORT,
        title='Sindicato Database Manager',
        favicon='🏢'
    )