from typing import List, Dict, Optional, Callable
from nicegui import ui
from api.client import APIClient

class DataTableComponent:
    """Self-contained reusable data table component with API client"""

    def __init__(
        self,
        api_client: APIClient,
        endpoint: str = None,
        data: List[Dict] = None,
        editable: bool = True,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None
    ):
        # Dependencies
        self.api_client = api_client
        self.endpoint = endpoint

        # Props
        self.initial_data = data or []
        self.editable = editable
        self.on_edit = on_edit
        self.on_delete = on_delete

        # Internal state
        self.records = []
        self.filtered_records = []
        self.filters = {}
        self.sort_column = None
        self.sort_ascending = True
        self.current_page = 1
        self.page_size = 10

        # UI references
        self.container = None
        self.table = None

    def mount(self) -> ui.column:
        """Mount the component and return its container"""
        self.container = ui.column().classes('w-full')
        self._initialize_data()
        self._render()
        return self.container

    def _initialize_data(self):
        """Initialize data from props"""
        if self.initial_data:
            self.records = self.initial_data
            self.filtered_records = self.initial_data.copy()
        elif self.endpoint:
            ui.timer(0.1, self._fetch_data, once=True)

    async def _fetch_data(self):
        """Fetch data using API client"""
        if not self.endpoint:
            return

        try:
            ui.spinner().classes('absolute inset-0')
            data = await self.api_client.get(self.endpoint)
            self.records = data if isinstance(data, list) else []
            self.filtered_records = self.records.copy()
            self._render()
            ui.notify(f'Loaded {len(self.records)} records', type='positive')
        except Exception as e:
            ui.notify(f'Error loading data: {e}', type='negative')
            self.records = []
            self.filtered_records = []
            self._render()

    def _render(self):
        """Render the component"""
        if not self.container:
            return

        self.container.clear()

        with self.container:
            # Toolbar
            with ui.row().classes('w-full gap-2 mb-4'):
                ui.input(
                    'Search...',
                    on_change=self._handle_search
                ).props('dense outlined').classes('flex-grow')

                ui.button(
                    icon='refresh',
                    on_click=self._fetch_data
                ).props('flat')

                if self.endpoint and self.editable:
                    ui.button(
                        'Add New',
                        icon='add',
                        on_click=self._show_add_dialog
                    ).props('color=primary')

                if self.filtered_records:
                    ui.button(
                        icon='download',
                        on_click=self._export_data
                    ).props('flat')

            # Table
            self._render_table()

            # Pagination
            if self.filtered_records:
                self._render_pagination()

    def _render_table(self):
        """Render the table"""
        if not self.filtered_records:
            ui.label('No data available').classes('text-gray-500')
            return

        # Calculate pagination
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_records = self.filtered_records[start:end]

        # Create table
        columns = [
            {'name': k, 'label': k.replace('_', ' ').title(), 'field': k, 'sortable': True}
            for k in page_records[0].keys()
        ]

        if self.editable:
            columns.append({
                'name': 'actions',
                'label': 'Actions',
                'field': 'actions'
            })

        rows = []
        for record in page_records:
            row = record.copy()
            if self.editable:
                row['actions'] = record.get('id', '')
            rows.append(row)

        self.table = ui.table(
            columns=columns,
            rows=rows,
            row_key='id',
            pagination={'rowsPerPage': self.page_size}
        ).classes('w-full')

        # Add action buttons if editable
        if self.editable:
            self.table.add_slot(
                'body-cell-actions',
                r'''
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('edit', props.row)" icon="edit" flat dense />
                    <q-btn @click="$parent.$emit('delete', props.row)" icon="delete" flat dense color="negative" />
                </q-td>
                '''
            )
            self.table.on('edit', lambda e: self._handle_edit(e.args))
            self.table.on('delete', lambda e: self._handle_delete(e.args))

    def _render_pagination(self):
        """Render pagination controls"""
        total_pages = max(1, -(-len(self.filtered_records) // self.page_size))

        with ui.row().classes('w-full justify-center items-center gap-2 mt-4'):
            ui.button(
                icon='chevron_left',
                on_click=self._prev_page
            ).props('flat').bind_enabled_from(self, 'current_page', lambda p: p > 1)

            ui.label().bind_text_from(
                self,
                'current_page',
                lambda p: f'Page {p} of {total_pages}'
            )

            ui.button(
                icon='chevron_right',
                on_click=self._next_page
            ).props('flat').bind_enabled_from(
                self,
                'current_page',
                lambda p: p < total_pages
            )

            # Page size selector
            ui.select(
                options=[5, 10, 25, 50],
                value=self.page_size,
                on_change=self._handle_page_size_change
            ).props('dense outlined').classes('w-20')

    def _handle_search(self, e):
        """Handle search input"""
        search_term = e.value.lower()
        if search_term:
            self.filtered_records = [
                r for r in self.records
                if any(search_term in str(v).lower() for v in r.values())
            ]
        else:
            self.filtered_records = self.records.copy()
        self.current_page = 1
        self._render()

    def _handle_edit(self, row):
        """Handle edit action"""
        if self.on_edit:
            self.on_edit(row)
        else:
            self._show_edit_dialog(row)

    async def _handle_delete(self, row):
        """Handle delete action"""
        if self.on_delete:
            await self.on_delete(row)
        else:
            # Confirm deletion
            with ui.dialog() as dialog, ui.card():
                ui.label('Confirm Deletion').classes('text-h6')
                ui.label(f'Delete record with ID {row.get("id")}?')
                with ui.row():
                    ui.button('Cancel', on_click=dialog.close)
                    ui.button(
                        'Delete',
                        on_click=lambda: self._delete_record(row, dialog)
                    ).props('color=negative')
            dialog.open()

    async def _delete_record(self, row, dialog):
        """Delete record using API"""
        try:
            if self.endpoint and row.get('id'):
                await self.api_client.delete(f"{self.endpoint}/{row['id']}")

            # Update local state
            self.records = [r for r in self.records if r.get('id') != row.get('id')]
            self.filtered_records = [r for r in self.filtered_records if r.get('id') != row.get('id')]
            self._render()

            ui.notify('Record deleted successfully', type='positive')
            dialog.close()
        except Exception as e:
            ui.notify(f'Error deleting record: {e}', type='negative')

    def _show_edit_dialog(self, row):
        """Show edit dialog"""
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('Edit Record').classes('text-h6')

            # Create input fields for each property
            inputs = {}
            for key, value in row.items():
                if key != 'actions':
                    inputs[key] = ui.input(
                        key.replace('_', ' ').title(),
                        value=str(value or '')
                    ).classes('w-full')

            with ui.row():
                ui.button('Cancel', on_click=dialog.close)
                ui.button(
                    'Save',
                    on_click=lambda: self._save_edit(row, inputs, dialog)
                ).props('color=primary')

        dialog.open()

    async def _save_edit(self, original_row, inputs, dialog):
        """Save edited record"""
        try:
            # Collect updated values
            updated = {}
            for key, input_field in inputs.items():
                updated[key] = input_field.value

            # Save via API if endpoint exists
            if self.endpoint and original_row.get('id'):
                await self.api_client.put(
                    f"{self.endpoint}/{original_row['id']}",
                    updated
                )

            # Update local state
            for record in self.records:
                if record.get('id') == original_row.get('id'):
                    record.update(updated)

            self.filtered_records = self.records.copy()
            self._render()

            ui.notify('Record updated successfully', type='positive')
            dialog.close()
        except Exception as e:
            ui.notify(f'Error saving record: {e}', type='negative')

    def _show_add_dialog(self):
        """Show add new record dialog"""
        # Implementation similar to edit dialog
        pass

    def _handle_page_size_change(self, e):
        """Handle page size change"""
        self.page_size = e.value
        self.current_page = 1
        self._render()

    def _prev_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self._render()

    def _next_page(self):
        """Go to next page"""
        total_pages = max(1, -(-len(self.filtered_records) // self.page_size))
        if self.current_page < total_pages:
            self.current_page += 1
            self._render()

    def _export_data(self):
        """Export data as CSV"""
        import csv
        import io

        if not self.filtered_records:
            return

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.filtered_records[0].keys())
        writer.writeheader()
        writer.writerows(self.filtered_records)

        ui.download(output.getvalue().encode(), 'export.csv')