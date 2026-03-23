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

        @ui.page("/join")
        async def join_page():
            form_container = ui.column().classes("w-full items-center mt-10")

            with form_container:
                with ui.card().classes("shadow-24 p-8 w-96"):
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

                        # Collect values directly matching the DB schema
                        data = {k: v.value for k, v in fields.items()}

                        # Hardcode afiliacion to False since this is a public pre-registration
                        data["afiliacion"] = False

                        # API Call using the centralized client
                        # If the CIF already exists, this will cleanly fail and return the duplicate error
                        record, error = await self.api.create_record("afiliadas", data)

                        if record:
                            ui.notify("¡Registro completado!", type="positive")
                            form_container.clear()
                            with form_container:
                                ui.label(
                                    "Gracias. Nos pondremos en contacto pronto."
                                ).classes("text-xl mt-10 text-center")
                        else:
                            # This will display your existing duplicate CIF error from client.py
                            ui.notify(f"{error}", type="negative")

                    ui.button("Enviar Registro", on_click=submit).classes(
                        "w-full mt-6 bg-red-600 text-white font-bold"
                    )
