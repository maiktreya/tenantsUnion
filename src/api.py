import asyncio
import httpx
from nicegui import ui

POSTGREST_URL = "http://localhost:3000/app_userd"

# Define columns for the table
columns = [
    {"name": "name", "label": "Name", "field": "name"},
    {"name": "age", "label": "Age", "field": "age"},
    {
        "name": "role",
        "label": "Role",
        "field": "role",
        "headerTooltip": "The user's job function in the company",
    },
]


async def fetch_users():
    async with httpx.AsyncClient() as client:
        # Adjust if your endpoint or expected query is different!
        resp = await client.get(POSTGREST_URL)
        resp.raise_for_status()
        return resp.json()  # Should return a list of dicts
