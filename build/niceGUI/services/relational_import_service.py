import csv
import io
import logging
from typing import Dict, Any, List, Generator, AsyncGenerator
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
            content = csv_bytes.decode('utf-8-sig')
            file_like = io.StringIO(content)
            reader = csv.DictReader(file_like)
            return list(reader)
        except Exception as e:
            log.error(f"Failed to parse CSV byte stream: {e}")
            raise RuntimeError(f"CSV data parsing failure: {str(e)}")

    async def process_relational_import(self, raw_records: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
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
                db_payload: Dict[str, Any] = {}
                
                # ---- STEP 1: PARSE AND CLEAN USER CSV FIELD DATA ONLY ----
                has_user_data = False
                has_user_mappings = False
                
                for db_column, csv_header in mapping.items():
                    if not str(csv_header).startswith("__fk__"):
                        has_user_mappings = True
                        val = raw_row.get(csv_header)
                        cleaned_val = val.strip() if (val and val.strip()) else None
                        
                        # Coerción de Propiedad Vertical obligatoria por defecto si viene vacía
                        if db_column == "prop_vertical" and cleaned_val is None:
                            cleaned_val = "No"
                        
                        if cleaned_val is not None:
                            has_user_data = True
                        db_payload[db_column] = cleaned_val

                # ---- STEP 2: SKIP OPTIONAL SUB-BLOCKS IF USER FIELDS ARE EMPTY ----
                if has_user_mappings and not has_user_data:
                    continue

                # ---- STEP 3: HYDRATE THE REGISTERED FOREIGN KEYS LINEAGE ----
                for db_column, csv_header in mapping.items():
                    if str(csv_header).startswith("__fk__"):
                        parent_table = csv_header.replace("__fk__", "").split(".")[0]
                        parent_id = generated_lineage_keys.get(parent_table)
                        
                        # FIX: Si el padre opcional (ej: bloques) se omitió, la FK se asigna como None en vez de fallar
                        db_payload[db_column] = parent_id if parent_id else None

                if row_failed:
                    break

                try:
                    # Leverage the explicit low-overhead PostgREST API client wrapper
                    result = await self.api.create_record(table_name, db_payload)
                    
                    if result and isinstance(result, list) and "id" in result[0]:
                        generated_lineage_keys[table_name] = result[0]["id"]
                    elif result and isinstance(result, dict) and "id" in result:
                        generated_lineage_keys[table_name] = result["id"]
                    else:
                        yield f" -> Error loading into table '{table_name}'\n"
                        row_failed = True
                        break
                        
                except Exception as ex:
                    log.error(f"API relational block insertion failure on table {table_name}: {ex}")
                    yield f" -> Critical Exception on table '{table_name}': {str(ex)}\n"
                    row_failed = True
                    break

            if row_failed:
                failed_count += 1
            else:
                success_count += 1

        yield f"\n*** Import Pipeline Finished ***\nSuccess rows: {success_count}\nFailed entries: {failed_count}\n"