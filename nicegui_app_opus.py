#!/usr/bin/env python3
from datetime import datetime
from typing import Dict, List, Optional, Any
import csv
import io
import httpx
from nicegui import ui, app

# PostgREST API configuration
API_BASE_URL = "http://localhost:3001"

# Table metadata for better UI
TABLE_INFO = {
    'entramado_empresas': {'display_name': 'Entramado Empresas', 'id_field': 'id'},
    'empresas': {'display_name': 'Empresas', 'id_field': 'id'},
    'bloques': {'display_name': 'Bloques', 'id_field': 'id'},
    'pisos': {'display_name': 'Pisos', 'id_field': 'id'},
    'usuarios': {'display_name': 'Usuarios', 'id_field': 'id'},
    'afiliadas': {'display_name': 'Afiliadas', 'id_field': 'id'},
    'facturacion': {'display_name': 'Facturación', 'id_field': 'id'},
    'asesorias': {'display_name': 'Asesorías', 'id_field': 'id'},
    'conflictos': {'display_name': 'Conflictos', 'id_field': 'id'},
    'diario_conflictos': {'display_name': 'Diario Conflictos', 'id_field': 'id'}
}

class APIClient:
    """PostgREST API client"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = None

    def _ensure_client(self):
        if self.client is None:
            self.client = httpx.AsyncClient()
        return self.client

    async def get_records(self, table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Get all records from a table with optional filters"""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}"
        params = filters or {}
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            ui.notify(f'Error fetching records: {str(e)}', type='negative')
            return []

    async def get_record(self, table: str, record_id: int) -> Optional[Dict]:
        """Get a single record by ID"""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}"
        params = {f'id': f'eq.{record_id}'}
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data[0] if data else None
        except Exception:
            return None

    async def create_record(self, table: str, data: Dict) -> Dict:
        """Create a new record"""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}"
        headers = {"Prefer": "return=representation"}
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result[0] if isinstance(result, list) else result

    async def update_record(self, table: str, record_id: int, data: Dict) -> Dict:
        """Update an existing record"""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}?id=eq.{record_id}"
        headers = {"Prefer": "return=representation"}
        response = await client.patch(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result[0] if isinstance(result, list) else result

    async def delete_record(self, table: str, record_id: int) -> None:
        """Delete a record"""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}?id=eq.{record_id}"
        response = await client.delete(url)
        response.raise_for_status()

# Initialize API client
api_client = APIClient(API_BASE_URL)

# Main page
@ui.page('/')
async def index():
    with ui.header().classes('bg-blue-600 text-white'):
        with ui.row().classes('w-full items-center'):
            ui.label('Sindicato INQ Management').classes('text-h6')
            ui.space()
            with ui.row().classes('gap-2'):
                ui.button('Admin', on_click=lambda: ui.navigate.to('/admin')).props('flat color=white')
                ui.button('Conflict Notes', on_click=lambda: ui.navigate.to('/conflicts')).props('flat color=white')

    with ui.column().classes('w-full p-8 items-center gap-8'):
        ui.label('Welcome to Sindicato INQ Management System').classes('text-h4')

        with ui.row().classes('gap-8'):
            with ui.card().classes('w-80 cursor-pointer').on('click', lambda: ui.navigate.to('/admin')):
                with ui.column().classes('items-center gap-4 p-4'):
                    ui.icon('admin_panel_settings', size='4rem')
                    ui.label('Database Admin').classes('text-h6')
                    ui.label('Manage all database tables with full CRUD operations').classes('text-center')

            with ui.card().classes('w-80 cursor-pointer').on('click', lambda: ui.navigate.to('/conflicts')):
                with ui.column().classes('items-center gap-4 p-4'):
                    ui.icon('note_add', size='4rem')
                    ui.label('Conflict Notes').classes('text-h6')
                    ui.label('Add notes and track conflict history').classes('text-center')

