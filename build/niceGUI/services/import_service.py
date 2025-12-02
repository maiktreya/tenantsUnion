# build/niceGUI/services/import_service.py

import pandas as pd
import io
import asyncio
import logging
import copy
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from dataclasses import dataclass, field

from api.client import APIClient
from components.importer_utils import transform_and_validate_row, short_address
from components.importer_normalization import normalize_address_key
from components.importer_record_status import ImporterRecordStatusService

log = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """A data class to hold the results of the import process."""
    total_records: int
    success_count: int = 0
    failed_imports: List[Dict] = field(default_factory=list)
    failed_snapshots: List[Dict] = field(default_factory=list)
    newly_created_afiliadas: List[Dict] = field(default_factory=list)
    log: List[str] = field(default_factory=list)


class AfiliadasImportService:
    """
    Service responsible for parsing CSV data, validating records, handling
    suggestions, and executing the import transaction logic.
    """

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.status_service = ImporterRecordStatusService(api_client)
        self._bloque_details_cache: Dict[int, Dict[str, Any]] = {}
        # Default score limit for fuzzy matching
        self.bloque_score_limit: float = 0.88

    def set_score_limit(self, limit: float):
        """Update the fuzzy match threshold."""
        self.bloque_score_limit = limit

    async def prepare_records_from_csv(self, csv_content: bytes) -> List[Dict]:
        """
        Parses CSV bytes, validates structure, preloads status caches (duplicates),
        and applies initial block suggestions.
        """
        self.status_service.reset()
        self._bloque_details_cache.clear()

        # Decode and parse
        content = csv_content.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(content), header=None, dtype=str).fillna("")
        
        # Transform rows
        records = [
            rec
            for _, row in df.iloc[1:].iterrows()
            if (rec := transform_and_validate_row(row)) is not None
        ]

        # Bulk pre-fetch duplicate statuses
        await self.status_service.preload_afiliada_cifs(records)
        await self.status_service.preload_piso_addresses(records)

        # Apply statuses to records
        for record in records:
            self._sync_metadata_from_status_cache(record)

        # Apply initial block suggestions
        await self.apply_batch_bloque_suggestions(records)
        
        return records

    async def apply_batch_bloque_suggestions(self, records: List[Dict]):
        """
        Fetches and applies block suggestions for a list of records 
        based on the current score limit.
        """
        if not records:
            return

        addresses = [
            {"index": idx, "direccion": r["piso"]["direccion"]}
            for idx, r in enumerate(records)
            if r.get("piso", {}).get("direccion")
        ]
        
        if not addresses:
            return

        try:
            suggestions = await self.api.get_bloque_suggestions(
                addresses, self.bloque_score_limit
            )
            suggestion_map = {
                s["piso_id"]: s for s in suggestions if s.get("piso_id") is not None
            }

            for idx, record in enumerate(records):
                suggestion = suggestion_map.get(idx)
                meta = record.setdefault("meta", {})
                
                # Logic to determine if we apply the suggestion or keep manual override would go here
                # For now, we apply suggestions if they meet criteria
                if suggestion and (
                    suggestion.get("suggested_bloque_id")
                    or suggestion.get("suggested_bloque_direccion")
                ):
                    meta["bloque"] = {
                        "id": suggestion.get("suggested_bloque_id"),
                        "direccion": suggestion.get("suggested_bloque_direccion"),
                    }
                    meta["bloque_score"] = suggestion.get("suggested_score")
                    
                    # If not explicitly linked yet, show suggestion in 'bloque' field
                    if record.get("piso", {}).get("bloque_id") is None:
                         record.setdefault("bloque", {})["direccion"] = suggestion.get(
                            "suggested_bloque_direccion"
                        )
                else:
                    meta.update({"bloque": None, "bloque_score": None})
                    # Revert to short address if no link
                    if record.get("piso", {}).get("bloque_id") is None:
                        record.setdefault("bloque", {})["direccion"] = short_address(
                            record.get("piso", {}).get("direccion", "")
                        )
        except Exception as e:
            log.warning("Failed to get bloque suggestions", exc_info=True)

    async def execute_import_process(
        self, records: List[Dict]
    ) -> AsyncGenerator[Union[str, ImportResult], None]:
        """
        Executes the import. Yields status strings for UI updates. 
        Yields the final ImportResult object as the last item.
        """
        result = ImportResult(total_records=len(records))

        for i, record in enumerate(records):
            name = f"{record['afiliada']['nombre']} {record['afiliada']['apellidos']}".strip()
            
            # Yield status update to the consumer (UI)
            yield f"Procesando {i + 1}/{result.total_records}: {name}..."

            try:
                # 1. Ensure/Link Bloque
                bloque_id = await self._ensure_bloque(record, result.log)
                record["piso"]["bloque_id"] = bloque_id

                # 2. Ensure/Create Piso
                piso_id = await self._ensure_piso(record, result.log)
                record["afiliada"]["piso_id"] = piso_id

                # 3. Create Afiliada
                new_afiliada = await self._create_afiliada(record, result.log)
                result.newly_created_afiliadas.append(new_afiliada)

                # 4. Create Facturacion
                await self._create_facturacion(record, new_afiliada["id"], result.log)

                result.success_count += 1
            except Exception as e:
                error_message = str(e)
                result.failed_imports.append({"afiliada": name, "error": error_message})
                result.failed_snapshots.append(
                    self._snapshot_failed_record(record, error_message)
                )
                error_log = f"❌ ERROR al importar a {name}: {error_message}"
                result.log.append(error_log)
                yield error_log # Yield error to UI log immediately

            # Slight yield to allow UI to render
            await asyncio.sleep(0.01)

        # Finalize log
        self._append_summary_to_log(result)
        
        # Yield final result
        yield result

    # --- Internal Logic Helpers ---

    async def _ensure_bloque(self, record: Dict, log_list: List[str]) -> Optional[int]:
        bloque_id = record["piso"].get("bloque_id")
        bloque_direccion = record["bloque"].get("direccion")

        if bloque_id:
            # Verify ID exists
            if not await self.api.get_records("bloques", {"id": f"eq.{bloque_id}"}):
                raise ValueError(f"El ID de bloque '{bloque_id}' proporcionado no existe.")
            return int(bloque_id)

        if bloque_direccion:
            # Check by address
            existing = await self.api.get_records(
                "bloques", {"direccion": f"eq.{bloque_direccion}"}
            )
            if existing:
                log_list.append(f"ℹ️ Bloque encontrado: {bloque_direccion} (ID: {existing[0]['id']})")
                return existing[0]["id"]

            # Create new
            new_bloque, error = await self.api.create_record(
                "bloques", {"direccion": bloque_direccion}
            )
            if error:
                raise Exception(f"Error al crear bloque: {error}")
            log_list.append(f"➕ Bloque creado: {bloque_direccion} (ID: {new_bloque['id']})")
            return new_bloque["id"]
        return None

    async def _ensure_piso(self, record: Dict, log_list: List[str]) -> int:
        piso_direccion = record["piso"]["direccion"]
        existing = await self.api.get_records("pisos", {"direccion": f"eq.{piso_direccion}"})
        
        if existing:
            log_list.append(f"ℹ️ Piso encontrado: {piso_direccion} (ID: {existing[0]['id']})")
            return existing[0]["id"]

        new_piso, error = await self.api.create_record("pisos", record["piso"])
        if error:
            raise Exception(f"Error al crear piso: {error}")
        log_list.append(f"➕ Piso creado: {piso_direccion} (ID: {new_piso['id']})")
        return new_piso["id"]

    async def _create_afiliada(self, record: Dict, log_list: List[str]) -> Dict:
        new_afiliada, error = await self.api.create_record("afiliadas", record["afiliada"])
        if error:
            raise Exception(f"Error al crear afiliada: {error}")
        name = f"{new_afiliada.get('nombre', '')} {new_afiliada.get('apellidos', '')}".strip()
        log_list.append(
            f"✅ Afiliada creada: {name} (ID: {new_afiliada['id']}, Nº: {new_afiliada.get('num_afiliada')})"
        )
        return new_afiliada

    async def _create_facturacion(self, record: Dict, afiliada_id: int, log_list: List[str]):
        fact_data = record["facturacion"]
        if fact_data.get("iban") or fact_data.get("cuota", 0) > 0:
            fact_data["afiliada_id"] = afiliada_id
            _, error = await self.api.create_record("facturacion", fact_data)
            if error:
                log_list.append(f"⚠️ Aviso (Facturación): {error}")
            else:
                log_list.append(f"💰 Facturación añadida.")

    def _sync_metadata_from_status_cache(self, record: Dict):
        """Updates record metadata based on preloaded existence checks."""
        # Check Afiliada (CIF)
        afiliada_cif = (record.get("afiliada", {}).get("cif") or "").strip().upper()
        exists_afiliada = bool(
            afiliada_cif and self.status_service.existing_afiliada_cifs.get(afiliada_cif)
        )
        record.setdefault("meta", {})["nif_exists"] = exists_afiliada
        
        # Add warning to validation if needed
        from config import DUPLICATE_NIF_WARNING
        warnings = record.setdefault("validation", {}).setdefault("warnings", [])
        if exists_afiliada and DUPLICATE_NIF_WARNING not in warnings:
            warnings.append(DUPLICATE_NIF_WARNING)
        elif not exists_afiliada and DUPLICATE_NIF_WARNING in warnings:
            warnings.remove(DUPLICATE_NIF_WARNING)

        # Check Piso (Address)
        direccion = (record.get("piso", {}).get("direccion") or "").strip()
        key = normalize_address_key(direccion)
        exists_piso = bool(self.status_service.existing_piso_addresses.get(key))
        record.setdefault("meta", {})["piso_exists"] = exists_piso

    def _snapshot_failed_record(self, record: Dict, error_message: str) -> Dict:
        """Creates a deep copy of a failed record for the error report."""
        return {
            "afiliada": copy.deepcopy(record.get("afiliada")),
            "piso": copy.deepcopy(record.get("piso")),
            "bloque": copy.deepcopy(record.get("bloque")),
            "facturacion": copy.deepcopy(record.get("facturacion")),
            "meta": {"nif_exists": record.get("meta", {}).get("nif_exists")},
            "validation": {
                "errors": list(record.get("validation", {}).get("errors", [])),
                "warnings": list(record.get("validation", {}).get("warnings", [])),
            },
            "error": error_message,
        }

    def _append_summary_to_log(self, result: ImportResult):
        summary_lines = [
            f"\nResumen final del proceso de importación",
            f"Total de registros procesados: {result.total_records}",
            f"Importaciones exitosas: {result.success_count}",
            f"Registros con errores: {len(result.failed_imports)}",
        ]
        if result.newly_created_afiliadas:
            summary_lines.append("\nAfiliadas creadas durante este proceso:")
            for af in result.newly_created_afiliadas:
                summary_lines.append(
                    f" - {af.get('nombre')} {af.get('apellidos')} (ID: {af.get('id')}, Nº: {af.get('num_afiliada')})"
                )
        if result.failed_imports:
            summary_lines.append(
                "\nConsulta la pestaña de fallidos para revisar y corregir los errores."
            )
        result.log.extend(summary_lines)