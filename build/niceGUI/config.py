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
# 'hidden_fields' key is added to specify which columns to hide from UI cards.

TABLE_INFO = {
    "nodos": {
        "display_name": "Nodos Territoriales",
        "id_field": "id",
        "hidden_fields": ["id"],
        "child_relations": [
            {"table": "nodos_cp_mapping", "foreign_key": "nodo_id"},
            {"table": "bloques", "foreign_key": "nodo_id"},
        ],
    },
    "nodos_cp_mapping": {
        "display_name": "Mapeo CP-Nodos",
        "id_field": "cp",
        "hidden_fields": ["cp"],
        "relations": {"nodo_id": {"view": "nodos", "display_field": "nombre"}},
    },
    "entramado_empresas": {
        "display_name": "Entramado de Empresas",
        "id_field": "id",
        "hidden_fields": ["id"],
        "child_relations": {"table": "empresas", "foreign_key": "entramado_id"},
    },
    "empresas": {
        "display_name": "Empresas",
        "id_field": "id",
        "hidden_fields": ["id"],
        "relations": {
            "entramado_id": {"view": "entramado_empresas", "display_field": "nombre"}
        },
        "child_relations": {"table": "bloques", "foreign_key": "empresa_id"},
    },
    "bloques": {
        "display_name": "Bloques",
        "id_field": "id",
        "hidden_fields": ["id"],
        "relations": {
            "empresa_id": {"view": "empresas", "display_field": "nombre"},
            "nodo_id": {"view": "nodos", "display_field": "nombre"},
        },
        "child_relations": {"table": "pisos", "foreign_key": "bloque_id"},
    },
    "pisos": {
        "display_name": "Pisos",
        "id_field": "id",
        "hidden_fields": ["id"],
        "relations": {"bloque_id": {"view": "bloques", "display_field": "direccion"}},
        "child_relations": {"table": "afiliadas", "foreign_key": "piso_id"},
    },
    "usuarios": {
        "display_name": "Usuarios",
        "id_field": "id",
        "hidden_fields": ["id"],
        "child_relations": [
            {"table": "asesorias", "foreign_key": "tecnica_id"},
            {"table": "conflictos", "foreign_key": "usuario_responsable_id"},
            {"table": "usuario_credenciales", "foreign_key": "usuario_id"},
            {"table": "usuario_roles", "foreign_key": "usuario_id"},
            {"table": "diario_conflictos", "foreign_key": "usuario_id"},
        ],
    },
    "roles": {
        "display_name": "Roles de Usuario",
        "id_field": "id",
        "hidden_fields": ["id"],
        "child_relations": {"table": "usuario_roles", "foreign_key": "role_id"},
    },
    "usuario_roles": {
        "display_name": "Roles Asignados",
        "id_field": "usuario_id,role_id",
        "hidden_fields": [],  # No primary key to hide visually
        "relations": {
            "usuario_id": {"view": "usuarios", "display_field": "alias"},
            "role_id": {"view": "roles", "display_field": "nombre"},
        },
    },
    "usuario_credenciales": {
        "display_name": "Credenciales de Usuario",
        "id_field": "usuario_id",
        "hidden_fields": ["usuario_id", "password_hash"],  # Hide sensitive data
        "relations": {"usuario_id": {"view": "usuarios", "display_field": "alias"}},
    },
    "afiliadas": {
        "display_name": "Afiliadas",
        "id_field": "id",
        "hidden_fields": ["id"],
        "relations": {"piso_id": {"view": "pisos", "display_field": "direccion"}},
        "child_relations": [
            {"table": "facturacion", "foreign_key": "afiliada_id"},
            {"table": "asesorias", "foreign_key": "afiliada_id"},
            {"table": "conflictos", "foreign_key": "afiliada_id"},
        ],
    },
    "facturacion": {
        "display_name": "Facturación",
        "id_field": "id",
        "hidden_fields": ["id"],
        "relations": {
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre,apellidos"}
        },
    },
    "asesorias": {
        "display_name": "Asesorías",
        "id_field": "id",
        "hidden_fields": ["id"],
        "relations": {
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre,apellidos"},
            "tecnica_id": {"view": "usuarios", "display_field": "alias"},
        },
    },
    "conflictos": {
        "display_name": "Conflictos",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": [
            "afiliada_id",
            "usuario_responsable_id",
            "estado",
            "ambito",
            "causa",
            "tarea_actual",
            "fecha_apertura",
            "descripcion",
            "resolucion",
            "fecha_cierre",
        ],
        "field_options": {
            "estado": sorted(["Abierto", "En proceso", "Resuelto", "Cerrado"]),
            "ambito": ["Afiliada", "Bloque", "Entramado", "Agrupación de Bloques"],
            "causa": sorted(
                [
                    "No renovación",
                    "Fianza",
                    "Acoso inmobiliario",
                    "Renta Antigua",
                    "Subida de alquiler",
                    "Individualización Calefacción",
                    "Reparaciones / Habitabilidad",
                    "Venta de la vivienda",
                    "Honorarios",
                    "Requerimiento de la casa para uso propio",
                    "Impago",
                    "Actualización del precio (IPC)",
                    "Negociación del contrato",
                ]
            ),
        },
        "relations": {
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre,apellidos"},
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
        "hidden_fields": ["id"],  # Hide the old foreign key field
        "fields": [
            "conflicto_id",
            "usuario_id",
            "accion",
            "notas",
            "tarea_actual",
        ],
        "field_options": {
            "estado": sorted(["Abierto", "En proceso", "Resuelto", "Cerrado"]),
            "accion": sorted(
                [
                    "nota simple",
                    "nota localización propiedades",
                    "deposito fianza",
                    "puerta a puerta",
                    "comunicación enviada",
                    "llamada",
                    "acción",
                    "reunión de negociación",
                    "informe vulnerabilidad",
                    "MASC",
                    "justicia gratuita",
                    "demanda",
                    "sentencia",
                ]
            ),
        },
        "relations": {
            "conflicto_id": {"view": "conflictos", "display_field": "id"},
            "usuario_id": {"view": "usuarios", "display_field": "alias"},
        },
    },
}

# =====================================================================
#  MATERIALIZED VIEW METADATA
# =====================================================================
VIEW_INFO = {
    "v_resumen_nodos": {"display_name": "Resumen de Nodos", "base_table": "nodos"},
    "v_resumen_entramados_empresas": {
        "display_name": "Resumen de Entramados",
        "base_table": "entramado_empresas",
    },
    "v_afiliadas_detalle": {
        "display_name": "Detalle de Afiliadas",
        "base_table": "afiliadas",
    },
    "v_conflictos_detalle": {
        "display_name": "Detalle de Conflictos",
        "base_table": "conflictos",
    },
    "v_diario_conflictos_con_afiliada": {
        "display_name": "Historial de Conflictos (Diario)",
        "base_table": "diario_conflictos",
    },
    "comprobar_link_pisos_bloques": {"display_name": "Comprobar Vínculo Pisos-Bloques"},
}

config = Config()
