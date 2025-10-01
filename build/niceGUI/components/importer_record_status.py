"""Helper service to determine duplicate afiliadas and existing pisos."""

from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING

from .importer_normalization import (
    chunk_list,
    format_in_filter_value,
    normalize_address_key,
)

if TYPE_CHECKING:  # pragma: no cover - only for type checkers
    from api.client import APIClient


class ImporterRecordStatusService:
    """Caches remote lookups to flag duplicated afiliadas and pisos."""

    def __init__(self, api_client: "APIClient") -> None:
        self.api = api_client
        self.existing_afiliada_cifs: Dict[str, Optional[bool]] = {}
        self.existing_piso_addresses: Dict[str, Optional[bool]] = {}

    def reset(self) -> None:
        """Clear cached lookups."""
        self.existing_afiliada_cifs.clear()
        self.existing_piso_addresses.clear()

    async def preload_afiliada_cifs(self, records: List[Dict]) -> Dict[str, Optional[bool]]:
        """Fetch duplicate status for CIF values found in the provided records."""
        cifs = sorted(
            {
                str(record.get("afiliada", {}).get("cif", "")).strip().upper()
                for record in records
                if record.get("afiliada", {}).get("cif")
            }
        )

        if not cifs:
            self.existing_afiliada_cifs.clear()
            return {}

        self.existing_afiliada_cifs = {cif: False for cif in cifs}

        for chunk in chunk_list(cifs):
            filter_value = ",".join(chunk)
            try:
                matches = await self.api.get_records(
                    "afiliadas", {"cif": f"in.({filter_value})"}
                )
            except Exception:
                matches = []

            for item in matches or []:
                cif_value = str(item.get("cif", "")).strip().upper()
                if cif_value:
                    self.existing_afiliada_cifs[cif_value] = True

        return dict(self.existing_afiliada_cifs)

    async def preload_piso_addresses(self, records: List[Dict]) -> Dict[str, Optional[bool]]:
        """Fetch existence status for piso addresses within the provided records."""
        address_map: Dict[str, str] = {}
        for record in records:
            direccion = (record.get("piso", {}).get("direccion") or "").strip()
            if not direccion:
                continue
            key = normalize_address_key(direccion)
            if key and key not in address_map:
                address_map[key] = direccion

        if not address_map:
            self.existing_piso_addresses.clear()
            return {}

        self.existing_piso_addresses = {key: False for key in address_map}

        address_values = list(address_map.values())
        for chunk in chunk_list(address_values):
            filter_value = ",".join(format_in_filter_value(val) for val in chunk)
            try:
                matches = await self.api.get_records(
                    "pisos", {"direccion": f"in.({filter_value})"}
                )
            except Exception:
                matches = []

            for item in matches or []:
                key = normalize_address_key(item.get("direccion"))
                if key:
                    self.existing_piso_addresses[key] = True

        return dict(self.existing_piso_addresses)

    async def ensure_afiliada_status(self, cif: str) -> bool:
        """Return whether a CIF already exists, performing a remote lookup if needed."""
        cif = (cif or "").strip().upper()
        if not cif:
            return False

        cached = self.existing_afiliada_cifs.get(cif)
        if cached is None:
            try:
                matches = await self.api.get_records("afiliadas", {"cif": f"eq.{cif}"})
                cached = bool(matches)
            except Exception:
                cached = False
            self.existing_afiliada_cifs[cif] = cached

        return bool(cached)

    async def ensure_piso_status(self, direccion: str) -> bool:
        """Return whether a piso address already exists, fetching it if unknown."""
        direccion = (direccion or "").strip()
        if not direccion:
            return False

        key = normalize_address_key(direccion)
        cached = self.existing_piso_addresses.get(key)
        if cached is None:
            try:
                matches = await self.api.get_records(
                    "pisos", {"direccion": f"eq.{direccion}"}
                )
                cached = bool(matches)
            except Exception:
                cached = False
            self.existing_piso_addresses[key] = cached

        return bool(cached)

    def mark_unknown_cif(self, cif: str) -> None:
        """Track a CIF that may require fetching in the future."""
        cif = (cif or "").strip().upper()
        if cif and cif not in self.existing_afiliada_cifs:
            self.existing_afiliada_cifs[cif] = None

    def mark_unknown_address(self, direccion: str) -> None:
        """Track a piso address that may require fetching in the future."""
        direccion = (direccion or "").strip()
        if not direccion:
            return
        key = normalize_address_key(direccion)
        if key and key not in self.existing_piso_addresses:
            self.existing_piso_addresses[key] = None


__all__ = ["ImporterRecordStatusService"]
