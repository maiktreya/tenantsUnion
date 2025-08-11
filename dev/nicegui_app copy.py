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

# Materialized View metadata
VIEW_INFO = {
    'v_afiliadas': {'display_name': 'Info completa de Afiliadas'},
    'v_bloques': {'display_name': 'Info de Bloques'},
    'v_empresas': {'display_name': 'Info completa de Empresas'},
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
        """Get all records from a table or view with optional filters"""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}"
        params = filters or {}
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            ui.notify(f'Error al obtener registros: {str(e)}', type='negative')
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

# Global state for current view and containers
current_view = {'value': 'home'}
content_containers = {}

def show_view(view_name: str):
    """Show a specific view and hide others"""
    current_view['value'] = view_name
    for name, container in content_containers.items():
        container.set_visibility(name == view_name)

# Global state for different modules
admin_state = {
    'selected_table': {'value': None},
    'table_data': {'records': [], 'filtered_records': []},
    'sort_config': {'column': None, 'ascending': True},
    'filter_config': {},
    'filter_container': None,
    'table_container': None,
    'current_page': {'value': 1},
    'page_size': 10,
    'page_container': None,
    'pagination_container': None
}

views_state = {
    'selected_view': {'value': None},
    'view_data': {'records': [], 'filtered_records': []},
    'sort_config': {'column': None, 'ascending': True},
    'filter_config': {},
    'filter_container': None,
    'table_container': None,
    'current_page': {'value': 1},
    'page_size': 10,
    'page_container': None,
    'pagination_container': None
}

conflicts_state = {
    'conflicts_data': {'conflicts': [], 'selected': None},
    'selected_conflict_info': {'conflict': None},
    'conflict_select': None,
    'conflict_info_container': None,
    'history_container': None
}

def create_home_content():
    """Create the home page content"""
    with ui.column().classes('w-full p-8 items-center gap-8'):
        ui.label('Bienvenido al Sistema de Gestión del Sindicato INQ').classes('text-h4')

        with ui.row().classes('gap-8 flex-wrap justify-center'):
            with ui.card().classes('w-80 cursor-pointer').on('click', lambda: show_view('admin')):
                with ui.column().classes('items-center gap-4 p-4'):
                    ui.icon('storage', size='4rem')
                    ui.label('Administración de Tablas').classes('text-h6')
                    ui.label('Gestionar todas las tablas de la base de datos con operaciones CRUD completas').classes('text-center')

            with ui.card().classes('w-80 cursor-pointer').on('click', lambda: show_view('views')):
                with ui.column().classes('items-center gap-4 p-4'):
                    ui.icon('table_view', size='4rem')
                    ui.label('Explorador de Vistas').classes('text-h6')
                    ui.label('Explorar datos de vistas materializadas predefinidas').classes('text-center')

            with ui.card().classes('w-80 cursor-pointer').on('click', lambda: show_view('conflicts')):
                with ui.column().classes('items-center gap-4 p-4'):
                    ui.icon('gavel', size='4rem')
                    ui.label('Gestor de Conflictos').classes('text-h6')
                    ui.label('Añadir notas y seguir el historial de conflictos').classes('text-center')

# --- Admin (Tables) Functions ---

async def load_table_data():
    """Load data for the selected table"""
    if not admin_state['selected_table']['value']:
        return

    try:
        records = await api_client.get_records(admin_state['selected_table']['value'])
        admin_state['table_data']['records'] = records
        admin_state['table_data']['filtered_records'] = records.copy()
        admin_state['filter_config'].clear()
        admin_state['sort_config']['column'] = None
        admin_state['sort_config']['ascending'] = True
        refresh_table()
        setup_filters()
        ui.notify(f'Se cargaron {len(records)} registros', type='positive')
    except Exception as e:
        ui.notify(f'Error al cargar datos: {str(e)}', type='negative')

