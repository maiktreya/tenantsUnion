from dataclasses import dataclass
import os


@dataclass
class Config:
    """Application configuration settings."""
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
# This dictionary is the engine for the Enhanced CRUD view.
# It defines table relationships to automatically generate dropdowns for foreign keys.
# - 'relations': Defines parent relationships (foreign keys in this table).
# - 'child_relations': Defines child relationships (tables that have a foreign key to this table).

TABLE_INFO = {
    "entramado_empresas": {
        "display_name": "Entramado de Empresas",
        "id_field": "id",
        "child_relations": {"table": "empresas", "foreign_key": "entramado_id"},
    },
    "empresas": {
        "display_name": "Empresas",
        "id_field": "id",
        "relations": {
            # This table has a foreign key 'entramado_id' to 'entramado_empresas'.
            "entramado_id": {"view": "entramado_empresas", "display_field": "nombre"}
        },
        "child_relations": {"table": "bloques", "foreign_key": "empresa_id"},
    },
    "bloques": {
        "display_name": "Bloques",
        "id_field": "id",
        "relations": {
            # This table has a foreign key 'empresa_id' to 'empresas'.
            "empresa_id": {"view": "empresas", "display_field": "nombre"}
        },
        "child_relations": {"table": "pisos", "foreign_key": "bloque_id"},
    },
    "pisos": {
        "display_name": "Pisos",
        "id_field": "id",
        "relations": {
            # This table has a foreign key 'bloque_id' to 'bloques'.
            "bloque_id": {"view": "bloques", "display_field": "direccion"}
        },
        "child_relations": {"table": "afiliadas", "foreign_key": "piso_id"},
    },
    "usuarios": {
        "display_name": "Usuarios",
        "id_field": "id",
        # Users can be related to multiple other tables as children.
        "child_relations": [
            {"table": "asesorias", "foreign_key": "tecnica_id"},
            {"table": "conflictos", "foreign_key": "usuario_responsable_id"},
        ]
    },
    "afiliadas": {
        "display_name": "Afiliadas",
        "id_field": "id",
        "relations": {
            # This table has a foreign key 'piso_id' to 'pisos'.
            "piso_id": {"view": "pisos", "display_field": "direccion"}
        },
        # 'Afiliadas' can be parents to multiple other records.
        "child_relations": [
            {"table": "facturacion", "foreign_key": "afiliada_id"},
            {"table": "asesorias", "foreign_key": "afiliada_id"},
            {"table": "conflictos", "foreign_key": "afiliada_id"},
        ]
    },
    "facturacion": {
        "display_name": "Facturación",
        "id_field": "id",
        "relations": {
            # This table has a foreign key 'afiliada_id' to 'afiliadas'.
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre"}
        },
    },
    "asesorias": {
        "display_name": "Asesorías",
        "id_field": "id",
        "relations": {
            # This table has foreign keys to both 'afiliadas' and 'usuarios'.
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre"},
            "tecnica_id": {"view": "usuarios", "display_field": "alias"},
        },
    },
    "conflictos": {
        "display_name": "Conflictos",
        "id_field": "id",
        "relations": {
            # This table is linked to both 'afiliadas' and 'usuarios'.
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre"},
            "usuario_responsable_id": {"view": "usuarios", "display_field": "alias"},
        },
        "child_relations": {
            "table": "diario_conflictos",
            "foreign_key": "conflicto_id",
        },
    },
    "diario_conflictos": {
        "display_name": "Diario de Conflictos",
        "id_field": "id",
        "relations": {
            # A journal entry belongs to a single conflict.
            "conflicto_id": {"view": "conflictos", "display_field": "descripcion"},
            # ENHANCEMENT: Added this relation based on the 'ConflictNoteDialog' logic,
            # which allows associating a journal entry with an 'afiliada'.
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre"},
        },
        # FIX: Removed the incorrect 'child_relations' that created a circular dependency.
        # A journal entry is a child and cannot be a parent to the main 'conflictos' table.
    },
    "solicitudes": {
        "display_name": "Solicitudes",
        "id_field": "id"
        # No relations are defined as its structure is simple.
    },
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