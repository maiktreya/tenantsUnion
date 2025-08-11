from typing import Dict, Optional, Callable
from nicegui import ui
from api.client import APIClient

class RecordDialog:
    """Dialog for creating/editing records"""

    def __init__(
        self,
        api: APIClient,
        table: str,
        record: Optional[Dict] = None,
        mode: str = 'create',
        on_success: Optional[Callable] = None
    ):
        self.api = api
        self.table = table
        self.record = record or {}
        self.mode = mode
        self.on_success = on_success
        self.dialog = None
        self.inputs = {}

    def open(self):
        """Open the dialog"""
        self.dialog = ui.dialog()

        with self.dialog, ui.card().classes('w-96'):
            # Title
            title = (
                f'Crear nuevo registro en {self.table}'
                if self.mode == 'create'
                else f'Editar registro #{self.record.get("id")} de {self.table}'
            )
            ui.label(title).classes('text-h6')

            # Create input fields
            self._create_inputs()

            # Action buttons
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancelar', on_click=self.dialog.close).props('flat')
                ui.button(
                    'Guardar',
                    on_click=lambda: ui.timer(0.1, self._save, once=True)
                ).props('color=orange-600')

        self.dialog.open()

    def _create_inputs(self):
        """Create input fields based on record structure"""
        # Get fields from existing record or sample
        if self.mode == 'edit':
            fields = {k: v for k, v in self.record.items() if k != 'id'}
        else:
            # For create mode, we need to determine fields
            # This is a simplified version - in production, you'd want schema info
            fields = self._get_table_fields()

        for field_name, field_value in fields.items():
            value = str(field_value) if field_value is not None else ''
            self.inputs[field_name] = ui.input(
                field_name,
                value=value if self.mode == 'edit' else ''
            ).classes('w-full')

    def _get_table_fields(self) -> Dict:
        """Get fields for the table (simplified version)"""
        # In a real application, you'd fetch this from schema or metadata
        # For now, return common fields based on table name
        common_fields = {
            'nombre': '',
            'descripcion': '',
            'estado': '',
            'fecha': '',
        }

        # Add table-specific fields
        table_fields = {
            'empresas': {'nombre': '', 'tipo': '', 'direccion': ''},
            'usuarios': {'nombre': '', 'email': '', 'rol': ''},
            'conflictos': {'descripcion': '', 'estado': '', 'causa': '', 'ambito': ''},
            'facturacion': {'monto': '', 'fecha': '', 'concepto': ''},
        }

        return table_fields.get(self.table, common_fields)

    async def _save(self):
        """Save the record"""
        try:
            # Collect data from inputs
            data = {
                field: self.inputs[field].value
                for field in self.inputs
                if self.inputs[field].value
            }

            if self.mode == 'create':
                result = await self.api.create_record(self.table, data)
                if result:
                    ui.notify('Registro creado con éxito', type='positive')
                    self.dialog.close()
                    if self.on_success:
                        await self.on_success()
            else:
                # Only update changed fields
                changed_data = {
                    field: value
                    for field, value in data.items()
                    if str(value) != str(self.record.get(field, ''))
                }

                if changed_data:
                    result = await self.api.update_record(
                        self.table,
                        self.record['id'],
                        changed_data
                    )
                    if result:
                        ui.notify('Registro actualizado con éxito', type='positive')
                        self.dialog.close()
                        if self.on_success:
                            await self.on_success()
                else:
                    ui.notify('No se realizaron cambios', type='info')

        except Exception as e:
            ui.notify(f'Error al guardar: {str(e)}', type='negative')


class ConflictNoteDialog:
    """Dialog for adding notes to conflicts"""

    def __init__(
        self,
        api: APIClient,
        conflict: Dict,
        on_success: Optional[Callable] = None
    ):
        self.api = api
        self.conflict = conflict
        self.on_success = on_success
        self.dialog = None

    def open(self):
        """Open the dialog"""
        from datetime import datetime

        self.dialog = ui.dialog()

        with self.dialog, ui.card().classes('w-96'):
            ui.label(f'Añadir Nota al Conflicto #{self.conflict["id"]}').classes('text-h6')

            # Input fields
            estado_input = ui.select(
                options=['Abierto', 'En proceso', 'Resuelto', 'Cerrado'],
                label='Estado',
                value=self.conflict.get('estado', '')
            ).classes('w-full')

            ambito_input = ui.input(
                'Ámbito',
                value=self.conflict.get('ambito', '')
            ).classes('w-full')

            afectada_input = ui.input('Afectada').classes('w-full')

            causa_input = ui.textarea('Causa/Notas').classes('w-full')

            # Action buttons
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancelar', on_click=self.dialog.close).props('flat')

                async def save_note():
                    try:
                        # Create note entry
                        note_data = {
                            'conflicto_id': self.conflict['id'],
                            'estado': estado_input.value or None,
                            'ambito': ambito_input.value or None,
                            'afectada': afectada_input.value or None,
                            'causa': causa_input.value or None,
                            'created_at': datetime.now().isoformat()
                        }

                        # Remove None values
                        note_data = {k: v for k, v in note_data.items() if v is not None}

                        # Save to diario_conflictos
                        result = await self.api.create_record('diario_conflictos', note_data)

                        if result:
                            # Update conflict status if changed
                            if estado_input.value and estado_input.value != self.conflict.get('estado'):
                                await self.api.update_record(
                                    'conflictos',
                                    self.conflict['id'],
                                    {'estado': estado_input.value}
                                )

                            ui.notify('Nota añadida con éxito', type='positive')
                            self.dialog.close()

                            if self.on_success:
                                await self.on_success()

                    except Exception as e:
                        ui.notify(f'Error al añadir la nota: {str(e)}', type='negative')

                ui.button(
                    'Guardar',
                    on_click=lambda: ui.timer(0.1, save_note, once=True)
                ).props('color=orange-600')

        self.dialog.open()