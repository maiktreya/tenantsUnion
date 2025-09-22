import sys
import types
from pathlib import Path
import asyncio
import pytest


# Ensure modules under build/niceGUI are importable as top-level packages
ROOT = Path(__file__).resolve().parents[1] / "build" / "niceGUI"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Provide a very small stub for nicegui if it's not available during tests
try:
    import nicegui  # type: ignore
except Exception:  # pragma: no cover - only used in environments without NiceGUI
    m = types.ModuleType("nicegui")
    class _Dummy:
        def __call__(self, *a, **k):
            return self
        def __getattr__(self, _):
            return self
        def classes(self, *a, **k):
            return self
        def props(self, *a, **k):
            return self
        def on(self, *a, **k):
            return self
        def bind_value(self, *a, **k):
            return self
        def bind_text_from(self, *a, **k):
            return self
        def set_text(self, *a, **k):
            return self
        def set_name(self, *a, **k):
            return self
        def set_enabled(self, *a, **k):
            return self
        def open(self, *a, **k):
            return self
        def close(self, *a, **k):
            return self
        def push(self, *a, **k):
            return self
    ui = _Dummy()
    m.ui = ui
    m.events = types.SimpleNamespace(UploadEventArguments=object, GenericEventArguments=object)
    sys.modules['nicegui'] = m


# Now we can safely import the app modules
from views.afiliadas_importer import AfiliadasImporterView  # type: ignore
from state.app_state import GenericViewState  # type: ignore
from components.importer_utils import short_address  # type: ignore


class DummyAPI:
    def __init__(self):
        self._bloques = {
            1001: {"id": 1001, "direccion": "Calle de Prueba 10"},
        }

    async def get_bloque_suggestions(self, addresses, score_limit: float = 0.88):
        # Simple deterministic stub:
        # - first address gets a match with score 0.70
        # - others get None
        out = []
        for item in addresses:
            idx = item.get("index")
            if idx == 0 and score_limit <= 0.7:
                out.append({
                    "piso_id": idx,
                    "piso_direccion": item.get("direccion"),
                    "suggested_bloque_id": 1001,
                    "suggested_bloque_direccion": "Calle de Prueba 10",
                    "suggested_score": 0.70,
                })
            else:
                out.append({
                    "piso_id": idx,
                    "piso_direccion": item.get("direccion"),
                    "suggested_bloque_id": None,
                    "suggested_bloque_direccion": None,
                    "suggested_score": None,
                })
        return out

    async def get_records(self, table: str, filters):
        if table == "bloques":
            try:
                _id = int(str(filters.get("id", "eq.0").split(".")[-1]))
                return [self._bloques[_id]] if _id in self._bloques else []
            except Exception:
                return []
        return []

    async def create_record(self, *a, **k):  # not used in these tests
        return None, None


@pytest.fixture
def view(monkeypatch):
    state = GenericViewState()
    api = DummyAPI()
    v = AfiliadasImporterView(api, state)
    # Avoid rendering UI during tests
    monkeypatch.setattr(v, "_render_all_panels", lambda: None)
    return v


def _make_record(nombre: str, apellidos: str, piso_dir: str, email: str = "user@example.com"):
    return {
        "afiliada": {
            "nombre": nombre,
            "apellidos": apellidos,
            "genero": "",
            "fecha_nac": "1990-01-01",
            "cif": "",
            "telefono": "",
            "email": email,
            "fecha_alta": "2024-01-01",
            "regimen": "",
            "estado": "Alta",
            "piso_id": None,
        },
        "piso": {
            "direccion": piso_dir,
            "municipio": "",
            "cp": None,
            "n_personas": None,
            "inmobiliaria": "",
            "propiedad": "",
            "prop_vertical": "",
            "fecha_firma": None,
            "bloque_id": None,
        },
        "bloque": {"direccion": short_address(piso_dir)},
        "facturacion": {
            "cuota": 0.0,
            "periodicidad": 1,
            "forma_pago": "Otro",
            "iban": None,
            "afiliada_id": None,
        },
        "meta": {"bloque": None, "bloque_manual": None},
        "validation": {"is_valid": True, "errors": []},
        "ui_updaters": {},
    }


@pytest.mark.asyncio
async def test_sort_by_text_and_status(view):
    view.state.set_records([
        _make_record("Álvaro", "Zeta", "Calle Uno 1"),
        _make_record("beatriz", "Alfa", "Calle Dos 2"),
    ])

    # Sort by nombre (accent-insensitive, case-insensitive)
    view._sort_by_column("nombre")
    assert view.state.records[0]["afiliada"]["nombre"].lower().startswith("álvaro")
    # Toggle sort direction
    view._sort_by_column("nombre")
    assert view.state.records[0]["afiliada"]["nombre"].lower().startswith("beatriz")

    # Sort by status (False before True on first toggle)
    view.state.records[0]["validation"]["is_valid"] = False
    view.state.records[1]["validation"]["is_valid"] = True
    view._sort_by_column("is_valid")
    assert view.state.records[0]["validation"]["is_valid"] is False


@pytest.mark.asyncio
async def test_threshold_applies_and_reverts_preview(view):
    rec = _make_record("Ana", "Beta", "Calle de Prueba 10, 1ºA, Madrid")
    view.state.set_records([rec])

    # Low threshold -> suggestion appears and fills preview direccion
    await view._on_score_limit_change(0.6)
    assert rec["meta"]["bloque"] is not None
    assert rec["bloque"]["direccion"] == "Calle de Prueba 10"

    # Increase threshold -> suggestion disappears and preview reverts
    await view._on_score_limit_change(0.9)
    assert rec["meta"]["bloque"] is None
    assert rec["bloque"]["direccion"] == short_address(rec["piso"]["direccion"])  # baseline


@pytest.mark.asyncio
async def test_apply_and_clear_link(view):
    rec = _make_record("Ana", "Beta", "Calle de Prueba 10, 1ºA, Madrid")
    view.state.set_records([rec])

    # Prepare a suggestion
    await view._on_score_limit_change(0.6)
    assert rec["meta"]["bloque"] is not None

    # Vincular should set bloque_id and mirror address
    view._apply_suggested_bloque(rec)
    assert rec["piso"]["bloque_id"] == 1001
    assert rec["bloque"]["direccion"] == "Calle de Prueba 10"

    # Limpiar should clear link and restore baseline address
    view._clear_bloque_assignment(rec)
    assert rec["piso"]["bloque_id"] is None
    assert rec["bloque"]["direccion"] == short_address(rec["piso"]["direccion"])  # baseline


def test_reset_bloques_entries(view):
    r1 = _make_record("A", "B", "Calle Uno 1, 2º")
    r2 = _make_record("C", "D", "Calle Dos 2, 3º")
    view.state.set_records([r1, r2])

    # Simulate one linked record
    r1["piso"]["bloque_id"] = 999
    r1["bloque"]["direccion"] = "Some Block"

    view._reset_bloques_entries()
    for rec in (r1, r2):
        assert rec["piso"]["bloque_id"] is None
        assert rec["bloque"]["direccion"] == short_address(rec["piso"]["direccion"])  # baseline

