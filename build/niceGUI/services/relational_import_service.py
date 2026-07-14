# build/niceGUI/services/relational_import_service.py
import csv
import io
import logging
from typing import Any, AsyncGenerator, Dict, List, Set, Tuple

from api.client import APIClient

log = logging.getLogger(__name__)


class MultiTableImportService:
    """
    Handles parsing de-normalized flat rows and sequentially populating
    relational target database tables while maintaining foreign key lineage.
    """

    def __init__(self, api_client: APIClient, schema_config: Dict[str, Any]):
        self.api = api_client
        self.config = schema_config
        self.execution_order: List[str] = schema_config.get("execution_order", [])
        self.table_mappings: Dict[str, Dict[str, str]] = schema_config.get("mappings", {})

    async def parse_csv_bytes(self, csv_bytes: bytes) -> List[Dict[str, Any]]:
        """Safely decodes and extracts structured raw records."""
        try:
            content = csv_bytes.decode("utf-8-sig")
            file_like = io.StringIO(content)
            reader = csv.DictReader(file_like)
            return list(reader)
        except Exception as e:
            log.error(f"Failed to parse CSV byte stream: {e}")
            raise RuntimeError(f"CSV data parsing failure: {str(e)}")

    # =====================================================================
    # Shared payload construction.
    #
    # This used to live inline inside `process_relational_import` only.
    # It is now factored out so that the dry-run preview
    # (`validate_relational_import`) and the real import run build the
    # *exact* same per-table payload from a CSV row — including the
    # `prop_vertical` default-coercion rule — so the two can never quietly
    # drift apart and report different things to the user.
    # =====================================================================
    def _build_table_payload(
        self, table_name: str, raw_row: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], bool, bool]:
        """
        Extracts and cleans the user-supplied (non-FK) columns for one table
        from a single flat CSV row.

        Returns (payload, has_user_mappings, has_user_data):
          - has_user_mappings: this table has at least one non-FK column mapped
            in the schema config.
          - has_user_data: at least one of those mapped columns was non-blank
            in this particular row.
        """
        mapping = self.table_mappings.get(table_name, {})
        payload: Dict[str, Any] = {}
        has_user_data = False
        has_user_mappings = False

        for db_column, csv_header in mapping.items():
            if str(csv_header).startswith("__fk__"):
                continue  # hydrated separately; only meaningful during the real run

            has_user_mappings = True
            val = raw_row.get(csv_header)
            cleaned_val = val.strip() if (val and val.strip()) else None

            # Coerción de Propiedad Vertical obligatoria por defecto si viene vacía
            if db_column == "prop_vertical" and cleaned_val is None:
                cleaned_val = "No"

            if cleaned_val is not None:
                has_user_data = True
            payload[db_column] = cleaned_val

        return payload, has_user_mappings, has_user_data

    def _preview_label(self, raw_row: Dict[str, Any]) -> str:
        """Builds a human-readable row identifier from the row's first non-blank values."""
        values = [v.strip() for v in raw_row.values() if v and v.strip()]
        return " / ".join(values[:3]) if values else "(fila vacía)"

    # =====================================================================
    # Dry-run validation — never calls create_record, never touches the DB.
    # =====================================================================
    async def validate_relational_import(
        self, raw_records: List[Dict[str, Any]], mandatory_headers: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Replays the exact same field-mapping/cleaning logic used by
        `process_relational_import`, but instead of inserting rows, checks
        each table's resulting payload against `TableValidator` (through
        `api.validate_record_data`, which performs no network I/O at all)
        and against the caller-supplied set of mandatory CSV headers.

        Known limitation: this cannot detect DB-side uniqueness conflicts
        (e.g. a CIF that already exists) since that requires a live query
        against current table state, not just the config-driven rules
        `TableValidator` knows about. Those are still only caught when the
        real import actually runs.
        """
        results: List[Dict[str, Any]] = []

        for idx, raw_row in enumerate(raw_records, start=1):
            issues: List[str] = []

            for table_name in self.execution_order:
                payload, has_user_mappings, has_user_data = self._build_table_payload(
                    table_name, raw_row
                )

                if has_user_mappings and not has_user_data:
                    continue  # mirrors the "skip empty optional sub-block" rule below

                mapping = self.table_mappings.get(table_name, {})
                for db_column, csv_header in mapping.items():
                    if csv_header in mandatory_headers and not payload.get(db_column):
                        issues.append(f"Falta el campo obligatorio: {csv_header}")

                _, table_errors = await self.api.validate_record_data(
                    table_name, payload, "create"
                )
                issues.extend(table_errors)

            results.append(
                {
                    "row_number": idx,
                    "status": "error" if issues else "valid",
                    "preview_label": self._preview_label(raw_row),
                    "issues": issues,
                }
            )

        return results

    # =====================================================================
    # Real import run.
    # =====================================================================
    async def process_relational_import(
        self, raw_records: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """
        Sequentially loops rows, extracts specific target schemas, posts
        records via PostgREST, and binds child foreign keys down the pipeline.
        """
        total = len(raw_records)
        success_count = 0
        failed_count = 0

        yield f"Starting processing loop for {total} relational rows...\n"

        for idx, raw_row in enumerate(raw_records, start=1):
            generated_lineage_keys: Dict[str, int] = {}
            row_failed = False

            yield f"[{idx}/{total}] Processing row lineage keys..."

            for table_name in self.execution_order:
                mapping = self.table_mappings.get(table_name, {})

                db_payload, has_user_mappings, has_user_data = self._build_table_payload(
                    table_name, raw_row
                )

                if has_user_mappings and not has_user_data:
                    continue

                # ---- Hydrate the registered foreign key lineage ----
                for db_column, csv_header in mapping.items():
                    if str(csv_header).startswith("__fk__"):
                        parent_table = csv_header.replace("__fk__", "").split(".")[0]
                        parent_id = generated_lineage_keys.get(parent_table)
                        # Si el padre opcional (ej: bloques) se omitió, la FK se asigna como None
                        db_payload[db_column] = parent_id if parent_id else None

                try:
                    # `create_record` returns a (record, error_message) tuple — NOT the
                    # raw record itself. The previous version of this loop checked
                    # `isinstance(result, list)` / `isinstance(result, dict)` against
                    # that tuple, which is neither, so it always fell through to the
                    # "error" branch even on a successful insert, marking every row
                    # failed and aborting the chain after the very first table. Fixed
                    # by unpacking the tuple, matching how `api.batch_create` already
                    # consumes `create_record` elsewhere in this codebase.
                    record, error_msg = await self.api.create_record(table_name, db_payload)

                    if record and "id" in record:
                        generated_lineage_keys[table_name] = record["id"]
                    else:
                        yield f" -> Error loading into table '{table_name}': {error_msg}\n"
                        row_failed = True
                        break

                except Exception as ex:
                    log.error(
                        f"API relational block insertion failure on table {table_name}: {ex}"
                    )
                    yield f" -> Critical Exception on table '{table_name}': {str(ex)}\n"
                    row_failed = True
                    break

            if row_failed:
                failed_count += 1
            else:
                success_count += 1

        yield (
            f"\n*** Import Pipeline Finished ***\n"
            f"Success rows: {success_count}\nFailed entries: {failed_count}\n"
        )