# Admin page with sorting and filtering
@ui.page('/admin')
async def admin():
    with ui.header().classes('bg-blue-600 text-white'):
        with ui.row().classes('w-full items-center'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat color=white')
            ui.label('Database Admin').classes('text-h6')

    selected_table = {'value': None}
    table_data = {'records': [], 'filtered_records': []}
    sort_config = {'column': None, 'ascending': True}
    filter_config = {}

    async def load_table_data():
        """Load data for the selected table"""
        if not selected_table['value']:
            return

        try:
            records = await api_client.get_records(selected_table['value'])
            table_data['records'] = records
            table_data['filtered_records'] = records.copy()
            filter_config.clear()
            sort_config['column'] = None
            sort_config['ascending'] = True
            refresh_table()
            setup_filters()
            ui.notify(f'Loaded {len(records)} records', type='positive')
        except Exception as e:
            ui.notify(f'Error loading data: {str(e)}', type='negative')

    def apply_filters():
        """Apply all active filters to the data"""
        filtered = table_data['records'].copy()

        for column, filter_value in filter_config.items():
            if filter_value:
                filtered = [
                    record for record in filtered
                    if str(filter_value).lower() in str(record.get(column, '')).lower()
                ]

        table_data['filtered_records'] = filtered
        apply_sort()

    def apply_sort():
        """Apply sorting to the filtered data"""
        if sort_config['column']:
            table_data['filtered_records'].sort(
                key=lambda x: x.get(sort_config['column'], ''),
                reverse=not sort_config['ascending']
            )
        refresh_table()

    def sort_by_column(column: str):
        """Sort by a specific column"""
        if sort_config['column'] == column:
            sort_config['ascending'] = not sort_config['ascending']
        else:
            sort_config['column'] = column
            sort_config['ascending'] = True
        apply_sort()

    def setup_filters():
        """Setup filter inputs for each column"""
        filter_container.clear()

        if not table_data['records']:
            return

        # Get columns from first record
        columns = list(table_data['records'][0].keys())

        with filter_container:
            ui.label('Filters').classes('text-h6 mb-2')
            with ui.row().classes('w-full gap-2 flex-wrap'):
                for column in columns:
                    filter_input = ui.input(
                        label=f'Filter {column}',
                        on_change=lambda e, col=column: update_filter(col, e.value)
                    ).classes('w-48').props('dense clearable')

    def update_filter(column: str, value: str):
        """Update filter for a specific column"""
        filter_config[column] = value
        apply_filters()

    def clear_filters():
        """Clear all filters"""
        filter_config.clear()
        table_data['filtered_records'] = table_data['records'].copy()
        setup_filters()
        refresh_table()

    def refresh_table():
        """Refresh the table display"""
        table_container.clear()

        records_to_show = table_data['filtered_records']

        if not records_to_show:
            with table_container:
                ui.label('No records found').classes('text-gray-500')
            return

        with table_container:
            # Show record count
            ui.label(f'Showing {len(records_to_show)} of {len(table_data["records"])} records').classes('text-caption text-gray-600 mb-2')

            # Get columns from first record
            if records_to_show:
                columns = list(records_to_show[0].keys())

                # Create custom table with sortable headers
                with ui.card().classes('w-full'):
                    # Table header
                    with ui.row().classes('w-full bg-gray-100 p-2'):
                        for column in columns:
                            with ui.row().classes('flex-1 items-center cursor-pointer').on('click', lambda c=column: sort_by_column(c)):
                                ui.label(column).classes('font-bold')
                                if sort_config['column'] == column:
                                    ui.icon('arrow_upward' if sort_config['ascending'] else 'arrow_downward', size='sm')
                        ui.label('Actions').classes('font-bold w-32')

                    # Table body with pagination
                    page_size = 10
                    total_pages = (len(records_to_show) - 1) // page_size + 1
                    current_page = {'value': 1}

                    def update_page_display():
                        page_container.clear()
                        start_idx = (current_page['value'] - 1) * page_size
                        end_idx = min(start_idx + page_size, len(records_to_show))

                        with page_container:
                            for record in records_to_show[start_idx:end_idx]:
                                with ui.row().classes('w-full border-b p-2 hover:bg-gray-50'):
                                    for column in columns:
                                        value = record.get(column, '')
                                        # Truncate long values
                                        display_value = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                                        ui.label(display_value).classes('flex-1').tooltip(str(value))

                                    with ui.row().classes('w-32 gap-1'):
                                        ui.button(icon='edit', on_click=lambda r=record: edit_record(r)).props('size=sm flat dense')
                                        ui.button(icon='delete', on_click=lambda r=record: delete_record_confirm(r)).props('size=sm flat dense color=negative')

                    page_container = ui.column().classes('w-full')
                    update_page_display()

                    # Pagination controls
                    if total_pages > 1:
                        with ui.row().classes('w-full justify-center items-center gap-2 p-2'):
                            ui.button(
                                icon='chevron_left',
                                on_click=lambda: (setattr(current_page, 'value', max(1, current_page['value'] - 1)), update_page_display())
                            ).props('flat dense').bind_enabled_from(current_page, 'value', lambda v: v > 1)

                            ui.label().bind_text_from(current_page, 'value', lambda v: f'Page {v} of {total_pages}')

                            ui.button(
                                icon='chevron_right',
                                on_click=lambda: (setattr(current_page, 'value', min(total_pages, current_page['value'] + 1)), update_page_display())
                            ).props('flat dense').bind_enabled_from(current_page, 'value', lambda v: v < total_pages)

    async def create_record():
        """Create a new record"""
        if not selected_table['value']:
            ui.notify('Please select a table first', type='warning')
            return

        # Get table schema by fetching one record or use empty template
        sample_record = table_data['records'][0] if table_data['records'] else {}
        fields = list(sample_record.keys()) if sample_record else []

        # Remove 'id' field as it's auto-generated
        fields = [f for f in fields if f != 'id']

        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f'Create new {selected_table["value"]} record').classes('text-h6')

            form_data = {}
            inputs = {}

            for field in fields:
                inputs[field] = ui.input(field).classes('w-full')
                form_data[field] = ''

            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancel', on_click=dialog.close).props('flat')

                async def save():
                    try:
                        # Collect form data
                        data = {field: inputs[field].value for field in fields if inputs[field].value}

                        # Create record
                        await api_client.create_record(selected_table['value'], data)
                        ui.notify('Record created successfully', type='positive')
                        dialog.close()
                        await load_table_data()
                    except Exception as e:
                        ui.notify(f'Error creating record: {str(e)}', type='negative')

                ui.button('Save', on_click=save).props('color=primary')

        dialog.open()

    def edit_record(record: Dict):
        """Edit an existing record"""
        record_id = record.get('id')

        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f'Edit {selected_table["value"]} record #{record_id}').classes('text-h6')

            inputs = {}

            # Create input fields for each field except 'id'
            for field, value in record.items():
                if field != 'id':
                    inputs[field] = ui.input(field, value=str(value) if value is not None else '').classes('w-full')

            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancel', on_click=dialog.close).props('flat')

                async def save():
                    try:
                        # Collect updated data
                        data = {field: inputs[field].value for field in inputs if inputs[field].value != str(record.get(field, ''))}

                        if data:
                            # Update record
                            await api_client.update_record(selected_table['value'], record_id, data)
                            ui.notify('Record updated successfully', type='positive')
                            dialog.close()
                            await load_table_data()
                        else:
                            ui.notify('No changes made', type='info')
                    except Exception as e:
                        ui.notify(f'Error updating record: {str(e)}', type='negative')

                ui.button('Save', on_click=save).props('color=primary')

        dialog.open()

    def delete_record_confirm(record: Dict):
        """Confirm and delete a record"""
        record_id = record.get('id')

        with ui.dialog() as dialog, ui.card():
            ui.label(f'Delete {selected_table["value"]} record #{record_id}?').classes('text-h6')
            ui.label('This action cannot be undone.').classes('text-body2 text-gray-600')

            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancel', on_click=dialog.close).props('flat')

                async def confirm_delete():
                    try:
                        await api_client.delete_record(selected_table['value'], record_id)
                        ui.notify('Record deleted successfully', type='positive')
                        dialog.close()
                        await load_table_data()
                    except Exception as e:
                        ui.notify(f'Error deleting record: {str(e)}', type='negative')

                ui.button('Delete', on_click=confirm_delete).props('color=negative')

        dialog.open()

    def export_data():
        """Export filtered data as CSV"""
        if not table_data['filtered_records']:
            ui.notify('No data to export', type='warning')
            return

        # Create CSV in memory
        output = io.StringIO()
        if table_data['filtered_records']:
            writer = csv.DictWriter(output, fieldnames=table_data['filtered_records'][0].keys())
            writer.writeheader()
            writer.writerows(table_data['filtered_records'])

        # Download the CSV
        csv_content = output.getvalue()
        ui.download(csv_content.encode(), f'{selected_table["value"]}_export.csv')
        ui.notify(f'Exported {len(table_data["filtered_records"])} records', type='positive')

    # UI Layout
    with ui.column().classes('w-full p-4 gap-4'):
        ui.label('Database Admin').classes('text-h4')

        with ui.row().classes('w-full gap-4 items-center'):
            # Table selector
            table_select = ui.select(
                options=list(TABLE_INFO.keys()),
                label='Select Table',
                on_change=lambda: load_table_data()
            ).classes('w-64').bind_value_to(selected_table, 'value')

            # Action buttons
            ui.button('Refresh', icon='refresh', on_click=load_table_data)
            ui.button('Create New', icon='add', on_click=create_record).props('color=primary')
            ui.button('Clear Filters', icon='filter_alt_off', on_click=clear_filters)
            ui.button('Export CSV', icon='download', on_click=export_data)

        # Filter container
        with ui.expansion('Filters & Search', icon='filter_list').classes('w-full').props('default-opened'):
            filter_container = ui.column().classes('w-full')

        # Table container
        table_container = ui.column().classes('w-full')

