# /build/niceGUI/api/client.py

from typing import Dict, List, Optional, Any, Type, TypeVar
import httpx
from nicegui import ui
from pydantic import BaseModel, ValidationError

# Import the new Pydantic models
from models import schemas

# Generic TypeVar for Pydantic models to improve type hinting
T = TypeVar("T", bound=BaseModel)

class APIClient:
    """
    PostgREST API client with a hybrid approach:
    1. Generic methods for dynamic, table-based operations (e.g., Admin view).
    2. Type-safe methods using Pydantic models for robust, specific operations.
    """

    _instance = None

    def __new__(cls, base_url: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.base_url = base_url
            cls._instance.client = None
        return cls._instance

    def _ensure_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client

    # =====================================================================
    #  PRIVATE HELPER FOR PARSING RESPONSES
    # =====================================================================

    def _parse_response(self, model: Type[T], response_data: Any) -> Optional[List[T]]:
        """Safely parses API response data into a list of Pydantic models."""
        if not response_data:
            return []
        try:
            if isinstance(response_data, list):
                return [model.model_validate(item) for item in response_data]
            return [model.model_validate(response_data)]
        except ValidationError as e:
            ui.notify(f"Error de validación de datos: {e}", type='negative')
            print(f"Pydantic Validation Error: {e}")
            return None

    # =====================================================================
    #  LOW-LEVEL GENERIC METHODS (UNCHANGED)
    #  Used by dynamic components like the Admin BBDD view
    # =====================================================================

    async def get_records(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict]:
        """Get records as dictionaries (unvalidated)."""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}"
        params = filters or {}

        if order: params['order'] = order
        if limit: params['limit'] = limit
        if offset: params['offset'] = offset

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

    async def create_record(self, table: str, data: Dict) -> Optional[Dict]:
        """Create a new record from a dictionary (unvalidated)."""
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

    async def update_record(self, table: str, record_id: Any, data: Dict) -> Optional[Dict]:
        """Update a record from a dictionary (unvalidated)."""
        client = self._ensure_client()
        # Handle composite keys or different primary key names
        pk_filter = f"id=eq.{record_id}"
        if table == 'usuario_credenciales': pk_filter = f"usuario_id=eq.{record_id}"
        elif table == 'nodos_cp_mapping': pk_filter = f"cp=eq.{record_id}"

        url = f"{self.base_url}/{table}?{pk_filter}"
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
        """Delete a record by ID."""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}?id=eq.{record_id}"
        try:
            response = await client.delete(url)
            response.raise_for_status()
            return True
        except Exception as e:
            ui.notify(f'Error al eliminar registro: {str(e)}', type='negative')
            return False

    # =====================================================================
    #  HIGH-LEVEL TYPE-SAFE METHODS
    #  Use these in application logic for robust, validated operations
    # =====================================================================

    async def get_afiliadas_typed(self, filters: Optional[Dict] = None) -> List[schemas.Afiliada]:
        """Gets a list of 'afiliadas' and validates them against the Pydantic model."""
        records = await self.get_records("afiliadas", filters=filters)
        validated_records = self._parse_response(schemas.Afiliada, records)
        return validated_records or []

    async def get_afiliada_by_id_typed(self, afiliada_id: int) -> Optional[schemas.Afiliada]:
        """Gets a single 'afiliada' by ID, fully validated."""
        records = await self.get_records("afiliadas", filters={'id': f'eq.{afiliada_id}'})
        validated_records = self._parse_response(schemas.Afiliada, records)
        return validated_records[0] if validated_records else None

    async def create_afiliada_typed(self, data: schemas.AfiliadaCreate) -> Optional[schemas.Afiliada]:
        """Creates an 'afiliada' using a validated Pydantic model."""
        # .model_dump() converts the Pydantic model to a dict for JSON serialization
        response_data = await self.create_record("afiliadas", data.model_dump())
        validated_response = self._parse_response(schemas.Afiliada, response_data)
        return validated_response[0] if validated_response else None

    async def update_afiliada_typed(self, afiliada_id: int, data: schemas.AfiliadaUpdate) -> Optional[schemas.Afiliada]:
        """Updates an 'afiliada' using a validated Pydantic model."""
        # exclude_unset=True ensures we only send fields that were actually provided
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            ui.notify("No changes to update.", type='info')
            return await self.get_afiliada_by_id_typed(afiliada_id) # Return current state
        
        response_data = await self.update_record("afiliadas", afiliada_id, update_data)
        validated_response = self._parse_response(schemas.Afiliada, response_data)
        return validated_response[0] if validated_response else None
        
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
