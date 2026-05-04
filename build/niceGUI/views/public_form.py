from nicegui import ui
from api.client import APIClient
import logging
from pathlib import Path

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

                        data = {k: v.value for k, v in fields.items()}
                        data["afiliacion"] = False

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

                    send_btn.on("click", submit)