def apply_filters():
    """Apply all active filters to the data"""
    filtered = admin_state['table_data']['records'].copy()

    for column, filter_value in admin_state['filter_config'].items():
        if filter_value:
            filtered = [
                record for record in filtered
                if str(filter_value).lower() in str(record.get(column, '')).lower()
            ]

    admin_state['table_data']['filtered_records'] = filtered
    apply_sort()

def apply_sort():
    """Apply sorting to the filtered data"""
    if admin_state['sort_config']['column']:
        admin_state['table_data']['filtered_records'].sort(
            key=lambda x: x.get(admin_state['sort_config']['column'], ''),
            reverse=not admin_state['sort_config']['ascending']
        )
    admin_state['current_page']['value'] = 1
    refresh_table()

def sort_by_column(column: str):
    """Sort by a specific column"""
    if admin_state['sort_config']['column'] == column:
        admin_state['sort_config']['ascending'] = not admin_state['sort_config']['ascending']
    else:
        admin_state['sort_config']['column'] = column
        admin_state['sort_config']['ascending'] = True
    apply_sort()

def setup_filters():
    """Setup filter inputs for each column"""
    if not admin_state['filter_container']:
        return

    admin_state['filter_container'].clear()

    if not admin_state['table_data']['records']:
        return

    columns = list(admin_state['table_data']['records'][0].keys())

    with admin_state['filter_container']:
        ui.label('Filtros').classes('text-h6 mb-2')
        with ui.row().classes('w-full gap-2 flex-wrap'):
            for column in columns:
                ui.input(
                    label=f'Filtrar {column}',
                    on_change=lambda e, col=column: update_filter(col, e.value)
                ).classes('w-48').props('dense clearable')

def update_filter(column: str, value: str):
    """Update filter for a specific column"""
    admin_state['filter_config'][column] = value
    admin_state['current_page']['value'] = 1
    apply_filters()

def clear_filters():
    """Clear all filters"""
    admin_state['filter_config'].clear()
    admin_state['table_data']['filtered_records'] = admin_state['table_data']['records'].copy()
    admin_state['current_page']['value'] = 1
    setup_filters()
    refresh_table()

