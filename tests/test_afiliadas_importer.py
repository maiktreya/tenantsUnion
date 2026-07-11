import sys
import types
import asyncio
import pytest

# Asegurar un entorno stub aislado de NiceGUI por si los tests corren sin dependencias de UI nativas
try:
    import nicegui  # type: ignore
except Exception:  # pragma: no cover
    m = types.ModuleType("nicegui")
    class _Dummy:
        def __call__(self, *a, **k): return self
        def __getattr__(self, _): return self
        def classes(self, *a, **k): return self
        def props(self, *a, **k): return self
        def set_enabled(self, *a, **k): return self
        def clear(self, *a, **k): return self
        def push(self, *a, **k): return self
    ui = _Dummy()
    m.ui = ui
    m.app = _Dummy()
    m.app.storage = types.SimpleNamespace(client={})
    m.events = types.SimpleNamespace(UploadEventArguments=object, GenericEventArguments=object)
    sys.modules['nicegui'] = m

# Importaciones del ecosistema de ingesta relacional refactorizado
from services.relational_import_service import MultiTableImportService
from views.generic_importer import GenericRelationalImporterView
from config import HOUSING_UNION_IMPORT_CONFIG


class MockPostgrestAPI:
    """
    Simulador asíncrono que emula las inserciones en cascada de PostgREST,
    registrando los payloads y devolviendo identificadores secuenciales (IDs).

    NOTA: debe reproducir fielmente el contrato de `APIClient.create_record`,
    que devuelve una tupla `(record, error_msg)` con el registro ya desempaquetado
    en un dict (no la lista JSON cruda de PostgREST). `MultiTableImportService`
    hace `record, error_msg = await self.api.create_record(...)`, así que
    devolver un único valor rompe el unpacking.
    """
    def __init__(self):
        self.id_counter = 5000
        self.recorded_payloads = []

    async def create_record(self, table_name: str, payload: dict):
        self.id_counter += 1
        # Captura instantáneas limpias para poder inspeccionar los payloads en las aserciones
        self.recorded_payloads.append({
            "table": table_name,
            "payload": payload.copy()
        })
        # Tupla (record, error_msg) idéntica al contrato real de APIClient.create_record
        return {"id": self.id_counter}, None


@pytest.fixture
def mock_api():
    return MockPostgrestAPI()


@pytest.fixture
def import_service(mock_api):
    return MultiTableImportService(mock_api, HOUSING_UNION_IMPORT_CONFIG)


@pytest.fixture
def mock_nicegui_storage(monkeypatch):
    """
    Fixture de aislamiento: Sobrescribe el almacenamiento dinámico por cliente de NiceGUI
    para neutralizar RuntimeErrors de contexto de sesión durante la inicialización de vistas.
    """
    from nicegui import app
    mock_storage = types.SimpleNamespace(client={})
    monkeypatch.setattr(app, "storage", mock_storage, raising=False)
    return mock_storage


# =====================================================================
# PRUEBAS UNITARIAS DEL MOTOR LOGICO DE CASILES (PIPELINE SERVICE)
# =====================================================================

@pytest.mark.asyncio
async def test_csv_byte_stream_parsing(import_service):
    """Garantiza la correcta lectura del stream de bytes plano y su descodificación con BOM UTF-8."""
    csv_bytes = (
        b"\xef\xbb\xbfdireccion_bloque,direccion_vivienda_completa,nombre_afiliada,cuota\n"
        b"Calle de la lucha 12,Calle de la lucha 12 3B,Maria Gomez,15.50\n"
    )

    parsed_records = await import_service.parse_csv_bytes(csv_bytes)

    assert len(parsed_records) == 1
    assert parsed_records[0]["direccion_bloque"] == "Calle de la lucha 12"
    assert parsed_records[0]["nombre_afiliada"] == "Maria Gomez"
    assert parsed_records[0]["cuota"] == "15.50"


