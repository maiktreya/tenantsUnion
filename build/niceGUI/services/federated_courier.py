# build/niceGUI/services/federation_courier.py
import httpx
from api.client import api_singleton


async def run_sync_job(satellite_url, credentials):
    async with httpx.AsyncClient() as client:
        # 1. Transport: Get the raw data
        # (Assuming you handle auth here briefly)
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
