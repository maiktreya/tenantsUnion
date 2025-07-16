# nicegui_app.py
import httpx
from nicegui import ui
from contextlib import contextmanager

# --- 1. Core Utilities & Theming (from theme.py, menu.py, api.py) ---
# These are defined first because other parts of the application depend on them.

# From menu.py: Defines the navigation links.
def menu() -> None:
    ui.link("Home", "/").classes(replace="text-black")
    ui.link("Test API", "/api-generator/").classes(replace="text-black")

# From theme.py: Defines the common layout frame used by all pages.
# This is a context manager that sets up the header, footer, and left drawer.
@contextmanager
def frame(navtitle: str):
    """Custom page frame to share the same styling and behavior across all pages"""
    ui.colors(primary='#6E93D6', secondary='#53B689', accent='#111B1E', positive='#53B689')
    # The 'yield' statement is where the specific page content will be inserted.
    with ui.column().classes('absolute-center items-center h-screen no-wrap p-9 w-full'):
        yield
    with ui.header().classes(replace='row items-center') as header:
        ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
        ui.label('Getting Started').classes('font-bold')

    with ui.footer(value=False) as footer:
        ui.label('Footer')
    with ui.left_drawer().classes('bg-blue-100') as left_drawer:
        ui.label('Menu')
        with ui.column():
            menu() # Calls the menu function defined above to add navigation links.
    with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
        ui.button(on_click=footer.toggle, icon='contact_support').props('fab')

# From api.py: Functions for fetching data from an API and preparing it for a UI table.
async def fetch_data(endpoint: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint)
        resp.raise_for_status()
        return resp.json()

def generate_columns(data):
    if not data:
        return []
    return [
        {
            "name": key,
            "label": key.replace("_", " ").capitalize(),
            "field": key,
        }
        for key in data[0].keys()
    ]

async def show_table(endpoint: str):
    """Fetches data and displays it in a NiceGUI table."""
    data = await fetch_data(endpoint)
    columns = generate_columns(data)
    ui.table(
        columns=columns,
        rows=data,
        row_key="id" if data and "id" in data[0] else None,
    )

# --- 2. Page Content Definitions (from home_page.py, table_API.py) ---
# These functions define the specific UI elements for each page.

# From home_page.py: Defines the content for the main homepage.
def home_page_content() -> None:
    with ui.column():
        ui.markdown(
            """
            ### Test de integración

            Aplicación mínima para test app CRUD Restful. 3 servicios docker sin imagenes custom. Fully composable.

            **PostgreSQL (DB) + PostgREST (API) + niceGUI (frontend)**

            Pending:

            1. Implement Nginx reverse server
            2. Interfaz toma de actas
            3. Histórico comflicto
            4. Revisión de tablas


            #### PostgreSQL

            Setup through init-scripts. (2 deps, 1 for testing)

            #### PostgREST

            auto-API endpoints. No deps, just compose.

            #### niceGUI

            Minimalist only python reactive frontend. 1 single script.

            ---

            So at the end. We only need:

            - 1 docker-compose file

            - 1 python script

            - 1 or 2 sql init files

            """

        )
ui.add_body_html('<a href="https://ibb.co/MyMWQzxj"><img src="https://i.ibb.co/mr61gnVY/test-pgerd.png" alt="test-pgerd" border="0"></a>').classes('w-16')

# From table_API.py: Defines the content and interaction logic for the API generator page.
def api_generator_page_content() -> None:
    # Uses the 'frame' context manager to apply the common layout.
    with frame("Testeo de API endpoints y renderizado"):
        endpoint_input = ui.input(
            "API endpoint", value="http://server:3000/usuarios"
        )
        # The button's click event calls the 'show_table' function defined above.
        ui.button(
            "Fetch and Show Table", on_click=lambda: show_table(endpoint_input.value)
        )

# --- 3. Page Route Registrations (from main.py, all_pages.py) ---
# This is where URLs are mapped to the functions that build their content.

# From main.py: Registers the root URL ("/") to display the homepage content.
@ui.page("/")
def index_page() -> None:
    # Uses the 'frame' context manager and then inserts the homepage specific content.
    with frame("Homepage"):
        home_page_content()

# From all_pages.py (which called table_API.py): Registers the "/api-generator/" URL.
# In a single file, we directly link the page to its content function.
ui.page("/api-generator/")(api_generator_page_content)


# --- 4. Application Start (from main.py) ---
# This is the final step that starts the NiceGUI server.
# Changed main guard to support NiceGUI's multiprocessing requirements
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Getting Started with NiceGUI", host="0.0.0.0", port=8081)