def refresh_table():
    """Refresh the table display"""
    if not admin_state['table_container']:
        return
    admin_state['table_container'].clear()
    records_to_show = admin_state['table_data']['filtered_records']
    if not records_to_show:
        with admin_state['table_container']:
            ui.label('No se encontraron registros').classes('text-gray-500')
        return
    with admin_state['table_container']:
        ui.label(f'Mostrando {len(records_to_show)} de {len(admin_state["table_data"]["records"])} registros').classes('text-caption text-gray-600 mb-2')
        total_pages = max(1, (len(records_to_show) - 1) // admin_state['page_size'] + 1)
        if admin_state['current_page']['value'] > total_pages:
            admin_state['current_page']['value'] = total_pages
        admin_state['page_container'] = ui.column().classes('w-full')
        update_page_display()
        if total_pages > 1:
            admin_state['pagination_container'] = ui.row().classes('w-full justify-center items-center gap-2 p-2')
            update_pagination_controls()

def update_page_display():
    """Update the current page display"""
    if not admin_state['page_container']:
        return
    admin_state['page_container'].clear()
    records_to_show = admin_state['table_data']['filtered_records']
    start_idx = (admin_state['current_page']['value'] - 1) * admin_state['page_size']
    end_idx = min(start_idx + admin_state['page_size'], len(records_to_show))
    if records_to_show:
        columns = list(records_to_show[0].keys())
        with admin_state['page_container']:
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full bg-gray-100 p-2'):
                    for column in columns:
                        with ui.row().classes('flex-1 items-center cursor-pointer').on('click', lambda c=column: sort_by_column(c)):
                            ui.label(column).classes('font-bold')
                            if admin_state['sort_config']['column'] == column:
                                ui.icon('arrow_upward' if admin_state['sort_config']['ascending'] else 'arrow_downward', size='sm')
                    ui.label('Acciones').classes('font-bold w-32')
                for record in records_to_show[start_idx:end_idx]:
                    with ui.row().classes('w-full border-b p-2 hover:bg-gray-50 items-center'):
                        for column in columns:
                            value = record.get(column, '')
                            display_value = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                            ui.label(display_value).classes('flex-1').tooltip(str(value))
                        with ui.row().classes('w-32 gap-1'):
                            ui.button(icon='edit', on_click=lambda r=record: edit_record(r)).props('size=sm flat dense')
                            ui.button(icon='delete', on_click=lambda r=record: delete_record_confirm(r)).props('size=sm flat dense color=negative')

def update_pagination_controls():
    """Update pagination controls"""
    if not admin_state['pagination_container']:
        return
    admin_state['pagination_container'].clear()
    records_to_show = admin_state['table_data']['filtered_records']
    total_pages = max(1, (len(records_to_show) - 1) // admin_state['page_size'] + 1)
    with admin_state['pagination_container']:
        ui.button(icon='first_page', on_click=lambda: go_to_page(1)).props('flat dense').bind_enabled_from(admin_state['current_page'], 'value', lambda v: v > 1)
        ui.button(icon='chevron_left', on_click=lambda: go_to_page(admin_state['current_page']['value'] - 1)).props('flat dense').bind_enabled_from(admin_state['current_page'], 'value', lambda v: v > 1)
        with ui.row().classes('items-center gap-2'):
            ui.label('Página')
            ui.number(value=admin_state['current_page']['value'], min=1, max=total_pages, on_change=lambda e: go_to_page(int(e.value)) if e.value and 1 <= int(e.value) <= total_pages else None).props('dense outlined').classes('w-16')
            ui.label(f'de {total_pages}')
        ui.button(icon='chevron_right', on_click=lambda: go_to_page(admin_state['current_page']['value'] + 1)).props('flat dense').bind_enabled_from(admin_state['current_page'], 'value', lambda v: v < total_pages)
        ui.button(icon='last_page', on_click=lambda: go_to_page(total_pages)).props('flat dense').bind_enabled_from(admin_state['current_page'], 'value', lambda v: v < total_pages)
        with ui.row().classes('items-center gap-2 ml-4'):
            ui.label('Mostrar:')
            ui.select(options=[5, 10, 25, 50, 100], value=admin_state['page_size'], on_change=lambda e: change_page_size(e.value)).props('dense').classes('w-20')
            ui.label('por página')

def go_to_page(page_num: int):
    """Navigate to a specific page"""
    records_to_show = admin_state['table_data']['filtered_records']
    total_pages = max(1, (len(records_to_show) - 1) // admin_state['page_size'] + 1)
    if 1 <= page_num <= total_pages:
        admin_state['current_page']['value'] = page_num
        update_page_display()
        update_pagination_controls()

def change_page_size(new_size: int):
    """Change the number of records per page"""
    admin_state['page_size'] = new_size
    admin_state['current_page']['value'] = 1
    refresh_table()

async def create_record():
    """Create a new record"""
    if not admin_state['selected_table']['value']:
        ui.notify('Por favor, seleccione una tabla primero', type='warning')
        return
    sample_record = admin_state['table_data']['records'][0] if admin_state['table_data']['records'] else {}
    fields = [f for f in list(sample_record.keys()) if f != 'id']
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label(f'Crear nuevo registro en {admin_state["selected_table"]["value"]}').classes('text-h6')
        inputs = {field: ui.input(field).classes('w-full') for field in fields}
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat')
            async def save():
                try:
                    data = {field: inputs[field].value for field in fields if inputs[field].value}
                    await api_client.create_record(admin_state['selected_table']['value'], data)
                    ui.notify('Registro creado con éxito', type='positive')
                    dialog.close()
                    await load_table_data()
                except Exception as e:
                    ui.notify(f'Error al crear el registro: {str(e)}', type='negative')
            ui.button('Guardar', on_click=save).props('color=orange-600')
    dialog.open()

def edit_record(record: Dict):
    """Edit an existing record"""
    record_id = record.get('id')
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label(f'Editar registro #{record_id} de {admin_state["selected_table"]["value"]}').classes('text-h6')
        inputs = {field: ui.input(field, value=str(value) if value is not None else '').classes('w-full') for field, value in record.items() if field != 'id'}
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat')
            async def save():
                try:
                    data = {field: inputs[field].value for field in inputs if inputs[field].value != str(record.get(field, ''))}
                    if data:
                        await api_client.update_record(admin_state['selected_table']['value'], record_id, data)
                        ui.notify('Registro actualizado con éxito', type='positive')
                        dialog.close()
                        await load_table_data()
                    else:
                        ui.notify('No se realizaron cambios', type='info')
                except Exception as e:
                    ui.notify(f'Error al actualizar el registro: {str(e)}', type='negative')
            ui.button('Guardar', on_click=save).props('color=orange-600')
    dialog.open()

def delete_record_confirm(record: Dict):
    """Confirm and delete a record"""
    record_id = record.get('id')
    with ui.dialog() as dialog, ui.card():
        ui.label(f'¿Eliminar registro #{record_id} de {admin_state["selected_table"]["value"]}?').classes('text-h6')
        ui.label('Esta acción no se puede deshacer.').classes('text-body2 text-gray-600')
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat')
            async def confirm_delete():
                try:
                    await api_client.delete_record(admin_state['selected_table']['value'], record_id)
                    ui.notify('Registro eliminado con éxito', type='positive')
                    dialog.close()
                    await load_table_data()
                except Exception as e:
                    ui.notify(f'Error al eliminar el registro: {str(e)}', type='negative')
            ui.button('Eliminar', on_click=confirm_delete).props('color=negative')
    dialog.open()

def export_data(source_state: dict, filename_prefix: str):
    """Export filtered data as CSV"""
    records_to_export = source_state['filtered_records']
    if not records_to_export:
        ui.notify('No hay datos para exportar', type='warning')
        return
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=records_to_export[0].keys())
    writer.writeheader()
    writer.writerows(records_to_export)
    csv_content = output.getvalue()
    ui.download(csv_content.encode(), f'{filename_prefix}_export.csv')
    ui.notify(f'Se exportaron {len(records_to_export)} registros', type='positive')

def create_admin_content():
    """Create the admin page content"""
    with ui.column().classes('w-full p-4 gap-4'):
        ui.label('Administración de Tablas').classes('text-h4')
        with ui.row().classes('w-full gap-4 items-center'):
            ui.select(options=list(TABLE_INFO.keys()), label='Seleccionar Tabla', on_change=lambda: ui.timer(0.1, load_table_data, once=True)).classes('w-64').bind_value_to(admin_state['selected_table'], 'value')
            ui.button('Refrescar', icon='refresh', on_click=lambda: ui.timer(0.1, load_table_data, once=True)).props('color=orange-600')
            ui.button('Crear Nuevo', icon='add', on_click=lambda: ui.timer(0.1, create_record, once=True)).props('color=orange-600')
            ui.button('Limpiar Filtros', icon='filter_alt_off', on_click=clear_filters).props('color=orange-600')
            ui.button('Exportar CSV', icon='download', on_click=lambda: export_data(admin_state['table_data'], admin_state['selected_table']['value'])).props('color=orange-600')
        with ui.expansion('Filtros y Búsqueda', icon='filter_list').classes('w-full').props('default-opened'):
            admin_state['filter_container'] = ui.column().classes('w-full')
        admin_state['table_container'] = ui.column().classes('w-full')

# --- Views Functions ---

async def load_view_data():
    """Load data for the selected view"""
    if not views_state['selected_view']['value']:
        return
    try:
        records = await api_client.get_records(views_state['selected_view']['value'])
        views_state['view_data']['records'] = records
        views_state['view_data']['filtered_records'] = records.copy()
        views_state['filter_config'].clear()
        views_state['sort_config']['column'] = None
        views_state['sort_config']['ascending'] = True
        refresh_view_table()
        setup_view_filters()
        ui.notify(f'Se cargaron {len(records)} registros de la vista', type='positive')
    except Exception as e:
        ui.notify(f'Error al cargar datos de la vista: {str(e)}', type='negative')

def apply_view_filters():
    """Apply all active filters to the view data"""
    filtered = views_state['view_data']['records'].copy()
    for column, filter_value in views_state['filter_config'].items():
        if filter_value:
            filtered = [record for record in filtered if str(filter_value).lower() in str(record.get(column, '')).lower()]
    views_state['view_data']['filtered_records'] = filtered
    apply_view_sort()

def apply_view_sort():
    """Apply sorting to the filtered view data"""
    if views_state['sort_config']['column']:
        views_state['view_data']['filtered_records'].sort(
            key=lambda x: x.get(views_state['sort_config']['column'], ''),
            reverse=not views_state['sort_config']['ascending']
        )
    views_state['current_page']['value'] = 1
    refresh_view_table()

def sort_view_by_column(column: str):
    """Sort view by a specific column"""
    if views_state['sort_config']['column'] == column:
        views_state['sort_config']['ascending'] = not views_state['sort_config']['ascending']
    else:
        views_state['sort_config']['column'] = column
        views_state['sort_config']['ascending'] = True
    apply_view_sort()

def setup_view_filters():
    """Setup filter inputs for each column of the view"""
    if not views_state['filter_container']:
        return
    views_state['filter_container'].clear()
    if not views_state['view_data']['records']:
        return
    columns = list(views_state['view_data']['records'][0].keys())
    with views_state['filter_container']:
        ui.label('Filtros').classes('text-h6 mb-2')
        with ui.row().classes('w-full gap-2 flex-wrap'):
            for column in columns:
                ui.input(label=f'Filtrar {column}', on_change=lambda e, col=column: update_view_filter(col, e.value)).classes('w-48').props('dense clearable')

def update_view_filter(column: str, value: str):
    """Update filter for a specific column in the view"""
    views_state['filter_config'][column] = value
    views_state['current_page']['value'] = 1
    apply_view_filters()

def clear_view_filters():
    """Clear all view filters"""
    views_state['filter_config'].clear()
    views_state['view_data']['filtered_records'] = views_state['view_data']['records'].copy()
    views_state['current_page']['value'] = 1
    setup_view_filters()
    refresh_view_table()

def refresh_view_table():
    """Refresh the view table display"""
    if not views_state['table_container']:
        return
    views_state['table_container'].clear()
    records_to_show = views_state['view_data']['filtered_records']
    if not records_to_show:
        with views_state['table_container']:
            ui.label('No se encontraron registros').classes('text-gray-500')
        return
    with views_state['table_container']:
        ui.label(f'Mostrando {len(records_to_show)} de {len(views_state["view_data"]["records"])} registros').classes('text-caption text-gray-600 mb-2')
        total_pages = max(1, (len(records_to_show) - 1) // views_state['page_size'] + 1)
        if views_state['current_page']['value'] > total_pages:
            views_state['current_page']['value'] = total_pages
        views_state['page_container'] = ui.column().classes('w-full')
        update_view_page_display()
        if total_pages > 1:
            views_state['pagination_container'] = ui.row().classes('w-full justify-center items-center gap-2 p-2')
            update_view_pagination_controls()

def update_view_page_display():
    """Update the current view page display"""
    if not views_state['page_container']:
        return
    views_state['page_container'].clear()
    records_to_show = views_state['view_data']['filtered_records']
    start_idx = (views_state['current_page']['value'] - 1) * views_state['page_size']
    end_idx = min(start_idx + views_state['page_size'], len(records_to_show))
    if records_to_show:
        columns = list(records_to_show[0].keys())
        with views_state['page_container']:
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full bg-gray-100 p-2'):
                    for column in columns:
                        with ui.row().classes('flex-1 items-center cursor-pointer').on('click', lambda c=column: sort_view_by_column(c)):
                            ui.label(column).classes('font-bold')
                            if views_state['sort_config']['column'] == column:
                                ui.icon('arrow_upward' if views_state['sort_config']['ascending'] else 'arrow_downward', size='sm')
                for record in records_to_show[start_idx:end_idx]:
                    with ui.row().classes('w-full border-b p-2 hover:bg-gray-50 items-center'):
                        for column in columns:
                            value = record.get(column, '')
                            display_value = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                            ui.label(display_value).classes('flex-1').tooltip(str(value))

def update_view_pagination_controls():
    """Update view pagination controls"""
    if not views_state['pagination_container']:
        return
    views_state['pagination_container'].clear()
    records_to_show = views_state['view_data']['filtered_records']
    total_pages = max(1, (len(records_to_show) - 1) // views_state['page_size'] + 1)
    with views_state['pagination_container']:
        ui.button(icon='first_page', on_click=lambda: go_to_view_page(1)).props('flat dense').bind_enabled_from(views_state['current_page'], 'value', lambda v: v > 1)
        ui.button(icon='chevron_left', on_click=lambda: go_to_view_page(views_state['current_page']['value'] - 1)).props('flat dense').bind_enabled_from(views_state['current_page'], 'value', lambda v: v > 1)
        with ui.row().classes('items-center gap-2'):
            ui.label('Página')
            ui.number(value=views_state['current_page']['value'], min=1, max=total_pages, on_change=lambda e: go_to_view_page(int(e.value)) if e.value and 1 <= int(e.value) <= total_pages else None).props('dense outlined').classes('w-16')
            ui.label(f'de {total_pages}')
        ui.button(icon='chevron_right', on_click=lambda: go_to_view_page(views_state['current_page']['value'] + 1)).props('flat dense').bind_enabled_from(views_state['current_page'], 'value', lambda v: v < total_pages)
        ui.button(icon='last_page', on_click=lambda: go_to_view_page(total_pages)).props('flat dense').bind_enabled_from(views_state['current_page'], 'value', lambda v: v < total_pages)
        with ui.row().classes('items-center gap-2 ml-4'):
            ui.label('Mostrar:')
            ui.select(options=[5, 10, 25, 50, 100], value=views_state['page_size'], on_change=lambda e: change_view_page_size(e.value)).props('dense').classes('w-20')
            ui.label('por página')

def go_to_view_page(page_num: int):
    """Navigate to a specific view page"""
    records_to_show = views_state['view_data']['filtered_records']
    total_pages = max(1, (len(records_to_show) - 1) // views_state['page_size'] + 1)
    if 1 <= page_num <= total_pages:
        views_state['current_page']['value'] = page_num
        update_view_page_display()
        update_view_pagination_controls()

def change_view_page_size(new_size: int):
    """Change the number of records per page for views"""
    views_state['page_size'] = new_size
    views_state['current_page']['value'] = 1
    refresh_view_table()

def create_views_content():
    """Create the views explorer page content"""
    with ui.column().classes('w-full p-4 gap-4'):
        ui.label('Explorador de Vistas').classes('text-h4')
        with ui.row().classes('w-full gap-4 items-center'):
            ui.select(options=list(VIEW_INFO.keys()), label='Seleccionar Vista', on_change=lambda: ui.timer(0.1, load_view_data, once=True)).classes('w-64').bind_value_to(views_state['selected_view'], 'value')
            ui.button('Refrescar', icon='refresh', on_click=lambda: ui.timer(0.1, load_view_data, once=True))
            ui.button('Limpiar Filtros', icon='filter_alt_off', on_click=clear_view_filters)
            ui.button('Exportar CSV', icon='download', on_click=lambda: export_data(views_state['view_data'], views_state['selected_view']['value']))
        with ui.expansion('Filtros y Búsqueda', icon='filter_list').classes('w-full').props('default-opened'):
            views_state['filter_container'] = ui.column().classes('w-full')
        views_state['table_container'] = ui.column().classes('w-full')

# --- Conflicts Functions ---

async def load_conflicts():
    """Load all conflicts"""
    try:
        conflicts = await api_client.get_records('conflictos')
        conflicts_state['conflicts_data']['conflicts'] = conflicts
        options = {}
        for conflict in conflicts:
            descripcion = conflict.get('descripcion') or conflict.get('causa') or 'Sin descripción'
            desc_preview = descripcion[:50] + "..." if len(descripcion) > 50 else descripcion
            label = f"ID {conflict['id']}: {desc_preview}"
            if conflict.get('fecha_apertura'):
                label += f" ({conflict['fecha_apertura']})"
            options[conflict['id']] = label
        if conflicts_state['conflict_select']:
            conflicts_state['conflict_select'].set_options(options)
        ui.notify(f'Se cargaron {len(conflicts)} conflictos', type='positive')
    except Exception as e:
        ui.notify(f'Error al cargar conflictos: {str(e)}', type='negative')

async def on_conflict_change(e):
    """Handle conflict selection change"""
    conflict_id = e.value
    conflicts_state['conflicts_data']['selected'] = conflict_id
    if conflict_id:
        selected_conflict = next((c for c in conflicts_state['conflicts_data']['conflicts'] if c['id'] == conflict_id), None)
        conflicts_state['selected_conflict_info']['conflict'] = selected_conflict
        await display_conflict_info()
        await load_conflict_history()

async def display_conflict_info():
    """Display information about the selected conflict"""
    if not conflicts_state['conflict_info_container']:
        return
    conflicts_state['conflict_info_container'].clear()
    conflict = conflicts_state['selected_conflict_info']['conflict']
    if not conflict:
        return
    with conflicts_state['conflict_info_container']:
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

async def load_conflict_history():
    """Load history for selected conflict"""
    if not conflicts_state['history_container']:
        return
    conflicts_state['history_container'].clear()
    if not conflicts_state['conflicts_data']['selected']:
        return
    try:
        history = await api_client.get_records('diario_conflictos', {'conflicto_id': f'eq.{conflicts_state["conflicts_data"]["selected"]}'})
        history.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        with conflicts_state['history_container']:
            ui.label('Historial').classes('text-h6 mb-2')
            if history:
                for entry in history:
                    with ui.card().classes('w-full mb-2'):
                        with ui.row().classes('w-full justify-between mb-2'):
                            ui.label(entry.get('created_at', 'Sin fecha')).classes('text-caption text-gray-600')
                            if entry.get('estado'):
                                ui.label(f"Estado: {entry['estado']}").classes('text-caption')
                        if entry.get('causa'):
                            ui.label(f"Causa: {entry['causa']}").classes('mb-1')
                        if entry.get('afectada'):
                            ui.label(f"Afectada: {entry['afectada']}").classes('mb-1')
                        if entry.get('ambito'):
                            ui.label(f"Ámbito: {entry['ambito']}").classes('mb-1')
            else:
                ui.label('No se encontraron entradas en el historial').classes('text-gray-500')
    except Exception as e:
        ui.notify(f'Error al cargar el historial: {str(e)}', type='negative')

async def add_note():
    """Add a new note to the selected conflict"""
    if not conflicts_state['conflicts_data']['selected']:
        ui.notify('Por favor, seleccione un conflicto primero', type='warning')
        return
    conflict = conflicts_state['selected_conflict_info']['conflict']
    if not conflict:
        return
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label(f'Añadir Nota al Conflicto #{conflicts_state["conflicts_data"]["selected"]}').classes('text-h6')
        estado_input = ui.select(options=['Abierto', 'En proceso', 'Resuelto', 'Cerrado'], label='Estado', value=conflict.get('estado', '')).classes('w-full')
        ambito_input = ui.input('Ámbito', value=conflict.get('ambito', '')).classes('w-full')
        afectada_input = ui.input('Afectada').classes('w-full')
        causa_input = ui.textarea('Causa/Notas').classes('w-full')
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat')
            async def save_note():
                try:
                    note_data = {
                        'conflicto_id': conflicts_state['conflicts_data']['selected'],
                        'estado': estado_input.value or None,
                        'ambito': ambito_input.value or None,
                        'afectada': afectada_input.value or None,
                        'causa': causa_input.value or None,
                        'created_at': datetime.now().isoformat()
                    }
                    note_data = {k: v for k, v in note_data.items() if v is not None}
                    await api_client.create_record('diario_conflictos', note_data)
                    if estado_input.value and estado_input.value != conflict.get('estado'):
                        await api_client.update_record('conflictos', conflicts_state['conflicts_data']['selected'], {'estado': estado_input.value})
                    ui.notify('Nota añadida con éxito', type='positive')
                    dialog.close()
                    await load_conflicts()
                    await on_conflict_change(ui.events.ValueChangeEventArguments(sender=None, client=None, value=conflicts_state['conflicts_data']['selected']))
                except Exception as e:
                    ui.notify(f'Error al añadir la nota: {str(e)}', type='negative')
            ui.button('Guardar', on_click=save_note).props('color=orange-600')
    dialog.open()

def create_conflicts_content():
    """Create the conflicts page content"""
    with ui.column().classes('w-full p-4 gap-4'):
        ui.label('Gestor de Conflictos').classes('text-h4')
        with ui.row().classes('w-full gap-4'):
            with ui.column().classes('w-96 gap-4'):
                with ui.row().classes('w-full gap-2'):
                    conflicts_state['conflict_select'] = ui.select(options={}, label='Seleccionar Conflicto', on_change=lambda e: ui.timer(0.1, lambda: on_conflict_change(e), once=True)).classes('flex-grow')
                    ui.button(icon='refresh', on_click=lambda: ui.timer(0.1, load_conflicts, once=True)).props('flat')
                ui.button('Añadir Nota', icon='add_comment', on_click=lambda: ui.timer(0.1, add_note, once=True)).props('color=orange-600').classes('w-full')
                conflicts_state['conflict_info_container'] = ui.column().classes('w-full')
            with ui.column().classes('flex-grow'):
                conflicts_state['history_container'] = ui.column().classes('w-full gap-4')
    ui.timer(0.5, load_conflicts, once=True)

# --- Main SPA Page ---
@ui.page('/')
async def spa_page():
    # Header with navigation
    with ui.header().classes('bg-orange-600 text-white'):
        with ui.row().classes('w-full items-center p-2'):
            ui.label('Gestión Sindicato INQ').classes('text-h6')
            ui.space()
            with ui.row().classes('gap-2'):
                ui.button('Inicio', on_click=lambda: show_view('home')).props('flat color=white')
                ui.button('Tablas', on_click=lambda: show_view('admin')).props('flat color=white')
                ui.button('Vistas', on_click=lambda: show_view('views')).props('flat color=white')
                ui.button('Conflictos', on_click=lambda: show_view('conflicts')).props('flat color=white')

    # Create all content containers
    with ui.column().classes('w-full min-h-screen'):
        content_containers['home'] = ui.column().classes('w-full')
        with content_containers['home']:
            create_home_content()

        content_containers['admin'] = ui.column().classes('w-full')
        with content_containers['admin']:
            create_admin_content()

        content_containers['views'] = ui.column().classes('w-full')
        with content_containers['views']:
            create_views_content()

        content_containers['conflicts'] = ui.column().classes('w-full')
        with content_containers['conflicts']:
            create_conflicts_content()

    # Show home by default
    show_view('home')

# Run the application
ui.run(host='0.0.0.0', port=8081, title='Gestión Sindicato INQ')
