from nicegui import ui


def content() -> None:
    with ui.column():
        ui.markdown(
            """

            # Test de integración
            ## PostgreSQL
            ## PostgREST
            ## niceGUI

            """
        )