# Conflict notes page - simplified working version
@ui.page('/conflicts')
async def conflicts():
    with ui.header().classes('bg-blue-600 text-white'):
        with ui.row().classes('w-full items-center'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat color=white')
            ui.label('Conflict Notes').classes('text-h6')

    # State management
    conflicts_data = {'conflicts': [], 'selected': None}
    selected_conflict_info = {'conflict': None}

    async def load_conflicts():
        """Load all conflicts"""
        try:
            conflicts = await api_client.get_records('conflictos')
            conflicts_data['conflicts'] = conflicts

            # Update select options
            options = {}
            for conflict in conflicts:
                descripcion = conflict.get('descripcion') or conflict.get('causa') or 'Sin descripción'
                desc_preview = descripcion[:50] + "..." if len(descripcion) > 50 else descripcion
                label = f"ID {conflict['id']}: {desc_preview}"
                if conflict.get('fecha_apertura'):
                    label += f" ({conflict['fecha_apertura']})"
                options[conflict['id']] = label

            conflict_select.set_options(options)
            ui.notify(f'Loaded {len(conflicts)} conflicts', type='positive')
        except Exception as e:
            ui.notify(f'Error loading conflicts: {str(e)}', type='negative')

    async def on_conflict_change(e):
        """Handle conflict selection change"""
        conflict_id = e.value
        conflicts_data['selected'] = conflict_id

        if conflict_id:
            selected_conflict = next((c for c in conflicts_data['conflicts'] if c['id'] == conflict_id), None)
            selected_conflict_info['conflict'] = selected_conflict
            await display_conflict_info()
            await load_conflict_history()

    async def display_conflict_info():
        """Display information about the selected conflict"""
        conflict_info_container.clear()

        conflict = selected_conflict_info['conflict']
        if not conflict:
            return

        with conflict_info_container:
            ui.label('Conflict Information').classes('text-h6 mb-2')

            with ui.card().classes('w-full'):
                info_items = [
                    ('ID', conflict.get('id', 'N/A')),
                    ('Estado', conflict.get('estado', 'N/A')),
                    ('Ámbito', conflict.get('ambito', 'N/A')),
                    ('Causa', conflict.get('causa', 'N/A')),
                    ('Fecha Apertura', conflict.get('fecha_apertura', 'N/A')),
                    ('Fecha Cierre', conflict.get('fecha_cierre', 'N/A')),
                    ('Descripción', conflict.get('descripcion', 'N/A'))
                ]

                for label, value in info_items:
                    with ui.row().classes('mb-1'):
                        ui.label(f"{label}:").classes('font-bold w-32')
                        ui.label(str(value) if value else 'N/A').classes('flex-grow')

    async def load_conflict_history():
        """Load history for selected conflict"""
        history_container.clear()

        if not conflicts_data['selected']:
            return

        try:
            # Get history entries
            history = await api_client.get_records('diario_conflictos', {'conflicto_id': f'eq.{conflicts_data["selected"]}'})

            # Sort by created_at descending
            history.sort(key=lambda x: x.get('created_at', ''), reverse=True)

            with history_container:
                ui.label('History').classes('text-h6 mb-2')

                if history:
                    for entry in history:
                        with ui.card().classes('w-full mb-2'):
                            with ui.row().classes('w-full justify-between mb-2'):
                                ui.label(entry.get('created_at', 'No date')).classes('text-caption text-gray-600')
                                if entry.get('estado'):
                                    ui.label(f"Estado: {entry['estado']}").classes('text-caption')

                            if entry.get('causa'):
                                ui.label(f"Causa: {entry['causa']}").classes('mb-1')
                            if entry.get('afectada'):
                                ui.label(f"Afectada: {entry['afectada']}").classes('mb-1')
                            if entry.get('ambito'):
                                ui.label(f"Ámbito: {entry['ambito']}").classes('mb-1')
                else:
                    ui.label('No history entries found').classes('text-gray-500')

        except Exception as e:
            ui.notify(f'Error loading history: {str(e)}', type='negative')

    async def add_note():
        """Add a new note to the selected conflict"""
        if not conflicts_data['selected']:
            ui.notify('Please select a conflict first', type='warning')
            return

        conflict = selected_conflict_info['conflict']
        if not conflict:
            return

        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f'Add Note to Conflict #{conflicts_data["selected"]}').classes('text-h6')

            # Form inputs
            estado_input = ui.select(
                options=['Abierto', 'En proceso', 'Resuelto', 'Cerrado'],
                label='Estado',
                value=conflict.get('estado', '')
            ).classes('w-full')

            ambito_input = ui.input(
                'Ámbito',
                value=conflict.get('ambito', '')
            ).classes('w-full')

            afectada_input = ui.input(
                'Afectada'
            ).classes('w-full')

            causa_input = ui.textarea(
                'Causa/Notes'
            ).classes('w-full')

            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancel', on_click=dialog.close).props('flat')

                async def save_note():
                    try:
                        # Prepare note data
                        note_data = {
                            'conflicto_id': conflicts_data['selected'],
                            'estado': estado_input.value or None,
                            'ambito': ambito_input.value or None,
                            'afectada': afectada_input.value or None,
                            'causa': causa_input.value or None,
                            'created_at': datetime.now().isoformat()
                        }

                        # Remove None values
                        note_data = {k: v for k, v in note_data.items() if v is not None}

                        # Save to diario_conflictos
                        await api_client.create_record('diario_conflictos', note_data)

                        # Update conflict if estado changed
                        if estado_input.value and estado_input.value != conflict.get('estado'):
                            await api_client.update_record('conflictos', conflicts_data['selected'], {
                                'estado': estado_input.value
                            })

                        ui.notify('Note added successfully', type='positive')
                        dialog.close()
                        await load_conflicts()
                        await display_conflict_info()
                        await load_conflict_history()
                    except Exception as e:
                        ui.notify(f'Error adding note: {str(e)}', type='negative')

                ui.button('Save', on_click=save_note).props('color=primary')

        dialog.open()

    # UI Layout
    with ui.column().classes('w-full p-4 gap-4'):
        ui.label('Conflict Notes - Diario de Conflictos').classes('text-h4')

        with ui.row().classes('w-full gap-4'):
            # Left panel - Conflict selection
            with ui.column().classes('w-96 gap-4'):
                with ui.row().classes('w-full gap-2'):
                    conflict_select = ui.select(
                        options={},
                        label='Select Conflict',
                        on_change=on_conflict_change
                    ).classes('flex-grow')

                    ui.button(icon='refresh', on_click=load_conflicts).props('flat')

                ui.button('Add Note', icon='add_comment', on_click=add_note).props('color=primary').classes('w-full')

                # Conflict info
                conflict_info_container = ui.column().classes('w-full')

            # Right panel - History
            with ui.column().classes('flex-grow'):
                history_container = ui.column().classes('w-full gap-4')

    # Load conflicts on page load
    await load_conflicts()

# Run the application
ui.run(host='0.0.0.0', port=8081, title='Sindicato INQ Management')