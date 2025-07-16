import httpx
from nicegui import ui

# Update this to the correct PostgREST endpoint
POSTGREST_URL = "http://localhost:3000/usuarios"

# Define the columns for display (adapted from your schema)
columns = [
    {"name": "id", "label": "ID", "field": "id"},
    {"name": "alias", "label": "Alias", "field": "alias"},
    {"name": "nombre", "label": "First Name", "field": "nombre"},
    {"name": "apellidos", "label": "Last Name", "field": "apellidos"},
    {"name": "email", "label": "Email", "field": "email"},
    {
        "name": "grupo_por_defecto",
        "label": "Default Group",
        "field": "grupo_por_defecto",
    },
]


async def fetch_usuarios():
    async with httpx.AsyncClient() as client:
        resp = await client.get(POSTGREST_URL)
        resp.raise_for_status()
        return resp.json()


table = ui.table(
    columns=columns,
    rows=[],
    row_key="id",
).classes("w-full")


@ui.page("/")
async def main():
    usuarios = await fetch_usuarios()
    table.rows = usuarios


ui.run()
