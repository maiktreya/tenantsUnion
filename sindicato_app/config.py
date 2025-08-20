from dataclasses import dataclass
import os

@dataclass
class Config:
    API_BASE_URL: str = os.environ.get("POSTGREST_API_URL", "http://localhost:3001")
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8081
    APP_TITLE: str = "Gestión Sindicato INQ"
    PAGE_SIZE_OPTIONS: list = None

    def __post_init__(self):
        if self.PAGE_SIZE_OPTIONS is None:
            self.PAGE_SIZE_OPTIONS = [5, 10, 25, 50, 100]

# =====================================================================
#  TABLE & RELATIONSHIP METADATA
# =====================================================================
# This dictionary drives the behavior of the entire Enhanced CRUD view.
# It defines not only the tables but also how they relate to each other.
# Now supports multiple child_relations per table.

TABLE_INFO = {
    "entramado_empresas": {
        "display_name": "Entramado Empresas",
        "id_field": "id",
        "child_relations": {"table": "empresas", "foreign_key": "entramado_id"},
    },
    "empresas": {
        "display_name": "Empresas",
        "id_field": "id",
        "relations": {
            "entramado_id": {"view": "entramado_empresas", "display_field": "nombre"}
        },
        "child_relations": {"table": "bloques", "foreign_key": "empresa_id"},
    },
    "bloques": {
        "display_name": "Bloques",
        "id_field": "id",
        "relations": {"empresa_id": {"view": "empresas", "display_field": "nombre"}},
        "child_relations": {"table": "pisos", "foreign_key": "bloque_id"},
    },
    "pisos": {
        "display_name": "Pisos",
        "id_field": "id",
        "relations": {"bloque_id": {"view": "bloques", "display_field": "direccion"}},
        "child_relations": {"table": "afiliadas", "foreign_key": "piso_id"},
    },
    "usuarios": {
        "display_name": "Usuarios",
        "id_field": "id",
        "child_relations": {"table": "asesorias", "foreign_key": "tecnica_id"},
    },
    "afiliadas": {
        "display_name": "Afiliadas",
        "id_field": "id",
        "relations": {"piso_id": {"view": "pisos", "display_field": "direccion"}},
        "child_relations": {"table": "facturacion", "foreign_key": "afiliada_id"},
    },
    "facturacion": {
        "display_name": "Facturación",
        "id_field": "id",
        "relations": {"afiliada_id": {"view": "afiliadas", "display_field": "nombre"}},
    },
    "asesorias": {
        "display_name": "Asesorías",
        "id_field": "id",
        "relations": {
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre"},
            "tecnica_id": {"view": "usuarios", "display_field": "alias"},
        },
    },
    "conflictos": {
        "display_name": "Conflictos",
        "id_field": "id",
        "relations": {
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre"},
            "usuario_responsable_id": {"view": "usuarios", "display_field": "alias"},
        },
        "child_relations": {"table": "diario_conflictos", "foreign_key": "conflicto_id"},
    },
    "diario_conflictos": {
        "display_name": "Diario Conflictos",
        "id_field": "id",
        "relations": {
            "conflicto_id": {"view": "conflictos", "display_field": "descripcion"},
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre"},
        },
        # Only allow diario_conflictos if the associated conflicto has afiliada_id not null.
        # When adding, set ambito = "Afiliada" by default if afiliada_id is not null.
    },
    "solicitudes": {"display_name": "Solicitudes", "id_field": "id"},
}

# =====================================================================
#  MATERIALIZED VIEW METADATA
# =====================================================================
VIEW_INFO = {
    "v_afiliadas": {"display_name": "Info completa de Afiliadas"},
    "v_bloques": {"display_name": "Info de Bloques"},
    "v_empresas": {"display_name": "Info completa de Empresas"},
}

config = Config()