@pytest.mark.asyncio
async def test_relational_insertion_and_fk_lineage(import_service, mock_api):
    """
    Test Crítico: Valida que un registro plano se rompa secuencialmente y que las
    entidades hijas enlacen los IDs autogenerados de sus respectivos padres relacionales.
    """
    raw_csv_record = [{
        "direccion_bloque": "Paseo de las Delicias 45",
        "empresa_propietaria": "Rentista SL",
        "direccion_vivienda_completa": "Paseo de las Delicias 45, Piso 4",
        "localidad": "Madrid",
        "codigo_postal": "28045",
        "propiedad_vertical": "Si",
        "nombre_afiliada": "Lucia",
        "apellidos_afiliada": "Fernandez",
        "dni_nie": "12345678X",
        "cuota": "10.00",
        "periodicidad": "1",  # Mensual
        "cuenta_bancaria_iban": "ES9101234567890123456789"
    }]

    # Ejecutar la importación simulada consumiendo los logs del generador asíncrono
    logs = []
    async for update in import_service.process_relational_import(raw_csv_record):
        logs.append(update)

    # 1. Verificar inserción exitosa en las 4 tablas relacionales
    assert len(mock_api.recorded_payloads) == 4

    bloque_entry = mock_api.recorded_payloads[0]
    piso_entry = mock_api.recorded_payloads[1]
    afiliada_entry = mock_api.recorded_payloads[2]
    facturacion_entry = mock_api.recorded_payloads[3]

    # 2. Corroborar el orden secuencial estricto de inserción para respetar restricciones
    assert bloque_entry["table"] == "bloques"
    assert piso_entry["table"] == "pisos"
    assert afiliada_entry["table"] == "afiliadas"
    assert facturacion_entry["table"] == "facturacion"

    # 3. Validar el paso e inyección precisa de linaje de claves foráneas (FKs)
    generated_bloque_id = 5001
    generated_piso_id = 5002
    generated_afiliada_id = 5003

    assert piso_entry["payload"]["bloque_id"] == generated_bloque_id
    assert afiliada_entry["payload"]["piso_id"] == generated_piso_id
    assert facturacion_entry["payload"]["afiliada_id"] == generated_afiliada_id

    # 4. Validar el mapeo de campos específicos (texto a pisos.propiedad, cuotas y periodicidad)
    assert piso_entry["payload"]["propiedad"] == "Rentista SL"
    assert piso_entry["payload"]["prop_vertical"] == "Si"
    assert afiliada_entry["payload"]["nombre"] == "Lucia"
    assert facturacion_entry["payload"]["periodicidad"] == 1


@pytest.mark.asyncio
async def test_skipping_completely_empty_optional_sub_blocks(import_service, mock_api):
    """
    Asegura que si un sub-bloque opcional (como la información de facturación o el bloque de finca)
    viene completamente en blanco en el CSV del usuario, el motor lo omita limpiamente sin enviar
    un payload vacío o corrupto a la base de datos de producción.
    """
    raw_record_without_billing = [{
        "direccion_bloque": "Calle Mayor 1",
        "empresa_propietaria": None,
        "direccion_vivienda_completa": "Calle Mayor 1, Principal Izquierda",
        "localidad": "Getafe",
        "codigo_postal": "28901",
        "propiedad_vertical": "",  # Se autocoercionará a 'No' por defecto
        "nombre_afiliada": "Carlos",
        "apellidos_afiliada": "Ruiz",
        "dni_nie": "87654321Z",
        # Parámetros explícitamente vacíos en el sub-bloque de facturación
        "cuota": "",
        "periodicidad": " ",
        "cuenta_bancaria_iban": ""
    }]

    async for _ in import_service.process_relational_import(raw_record_without_billing):
        pass

    # El flujo debe impactar bloques, pisos (con propiedad_vertical='No') y afiliadas,
    # pero tiene que saltarse por completo la inserción en la tabla de facturación.
    inserted_tables = [item["table"] for item in mock_api.recorded_payloads]
    assert "bloques" in inserted_tables
    assert "pisos" in inserted_tables
    assert "afiliadas" in inserted_tables
    assert "facturacion" not in inserted_tables

    # Comprobar la aserción de coerción del valor por defecto
    assert mock_api.recorded_payloads[1]["payload"]["prop_vertical"] == "No"


# =====================================================================
# PRUEBAS UNITARIAS DE LA CAPA DE PRESENTACIÓN (INTERFAZ)
# =====================================================================

def test_view_staging_memory_allocation(mock_nicegui_storage, mock_api):
    """Verifica que la vista configure y reserve correctamente el almacenamiento aislado por cliente."""
    # GenericRelationalImporterView.__init__ solo acepta `api_client`: internamente
    # ya fija `schema_config = HOUSING_UNION_IMPORT_CONFIG`, no se le pasa por fuera.
    view_instance = GenericRelationalImporterView(mock_api)

    # Comprobar el correcto enrutamiento del estado interno local
    assert "generic_importer_records" in mock_nicegui_storage.client
    assert isinstance(view_instance.raw_records, list)