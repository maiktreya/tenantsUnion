# build/niceGUI/services/federation_courier.py
import os
from api.client import APIClient
from config import config

SATELLITE_URL = os.environ.get("SATELLITE_URL", "default-secret")

api_singleton = APIClient(config.API_BASE_URL)


async def run_sync_job(satellite_url):
    # 1. Call Api Client
    async with api_singleton as client:
        response = await client.get(f"{satellite_url}/rpc/get_public_companies")
        if response.status_code != 200:
            return

        raw_json = response.json()

    # 2. Handover: Give it to the Brain (PostgreSQL)
    # The DB handles validation, loops, and logic.
    result = await api_singleton.call_rpc(
        "rpc_ingest_federated_data", {"p_payload": raw_json}
    )

    return result
