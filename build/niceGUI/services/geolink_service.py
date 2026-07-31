# build/niceGUI/services/geolink_service.py
"""
Async, in-process port of the address -> (ref_catastral, lat, lng) lookup used
by the offline ETL pipeline. See `ETL/02-geolink.py::get_cadastral_data` for
the canonical, batch-oriented implementation this mirrors.

WHY THIS DUPLICATES LOGIC INSTEAD OF IMPORTING IT
--------------------------------------------------
`ETL/02-geolink.py` is invoked directly on the host by `utils/cron/daily_sync.sh`
(`python3 "$GEOLINK_SCRIPT_PATH" ...`). It is NOT part of the `nicegui-app`
Docker image: the container's build context is `./build/niceGUI` only (see
`docker-compose.yaml` and `build/niceGUI/Dockerfile`), so `ETL/` is not on
disk inside the running app and cannot be imported here.

WHY THIS IS async/httpx INSTEAD OF sync/requests
--------------------------------------------------
The ETL script is a one-shot batch job, so its blocking `requests.get(...)`
and `time.sleep(...)` calls are harmless there. This module runs inside
NiceGUI's single-threaded async event loop instead, where a blocking call
would freeze the UI for every connected user for the duration of each
CartoCiudad request. Everything here is therefore rewritten around
`httpx.AsyncClient` and `asyncio.sleep`.

If CartoCiudad's response shape or the matching/retry rules ever change,
update BOTH this file and `ETL/02-geolink.py`. If that duplication becomes
painful, the cleanest long-term fix is extracting a single shared module and
mounting it read-only into both the cron host path and the `nicegui-app`
container (an extra volume in `docker-compose.yaml`), rather than keeping two
copies in sync by hand.
"""

import asyncio
import logging
from typing import Optional, Tuple

import httpx

log = logging.getLogger(__name__)

API_URL = "https://www.cartociudad.es/geocoder/api/geocoder/candidates"
API_TIMEOUT = 10.0

# Courtesy delay between requests, matching ETL/02-geolink.py's RATE_LIMIT_SLEEP.
# Callers should `await asyncio.sleep(RATE_LIMIT_SLEEP)` between successive
# calls to this function when processing a batch of addresses.
RATE_LIMIT_SLEEP = 0.2

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.5


async def lookup_cadastral_data(
    address: str, municipality: Optional[str] = "Madrid"
) -> Tuple[Optional[str], Optional[float], Optional[float]]:
    """
    Queries CartoCiudad for a single address.

    Returns a (ref_catastral, lat, lng) tuple. Any element may be `None` if
    CartoCiudad didn't return that piece of data (or found no candidate at
    all) — callers should only write back the fields that came back non-None,
    so an unsuccessful lookup never overwrites existing data with blanks.

    Mirrors the retry/backoff behaviour of
    `ETL/02-geolink.py::get_cadastral_data`, minus the CSV/floor/door
    post-processing steps, which aren't relevant to enriching a single
    already-stored `pisos` row.
    """
    if not address or len(address.strip()) < 5:
        return None, None, None

    params = {"q": address.strip(), "limit": 1}
    if municipality:
        params["municipio_filter"] = str(municipality).strip()

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.get(API_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if not data or not isinstance(data, list):
                    return None, None, None

                best = data[0]
                ref_catastral = (best.get("refCatastral") or "").strip() or None

                lat_raw, lng_raw = best.get("lat"), best.get("lng")
                try:
                    lat = float(lat_raw) if lat_raw not in (None, "") else None
                    lng = float(lng_raw) if lng_raw not in (None, "") else None
                except (TypeError, ValueError):
                    lat, lng = None, None

                return ref_catastral, lat, lng

            except Exception as ex:
                if attempt == MAX_RETRIES:
                    log.warning(
                        "CartoCiudad lookup permanently failed for '%s': %s",
                        address,
                        ex,
                    )
                else:
                    await asyncio.sleep(RETRY_BACKOFF_BASE * attempt)

    return None, None, None


def to_ewkt_point(lat: float, lng: float) -> str:
    """
    Formats a (lat, lng) pair as EWKT text that PostgREST/PostGIS will accept
    for a PATCH against a `geometry(Point, 4326)` column — PostGIS registers
    an implicit text->geometry cast, so this can go straight into a JSON
    payload as a plain string value.

    Note the coordinate order: PostGIS POINT(x y) is (longitude, latitude),
    matching the `ST_MakePoint(lng, lat)` call already used in
    `ETL/03-load-from-csv.sql` for the batch-loaded path.
    """
    return f"SRID=4326;POINT({lng} {lat})"