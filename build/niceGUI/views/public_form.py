from nicegui import ui
from api.client import APIClient
import logging

log = logging.getLogger(__name__)

class PublicJoinForm:
    def __init__(self, api_client: APIClient):
        self.api = api_client

    def setup_public_routes(self):
        """
        Defines the standalone public page. 
        This must be called in main.py during the initialization phase.
        """
        
        @ui.page('/join')
        async def join_page():
            # Define the container first so it exists in the scope for the submit function
            form_container = ui.column().classes('w-full items-center')
            
            with form_container:
                with ui.card().classes('shadow-24 p-8 w-96 mt-10'):
                    ui.label('Formulario de Inscripción').classes('text-2xl mb-4 text-red-600 font-bold')
                    
                    # Store inputs in a dict for easier access
                    fields = {
                        "nombre": ui.input('Nombre').classes('w-full'),
                        "apellidos": ui.input('Apellidos').classes('w-full'),
                        "email": ui.input('Mail').classes('w-full'),
                        "telefono": ui.input('Teléfono').classes('w-full'),
                        "cif": ui.input('DNI (CIF)').classes('w-full'),
                    }
                    afiliacion = ui.checkbox('Deseo afiliarme ahora')

                    async def submit():
                        # Collect values
                        data = {k: v.value for k, v in fields.items()}
                        data["afiliacion"] = afiliacion.value
                        data["estado"] = "Alta" if afiliacion.value else "Pre-alta"

                        # API Call using the centralized client
                        success, error = await self.api.create_record("afiliadas", data)
                        
                        if success:
                            ui.notify('¡Registro completado!', type='positive')
                            form_container.clear() # Now form_container is correctly referenced
                            with form_container:
                                ui.label('Gracias. Nos pondremos en contacto pronto.').classes('text-xl mt-10')
                        else:
                            ui.notify(f'Error: {error}', type='negative')

                    ui.button('Enviar Registro', on_click=submit).classes('w-full mt-4 bg-red-600 text-white')