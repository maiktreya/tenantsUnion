from typing import Dict, List, Optional, Any
import httpx
from nicegui import ui

class APIClient:
    """PostgREST API client with a more robust singleton pattern."""

    _instance = None
    _initialized = False # Add an initialization flag

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, base_url: str):
        # The __init__ method is called every time you do APIClient(),
        # so we use a flag to ensure it only runs once.
        if self._initialized:
            return
        self.base_url = base_url
        self.client: Optional[httpx.AsyncClient] = None
        self._initialized = True


    def _ensure_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client

    # ... all other methods (get_records, create_record, etc.) remain exactly the same ...
    async def get_records(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict]:
        """Get records with advanced filtering"""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}"
        params = filters or {}

        if order:
            params['order'] = order
        if limit:
            params['limit'] = limit
        if offset:
            params['offset'] = offset

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            ui.notify(f'Error HTTP {e.response.status_code}: {e.response.text}', type='negative')
            return []
        except Exception as e:
            ui.notify(f'Error al obtener registros: {str(e)}', type='negative')
            return []

    async def get_record(self, table: str, record_id: int) -> Optional[Dict]:
        """Get a single record by ID"""
        # This implementation can be slightly optimized
        # records = await self.get_records(table, {'id': f'eq.{record_id}'})
        # return records[0] if records else None
        client = self._ensure_client()
        url = f"{self.base_url}/{table}"
        params = {'id': f'eq.{record_id}'}
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            records = response.json()
            return records[0] if records else None
        except httpx.HTTPStatusError as e:
            ui.notify(f'Error HTTP {e.response.status_code}: {e.response.text}', type='negative')
            return None
        except Exception as e:
            ui.notify(f'Error al obtener registro: {str(e)}', type='negative')
            return None

    async def create_record(self, table: str, data: Dict) -> Optional[Dict]:
        """Create a new record"""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}"
        headers = {"Prefer": "return=representation"}

        try:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result[0] if isinstance(result, list) else result
        except Exception as e:
            ui.notify(f'Error al crear registro: {str(e)}', type='negative')
            return None

    async def update_record(self, table: str, record_id: int, data: Dict) -> Optional[Dict]:
        """Update an existing record"""
        client = self._ensure_client()
        # The primary key column might not always be 'id'.
        # A more robust implementation could fetch this from TABLE_INFO
        # but for now, this is fine.
        url = f"{self.base_url}/{table}?id=eq.{record_id}"
        headers = {"Prefer": "return=representation"}

        try:
            response = await client.patch(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result[0] if isinstance(result, list) else result
        except Exception as e:
            ui.notify(f'Error al actualizar registro: {str(e)}', type='negative')
            return None

    async def delete_record(self, table: str, record_id: int) -> bool:
        """Delete a record"""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}?id=eq.{record_id}"

        try:
            response = await client.delete(url)
            response.raise_for_status()
            return True
        except Exception as e:
            ui.notify(f'Error al eliminar registro: {str(e)}', type='negative')
            return False

    async def close(self):
        """Close the HTTP client"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            self.client = None