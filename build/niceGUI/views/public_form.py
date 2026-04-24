from nicegui import ui
from api.client import APIClient
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# Calculamos la ruta absoluta del archivo en el disco duro.
# __file__ es views/public_form.py
# .parent.parent nos lleva a la carpeta raíz 'niceGUI'
LOGO_PATH = Path(__file__).parent.parent / "assets" / "images" / "logo.png"

class PublicJoinForm:
    def __init__(self, api_client: APIClient):
        self.api = api_client

    def setup_public_routes(self):
        """
        Defines the standalone public page.
        This must be called in main.py during the initialization phase.
        """

        @ui.page("/join")
        async def join_page():
            form_container = ui.column().classes("w-full items-center mt-10")

            with form_container:
                with ui.card().classes("shadow-24 p-8 w-96 items-center"):
                    # PASAMOS LA RUTA DEL ARCHIVO FÍSICO (LOGO_PATH)
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
                    
                    async def submit():
                        # Basic frontend validation
                        if not all(
                            [
                                fields["nombre"].value,
                                fields["apellidos"].value,
                                fields["email"].value,
                                fields["cif"].value,
                            ]
                        ):
                            ui.notify(
                                "Por favor, rellena todos los campos obligatorios (*)",
                                type="warning",
                            )
                            return

                        data = {k: v.value for k, v in fields.items()}
                        data["afiliacion"] = False

                        # API Call usando return_representation=False
                        record, error = await self.api.create_record(
                            "afiliadas", 
                            data,
                            return_representation=False
                        )

                        if record:
                            ui.notify("¡Registro completado!", type="positive")
                            form_container.clear()
                            
                            with form_container:
                                with ui.card().classes("shadow-24 p-8 w-96 items-center"):
                                    # USAMOS DE NUEVO LA RUTA DEL ARCHIVO FÍSICO
                                    ui.image(LOGO_PATH).classes("w-48 mb-6")
                                    
                                    ui.label("¡Gracias por registrarte!").classes(
                                        "text-2xl text-red-600 font-bold text-center w-full mb-4"
                                    )
                                    ui.label(
                                        "Esperamos que la reunión de bienvenida empiece a resolver tus dudas. "
                                        "Nos pondremos en contacto contigo pronto."
                                    ).classes("text-lg text-center text-gray-700")
                        else:
                            ui.notify(f"{error}", type="negative")

                    ui.button("Enviar Registro", on_click=submit).classes(
                        "w-full mt-6 bg-red-600 text-white font-bold"
                    )