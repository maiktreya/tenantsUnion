from nicegui import ui
from api.client import APIClient
import logging
from pathlib import Path
import re
from datetime import date

log = logging.getLogger(__name__)

LOGO_PATH = Path(__file__).parent.parent / "assets" / "images" / "logo.png"

class PublicJoinForm:
    def __init__(self, api_client: APIClient):
        self.api = api_client

    def setup_public_routes(self):
        @ui.page("/join")
        async def join_page():
            form_container = ui.column().classes("w-full items-center mt-10")

            with form_container:
                with ui.card().classes("shadow-24 p-8 w-96 items-center"):
                    ui.image(LOGO_PATH).classes("w-48 mb-4")
                    
                    ui.label("Formulario de Inscripción").classes(
                        "text-2xl mb-4 text-red-600 font-bold text-center w-full"
                    )

                    fields = {
                        "nombre": ui.input("Nombre *").classes("w-full"),
                        "apellidos": ui.input("Apellidos *").classes("w-full"),
                        "email": ui.input("Mail *").classes("w-full"),
                        "telefono": ui.input("Teléfono").classes("w-full"),
                        "cif": ui.input("DNI / CIF / NIE *").classes("w-full"),
                    }

                    # Privacy checkbox row
                    with ui.row().classes("w-full items-center mt-4 gap-2"):
                        privacy_check = ui.checkbox()
                        ui.html(
                            'Acepto los '
                            '<a href="https://inquilinato.org/politica-privacidad/" '
                            'target="_blank" '
                            'style="color: #dc2626; text-decoration: underline;">'
                            'términos de privacidad</a>',
                            sanitize=False  # needed to allow the <a> tag through
                        )

                    # Send button — disabled by default
                    send_btn = ui.button("Enviar Registro").classes(
                        "w-full mt-4 bg-red-600 text-white font-bold"
                    )

                    # Toggle button state when checkbox changes
                    def on_privacy_change():
                        send_btn.enabled = privacy_check.value

                    privacy_check.on("update:model-value", lambda _: on_privacy_change())
                    send_btn.enabled = False  # start greyed out

                    async def submit():
                        if not all([
                            fields["nombre"].value,
                            fields["apellidos"].value,
                            fields["email"].value,
                            fields["cif"].value,
                        ]):
                            ui.notify(
                                "Por favor, rellena todos los campos obligatorios (*)",
                                type="warning",
                            )
                            return
                        
                        # 1. Data Sanitization 
                        # .strip() naturally removes both leading and trailing whitespaces.
                        # re.sub() removes internal duplicate spaces.
                        clean_cif = re.sub(r'\s+', '', fields["cif"].value).strip().upper()
                        clean_nombre = re.sub(r'\s+', ' ', fields["nombre"].value).strip().title()
                        clean_apellidos = re.sub(r'\s+', ' ', fields["apellidos"].value).strip().title()
                        clean_email = re.sub(r'\s+', '', fields["email"].value).strip().lower()
                        
                        telefono_val = fields["telefono"].value
                        clean_telefono = re.sub(r'\s+', '', telefono_val).strip() if telefono_val else None

                        # Prepare the payload with the target values
                        data = {
                            "nombre": clean_nombre,
                            "apellidos": clean_apellidos,
                            "email": clean_email,
                            "cif": clean_cif,
                            "telefono": clean_telefono,
                            "afiliacion": "true",
                            "estado": "Bienvenida",
                            "fecha_alta": date.today().isoformat()
                        }

                        # 2. Application-Level Upsert Logic
                        # First, check if the pre-afiliada already exists by CIF
                        existing_records = await self.api.get_records(
                            "afiliadas", 
                            filters={"cif": f"eq.{clean_cif}"}
                        )

                        success = False
                        
                        if existing_records:
                            # They exist! UPDATE the record (transform 'Importado' -> 'TRUE')
                            existing_id = existing_records[0]["id"]
                            updated_record = await self.api.update_record(
                                "afiliadas", 
                                existing_id, 
                                data
                            )
                            if updated_record:
                                success = True
                            else:
                                ui.notify("Error al actualizar los datos existentes.", type="negative")
                        else:
                            # They don't exist, INSERT as a brand new record
                            created_record, error = await self.api.create_record(
                                "afiliadas",
                                data,
                                return_representation=False
                            )
                            if created_record:
                                success = True
                            else:
                                ui.notify(f"{error}", type="negative")

                        # 3. Success UI Update
                        if success:
                            ui.notify("¡Registro procesado con éxito!", type="positive")
                            form_container.clear()
                            
                            with form_container:
                                with ui.card().classes("shadow-24 p-8 w-96 items-center"):
                                    ui.image(LOGO_PATH).classes("w-48 mb-6")
                                    ui.label("¡Gracias por registrarte!").classes(
                                        "text-2xl text-red-600 font-bold text-center w-full mb-4"
                                    )
                                    ui.label(
                                        "Esperamos que la reunión de bienvenida empiece a resolver tus dudas. "
                                        "Nos pondremos en contacto contigo pronto."
                                    ).classes("text-lg text-center text-gray-700")

                    send_btn.on("click", submit)