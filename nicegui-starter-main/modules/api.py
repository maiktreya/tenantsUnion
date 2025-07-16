import httpx
from nicegui import ui


# Fetch data from a dynamic endpoint
async def fetch_data(endpoint: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint)
        resp.raise_for_status()
        return resp.json()  # Expecting a list of dicts


# Dynamically generate columns based on data keys
def generate_columns(data):
    if not data:
        return []
    # Use the keys of the first dict as columns
    return [
        {
            "name": key,
            "label": key.replace("_", " ").capitalize(),
            "field": key,
        }
        for key in data[0].keys()
    ]


# Example usage in NiceGUI
async def show_table(endpoint: str):
    data = await fetch_data(endpoint)
    columns = generate_columns(data)
    ui.table(
        columns=columns,
        rows=data,
        row_key="id" if data and "id" in data[0] else None,
    )
