import csv
import io
import logging
from datetime import datetime
from typing import Dict, Any, List, Generator, AsyncGenerator, Optional
from api.client import APIClient

log = logging.getLogger(__name__)

class MultiTableImportService:
    """
    Gestiona la lectura de filas planas de un CSV y puebla secuencialmente las tablas
    relacionales manteniendo la integridad del linaje de claves foráneas.
    """
    def __init__(self, api_client: APIClient, schema_config: Dict[str, Any]):
        self.api = api_client
        self.config = schema_config
        self.execution_order: List[str] = schema_config.get("execution_order", [])
        self.table_mappings: Dict[str, Dict[str, str]] = schema_config.get("mappings", {})

    async def parse_csv_bytes(self, csv_bytes: bytes) -> List[Dict[str, Any]]:
        """Descodifica de forma segura el stream de bytes del archivo CSV cargado."""
        try:
            content = csv_bytes.decode('utf-8-sig')
            file_like = io.StringIO(content)
            reader = csv.DictReader(file_like)
            return list(reader)
        except Exception as e:
            log.error(f"Error parsing CSV byte stream: {e}")
            raise RuntimeError(f"Error en parseo de datos CSV: {str(e)}")

    def _normalize_date_string(self, val: str) -> str:
        """
        Intenta parsear cadenas de texto con fechas en formatos comunes y las
        homogeneiza estrictamente al formato requerido por el validador (AAAA-MM-DD).
        """
        cleaned = val.strip()
        if not cleaned:
            return val

        formats_to_try = [
            "%Y-%m-%d",  # 2026-07-10 (Estándar)
            "%d/%m/%Y",  # 10/07/2026 (Español con barras)
            "%d-%m-%Y",  # 10-02-2026 (Español con guiones)
            "%Y/%m/%d",  # 2026/07/10 (Alternativo)
        ]

        for fmt in formats_to_try:
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return cleaned

    async def process_relational_import(self, raw_records: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """
        Itera las filas del CSV, extrae los esquemas de datos por entidad, realiza las llamadas
        a PostgREST y propaga los IDs de los padres hacia las claves foráneas de los hijos.
        """
        total = len(raw_records)
        success_count = 0
        failed_count = 0

        yield f"Iniciando bucle de procesamiento para {total} filas relacionales...\n"

        for idx, raw_row in enumerate(raw_records, start=1):
            # GANCHO DE SEGURIDAD PREVENTIVO: Ignorar silenciosamente la fila de metadatos guía del CSV
            if raw_row.get("nombre_afiliada") == "Obligatorio":
                continue

            generated_lineage_keys: Dict[str, int] = {}
            row_failed = False
            
            yield f"[{idx}/{total}] Procesando linaje de la fila..."

            for table_name in self.execution_order:
                mapping = self.table_mappings.get(table_name, {})
                db_payload: Dict[str, Any] = {}
                
                # ---- PASO 1: EXTRAER Y LIMPIAR ÚNICAMENTE LOS DATOS DEL CSV ----
                has_user_data = False
                has_user_mappings = False
                
                for db_column, csv_header in mapping.items():
                    if not str(csv_header).startswith("__fk__"):
                        has_user_mappings = True
                        val = raw_row.get(csv_header)
                        cleaned_val = val.strip() if (val and val.strip()) else None
                        
                        # Coerción imperativa de Propiedad Vertical por defecto
                        if db_column == "prop_vertical" and cleaned_val is None:
                            cleaned_val = "No"
                        
                        # ---- GANCHO DE TOLERANCIA DE FECHAS ----
                        if cleaned_val is not None and ("fecha" in db_column or "date" in db_column):
                            cleaned_val = self._normalize_date_string(cleaned_val)
                        
                        # ---- GANCHO DE TOLERANCIA DE PERIODICIDAD (Mensual -> 1, Anual -> 12) ----
                        if db_column == "periodicidad" and cleaned_val is not None:
                            norm_p = cleaned_val.lower()
                            if "mensual" in norm_p or norm_p == "1":
                                cleaned_val = 1
                            elif "anual" in norm_p or norm_p == "12":
                                cleaned_val = 12
                        
                        if cleaned_val is not None:
                            has_user_data = True
                        db_payload[db_column] = cleaned_val

                # ---- PASO 2: OMITIR SUB-BLOQUES OPCIONALES VACÍOS ----
                if has_user_mappings and not has_user_data:
                    continue

                # ---- PASO 3: INYECTAR LAS CLAVES FORÁNEAS (FK) DEL LINAJE PADRE ----
                for db_column, csv_header in mapping.items():
                    if str(csv_header).startswith("__fk__"):
                        parent_table = csv_header.replace("__fk__", "").split(".")[0]
                        parent_id = generated_lineage_keys.get(parent_table)
                        
                        db_payload[db_column] = parent_id if parent_id else None

                if row_failed:
                    break

                try:
                    # Intentar la creación del registro a través de la API PostgREST
                    record, error_msg = await self.api.create_record(table_name, db_payload)
                    
                    # ---- NÚCLEO DE IDEMPOTENCIA: GANCHO DE SALVAMENTO RELACIONAL ----
                    if error_msg and "Error de Duplicado" in error_msg:
                        existing_records = []
                        
                        if table_name in ["bloques", "pisos"] and db_payload.get("direccion"):
                            existing_records = await self.api.get_records(
                                table_name, 
                                filters={"direccion": f"eq.{db_payload['direccion']}"}
                            )
                        elif table_name == "afiliadas" and db_payload.get("cif"):
                            existing_records = await self.api.get_records(
                                table_name, 
                                filters={"cif": f"eq.{db_payload['cif']}"}
                            )
                        
                        if existing_records:
                            record = existing_records[0]
                            error_msg = None
                    
                    # Guardar el ID en el linaje de ejecución temporal
                    if record and isinstance(record, dict) and "id" in record:
                        generated_lineage_keys[table_name] = record["id"]
                    elif record and isinstance(record, list) and record and "id" in record[0]:
                        generated_lineage_keys[table_name] = record[0]["id"]
                    else:
                        err_detail = f" Detalle: {error_msg}" if error_msg else ""
                        yield f" -> Error cargando en tabla '{table_name}'.{err_detail}\n"
                        row_failed = True
                        break
                        
                except Exception as ex:
                    log.error(f"Fallo de inserción relacional en tabla {table_name}: {ex}")
                    yield f" -> Excepción crítica en tabla '{table_name}': {str(ex)}\n"
                    row_failed = True
                    break

            if row_failed:
                failed_count += 1
            else:
                success_count += 1

        yield f"\n*** Pipeline de Importación Finalizado ***\nFilas procesadas con éxito: {success_count}\nFilas fallidas: {failed_count}\n"