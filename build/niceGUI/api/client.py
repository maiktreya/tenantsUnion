import httpx
import logging  # <-- CHANGE: Import the logging module
from typing import Dict, List, Optional, Any, Tuple
from nicegui import ui
from api.validate import validator

log = logging.getLogger(__name__)  # <-- CHANGE: Get a logger for this module


class APIClient:
    """
    Enhanced PostgREST API client with config-driven validation.
    Uses TABLE_INFO from config.py as the single source of truth.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client: Optional[httpx.AsyncClient] = None

    def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure the HTTP client is initialized."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client

    # =====================================================================
    #  CORE CRUD OPERATIONS WITH CONFIG-DRIVEN VALIDATION
    # =====================================================================

    async def get_records(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        validate_response: bool = False,
    ) -> List[Dict]:
        """Get records as dictionaries with optional response validation."""
        client = self._ensure_client()
        url = f"{self.base_url}/{table}"
        params = filters or {}

        if order:
            params["order"] = order
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            records = response.json()

            if validate_response and isinstance(records, list):
                validated_records = []
                for record in records:
                    is_valid, errors = validator.validate_record(table, record, "read")
                    if is_valid:
                        validated_records.append(record)
                    else:
                        ui.notify(
                            f'Invalid record in {table}: {"; ".join(errors)}',
                            type="warning",
                        )
                return validated_records

            return records
        except httpx.HTTPStatusError as e:
            # <-- CHANGE: Added detailed logging -->
            log.error(
                f"HTTP Error getting records from '{table}': Status {e.response.status_code}",
                exc_info=True,
            )
            ui.notify(
                f"Error HTTP {e.response.status_code}: {e.response.text}",
                type="negative",
            )
            return []
        except Exception as e:
            # <-- CHANGE: Added detailed logging -->
            log.error(f"Unexpected error getting records from '{table}'", exc_info=True)
            ui.notify(f"Error al obtener registros: {str(e)}", type="negative")
            return []

    async def create_record(
        self,
        table: str,
        data: Dict,
        validate: bool = True,
        show_validation_errors: bool = True,
    ) -> Optional[Dict]:
        """Create a new record from a dictionary with optional validation."""
        if validate:
            is_valid, errors = validator.validate_record(table, data, "create")
            if not is_valid:
                if show_validation_errors:
                    ui.notify(
                        f'Validation errors: {"; ".join(errors)}', type="negative"
                    )
                return None

        client = self._ensure_client()
        url = f"{self.base_url}/{table}"
        headers = {"Prefer": "return=representation"}

        try:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            created_record = result[0] if isinstance(result, list) else result

            if validate:
                is_valid, errors = validator.validate_record(
                    table, created_record, "read"
                )
                if not is_valid and show_validation_errors:
                    ui.notify(
                        f'Warning - Created record has validation issues: {"; ".join(errors)}',
                        type="warning",
                    )

            return created_record
        except Exception as e:
            # <-- CHANGE: Added detailed logging -->
            log.error(
                f"Error creating record in '{table}' with data: {data}", exc_info=True
            )
            ui.notify(f"Error al crear registro: {str(e)}", type="negative")
            return None

    async def update_record(
        self,
        table: str,
        record_id: Any,
        data: Dict,
        validate: bool = True,
        show_validation_errors: bool = True,
    ) -> Optional[Dict]:
        """Update a record from a dictionary with optional validation."""
        if validate:
            is_valid, errors = validator.validate_record(table, data, "update")
            if not is_valid:
                if show_validation_errors:
                    ui.notify(
                        f'Validation errors: {"; ".join(errors)}', type="negative"
                    )
                return None

        client = self._ensure_client()
        pk_filter = f"id=eq.{record_id}"
        if table == "usuario_credenciales":
            pk_filter = f"usuario_id=eq.{record_id}"
        elif table == "nodos_cp_mapping":
            pk_filter = f"cp=eq.{record_id}"

        url = f"{self.base_url}/{table}?{pk_filter}"
        headers = {"Prefer": "return=representation"}

        try:
            response = await client.patch(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            updated_record = result[0] if isinstance(result, list) else result

            if validate:
                is_valid, errors = validator.validate_record(
                    table, updated_record, "read"
                )
                if not is_valid and show_validation_errors:
                    ui.notify(
                        f'Warning - Updated record has validation issues: {"; ".join(errors)}',
                        type="warning",
                    )

            return updated_record
        except Exception as e:
            # <-- CHANGE: Added detailed logging -->
            log.error(
                f"Error updating record ID '{record_id}' in '{table}' with data: {data}",
                exc_info=True,
            )
            ui.notify(f"Error al actualizar registro: {str(e)}", type="negative")
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
            # <-- CHANGE: Added detailed logging -->
            log.error(
                f"Error deleting record ID '{record_id}' from '{table}'", exc_info=True
            )
            ui.notify(f"Error al eliminar registro: {str(e)}", type="negative")
            return False

    # =====================================================================
    #  ENHANCED UTILITY METHODS (No changes needed here)
    # =====================================================================

    async def get_record_by_id(
        self, table: str, record_id: Any, validate: bool = False
    ) -> Optional[Dict]:
        """Get a single record by ID with optional validation."""
        records = await self.get_records(
            table, filters={"id": f"eq.{record_id}"}, validate_response=validate
        )
        return records[0] if records else None

    async def batch_create(
        self,
        table: str,
        records: List[Dict],
        validate: bool = True,
        stop_on_error: bool = False,
    ) -> Tuple[List[Dict], List[str]]:
        """Create multiple records with optional validation and error handling."""
        created = []
        errors = []

        for i, record in enumerate(records):
            result = await self.create_record(
                table, record, validate=validate, show_validation_errors=False
            )

            if result:
                created.append(result)
            else:
                error_msg = f"Failed to create record {i+1}"
                errors.append(error_msg)
                if stop_on_error:
                    break

        return created, errors

    async def validate_record_data(
        self, table: str, data: Dict, operation: str = "create"
    ) -> Tuple[bool, List[str]]:
        """Explicitly validate record data without performing any database operations."""
        return validator.validate_record(table, data, operation)

    def get_table_schema(self, table: str) -> Optional[Dict]:
        """Get table configuration from TABLE_INFO."""
        from config import TABLE_INFO

        return TABLE_INFO.get(table)

    def get_field_constraints(self, table: str, field: str) -> Dict[str, Any]:
        """Get validation constraints for a specific field."""
        return validator.get_field_constraints(table, field)

    def get_table_display_fields(self, table: str, record: Dict) -> Dict[str, Any]:
        """Get only the fields that should be displayed in the UI."""
        schema = self.get_table_schema(table)
        if not schema:
            return record

        hidden_fields = set(schema.get("hidden_fields", []))
        return {k: v for k, v in record.items() if k not in hidden_fields}

    async def search_records(
        self, table: str, search_term: str, search_fields: Optional[List[str]] = None
    ) -> List[Dict]:
        """Search records across specified fields using PostgREST text search."""
        schema = self.get_table_schema(table)
        if not schema:
            return []

        if not search_fields:
            all_fields = schema.get("fields", [])
            hidden_fields = set(schema.get("hidden_fields", []))
            search_fields = [
                f
                for f in all_fields
                if f not in hidden_fields and not f.endswith("_id")
            ]

        or_conditions = ",".join(
            [f"{field}.ilike.*{search_term}*" for field in search_fields]
        )
        filters = {"or": f"({or_conditions})"}

        return await self.get_records(table, filters=filters)

    # =====================================================================
    #  RELATIONSHIP HELPERS (No changes needed here)
    # =====================================================================

    async def get_related_records(
        self, table: str, record_id: Any, relation_table: str
    ) -> List[Dict]:
        """Get records related to a parent record."""
        schema = self.get_table_schema(table)
        if not schema:
            return []

        child_relations = schema.get("child_relations", [])
        relation_config = next(
            (rel for rel in child_relations if rel["table"] == relation_table), None
        )

        if not relation_config:
            return []

        foreign_key = relation_config["foreign_key"]
        filters = {foreign_key: f"eq.{record_id}"}

        return await self.get_records(relation_table, filters=filters)

    async def get_parent_record(
        self, table: str, record: Dict, parent_field: str
    ) -> Optional[Dict]:
        """Get the parent record for a relationship field."""
        schema = self.get_table_schema(table)
        if not schema or parent_field not in record:
            return None

        relations = schema.get("relations", {})
        if parent_field not in relations:
            return None

        parent_table = relations[parent_field]["view"]
        parent_id = record[parent_field]

        if not parent_id:
            return None

        return await self.get_record_by_id(parent_table, parent_id)

    # =====================================================================
    #  RESOURCE CLEANUP
    # =====================================================================

    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
