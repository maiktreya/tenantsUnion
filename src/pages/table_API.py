import theme
from nicegui import ui
from modules.api import show_table


def api_generator():
    with theme.frame("Testeo de API endpoints y renderizado"):

        # Sample data: list of dicts
        # UI: Input for endpoint and show table on button click
        endpoint_input = ui.input(
            "API endpoint", value="http://localhost:3001/usuarios"
        )
        ui.button(
            "Fetch and Show Table", on_click=lambda: show_table(endpoint_input.value)
        )
