# build/niceGUI/config.py

from dataclasses import dataclass
import os


@dataclass
class Config:
    """Application configuration settings."""

    API_BASE_URL: str = os.environ.get("POSTGREST_API_URL", "http://localhost:3001")
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8081
    APP_TITLE: str = "Gestión Sindicato de Inquilinas de Madrid"
    PAGE_SIZE_OPTIONS: list = None

    def __post_init__(self):
        if self.PAGE_SIZE_OPTIONS is None:
            self.PAGE_SIZE_OPTIONS = [5, 10, 25, 50, 100]


# =====================================================================
#  TABLE & RELATIONSHIP METADATA (ENHANCED FOR MULTI-LEVEL EXPLORATION)
# =====================================================================

# This configuration object is the single source of truth for the application's
# understanding of the database schema. It drives UI generation, validation,
# and relationship exploration.

TABLE_INFO = {
    "entramado_empresas": {
        "display_name": "Entramado de Empresas",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": ["nombre", "descripcion"],
        "child_relations": [
            {"table": "empresas", "foreign_key": "entramado_id"},
        ],
    },
    "empresas": {
        "display_name": "Empresas",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": [
            "nombre",
            "cif_nif_nie",
            "directivos",
            "direccion_fiscal",
            "entramado_id",
            "url_notas",
        ],
        "relations": {
            "entramado_id": {"view": "entramado_empresas", "display_field": "nombre"}
        },
        "child_relations": [
            {"table": "bloques", "foreign_key": "empresa_id"},
        ],
    },
    "bloques": {
        "display_name": "Bloques",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": ["direccion", "empresa_id"],
        "relations": {
            "empresa_id": {"view": "empresas", "display_field": "nombre"}
        },
        "child_relations": [
            {
                "table": "pisos",
                "foreign_key": "bloque_id",
                "child_relations": [{"table": "afiliadas", "foreign_key": "piso_id"}],
            },
        ],
    },
    "pisos": {
        "display_name": "Pisos",
        "id_field": "id",
        "hidden_fields": [
            "id",
            "por_habitaciones",
            "inmobiliaria",
            "bloque_id",
            "vpo",
            "vpo_date",
            "propiedad",
            "prop_vertical",
            "n_personas",
            "fecha_firma",
        ],
        "fields": [
            "direccion",
            "municipio",
            "cp",
        ],
        "relations": {
            "bloque_id": {
                "view": "bloques",
                "display_field": "direccion",
                "relations": {
                    "empresa_id": {"view": "empresas", "display_field": "nombre"}
                },
            }
        },
        "child_relations": [
            {"table": "afiliadas", "foreign_key": "piso_id"},
        ],
    },
    "afiliadas": {
        "display_name": "Afiliadas",
        "id_field": "id",
        "hidden_fields": ["id", "nivel_participacion"],
        "fields": [
            "piso_id",
            "num_afiliada",
            "nombre",
            "apellidos",
            "cif",
            "fecha_nac",
            "genero",
            "email",
            "telefono",
            "estado",
            "regimen",
            "fecha_alta",
            "fecha_baja",
        ],
        "relations": {
            "piso_id": {
                "view": "pisos",
                "display_field": "direccion",
                "label_template": "[{id}] {direccion}",
                "search_fields": ["direccion", "municipio", "cp", "id"],
                "options_limit": 5000,
                "order_by": "direccion",
                "value_field": "id",
            }
        },
        "child_relations": [
            {"table": "facturacion", "foreign_key": "afiliada_id"},
            {"table": "asesorias", "foreign_key": "afiliada_id"},
            {"table": "conflictos", "foreign_key": "afiliada_id"},
        ],
    },
    "nodos": {
        "display_name": "Nodos Territoriales",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": ["nombre", "descripcion"],
        "child_relations": [
            {"table": "nodos_cp_mapping", "foreign_key": "nodo_id"},
        ],
    },
    "roles": {
        "display_name": "Roles de Usuario",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": ["nombre", "descripcion"],
        "child_relations": [
            {"table": "usuario_roles", "foreign_key": "role_id"},
        ],
    },
    "usuarios": {
        "display_name": "Usuarios",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": [
            "alias",
            "nombre",
            "apellidos",
            "email",
            "is_active",
            "created_at",
        ],
        "child_relations": [
            {"table": "usuario_credenciales", "foreign_key": "usuario_id"},
            {"table": "usuario_roles", "foreign_key": "usuario_id"},
            {"table": "asesorias", "foreign_key": "tecnica_id"},
            {"table": "diario_conflictos", "foreign_key": "usuario_id"},
            {"table": "nodos", "foreign_key": "usuario_responsable_id"},
        ],
    },
    "nodos_cp_mapping": {
        "display_name": "Mapeo CP-Nodos",
        "id_field": "cp,nodo_id",
        "hidden_fields": [],
        "fields": ["cp", "nodo_id"],
        "relations": {"nodo_id": {"view": "nodos", "display_field": "nombre"}},
    },
    "usuario_credenciales": {
        "display_name": "Credenciales de Usuario",
        "id_field": "usuario_id",
        "hidden_fields": ["password_hash"],
        "fields": ["usuario_id", "password_hash"],
        "relations": {"usuario_id": {"view": "usuarios", "display_field": "alias"}},
    },
    "usuario_roles": {
        "display_name": "Roles Asignados",
        "id_field": "usuario_id,role_id",
        "hidden_fields": [],
        "fields": ["usuario_id", "role_id"],
        "relations": {
            "usuario_id": {"view": "usuarios", "display_field": "alias"},
            "role_id": {"view": "roles", "display_field": "nombre"},
        },
    },
    "asesorias": {
        "display_name": "Asesorías",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": [
            "estado",
            "fecha_asesoria",
            "tipo_beneficiaria",
            "tipo",
            "resultado",
            "afiliada_id",
            "tecnica_id",
        ],
        "relations": {
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre,apellidos"},
            "tecnica_id": {"view": "usuarios", "display_field": "alias"},
        },
    },
    "conflictos": {
        "display_name": "Conflictos",
        "id_field": "id",
        "hidden_fields": ["id", "fecha_cierre", "estado", "tarea_actual", "resolucion"],
        "fields": [
            "ambito",
            "causa",
            "fecha_apertura",
            "descripcion",
            "afiliada_id",
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
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre,apellidos"}
        },
        "child_relations": [
            {"table": "diario_conflictos", "foreign_key": "conflicto_id"},
        ],
    },
    "diario_conflictos": {
        "display_name": "Diario de Conflictos",
        "id_field": "id",
        "hidden_fields": ["id", "created_at"],
        "fields": [
            "estado",
            "accion",
            "notas",
            "tarea_actual",
            "conflicto_id",
            "usuario_id",
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
    "facturacion": {
        "display_name": "Facturación",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": ["cuota", "periodicidad", "forma_pago", "iban", "afiliada_id"],
        "relations": {
            "afiliada_id": {"view": "afiliadas", "display_field": "nombre,apellidos"}
        },
        "field_patterns": {
            "iban": {
                "regex": "^ES[0-9]{22}$",
                "error_message": "El IBAN debe tener el formato español (ej: ES0012345678901234567890).",
            }
        },
    },
}

# =====================================================================
#  MATERIALIZED VIEW METADATA
# =====================================================================
VIEW_INFO = {
    "v_resumen_nodos": {"display_name": "Resumen de Nodos", "base_table": "nodos"},
    "v_resumen_bloques": {
        "display_name": "Resumen de Bloques",
        "base_table": "bloques",
        "hidden_fields": ["id", "empresa_id", "nodo_id"],
    },
    "v_resumen_entramados_empresas": {
        "display_name": "Resumen de Entramados",
        "base_table": "entramado_empresas",
        "hidden_fields": ["id", "entramado_id", "empresa_id", "nodo_id"],
    },
    "v_afiliadas_detalle": {
        "display_name": "Detalle de Afiliadas",
        "base_table": "afiliadas",
        "hidden_fields": ["id", "piso_id", "entramado_id", "empresa_id", "nodo_id"],
    },
    "v_conflictos_detalle": {
        "display_name": "Detalle de Conflictos",
        "base_table": "conflictos",
        "hidden_fields": ["id", "entramado_id", "empresa_id", "nodo_id"],
    },
    "comprobar_link_pisos_bloques": {
        "display_name": "Comprobar Vínculo Pisos-Bloques",
        "base_table": "pisos",
    },
    "v_facturacion": {
        "display_name": "Vista extendida de facturación",
        "base_table": "afiliadas",
        "hidden_fields": ["id"],
    },
    "v_consolidar_pisos_bloques": {
        "display_name": "Vista consolidada de Pisos-Bloques",
        "base_table": "pisos",
        "hidden_fields": ["id"],
    },
}

# =====================================================================
#  UI METADATA (HEADER MAPPINGS)
# =====================================================================
IMPORTER_HEADER_MAP = {
    "nombre": "Nombre",
    "apellidos": "Apellidos",
    "cif": "CIF/NIE",
    "email": "Email",
    "telefono": "Teléfono",
    "direccion": "Dirección",
    "municipio": "Municipio",
    "cp": "CP",
    "fecha_nac": "Fecha Nacimiento",
    "propiedad": "Propiedad",
    "prop_vertical": "Prop. Vertical",
    "fecha_alta": "Fecha Alta",
    "n_personas": "Nº Personas",
    "inmobiliaria": "Inmobiliaria",
    "cuota": "Cuota (€)",
    "periodicidad": "Periodicidad (m)",
    "forma_pago": "Forma Pago",
    "iban": "IBAN",
    "bloque_id": "Bloque sugerido",
}
# =====================================================================
#  AFILIADAS IMPORTER VIEW VALIDATION CONFIG
# =====================================================================
FAILED_EXPORT_FIELD_MAP = {
    "afiliada": [
        "nombre",
        "apellidos",
        "cif",
        "telefono",
        "email",
        "fecha_nac",
        "regimen",
    ],
    "piso": [
        "direccion",
        "municipio",
        "cp",
        "bloque_id",
        "n_personas",
        "inmobiliaria",
        "propiedad",
        "prop_vertical",
        "fecha_firma",
    ],
    "bloque": [
        "direccion",
    ],
    "facturacion": [
        "cuota",
        "periodicidad",
        "forma_pago",
        "iban",
    ],
}
DUPLICATE_NIF_WARNING = "La afiliada con este NIF ya existe en el sistema."

config = Config()
