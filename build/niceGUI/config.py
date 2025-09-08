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
    "entramado_empresas": {
        "display_name": "Entramado de Empresas",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": ["nombre", "descripcion"],
        "child_relations": [
            {"table": "empresas", "foreign_key": "entramado_id"},
        ],
    },
    "nodos": {
        "display_name": "Nodos Territoriales",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": ["nombre", "descripcion"],
        "child_relations": [
            {"table": "nodos_cp_mapping", "foreign_key": "nodo_id"},
            {"table": "bloques", "foreign_key": "nodo_id"},
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
            "roles",
            "is_active",
            "created_at",
        ],
        "child_relations": [
            {"table": "usuario_credenciales", "foreign_key": "usuario_id"},
            {"table": "usuario_roles", "foreign_key": "usuario_id"},
            {"table": "asesorias", "foreign_key": "tecnica_id"},
            {"table": "conflictos", "foreign_key": "usuario_responsable_id"},
            {"table": "diario_conflictos", "foreign_key": "usuario_id"},
        ],
    },
    "nodos_cp_mapping": {
        "display_name": "Mapeo CP-Nodos",
        "id_field": "cp",
        "hidden_fields": [],
        "fields": ["cp", "nodo_id"],
        "relations": {"nodo_id": {"view": "nodos", "display_field": "nombre"}},
    },
    "empresas": {
        "display_name": "Empresas",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": [
            "nombre",
            "cif_nif_nie",
            "directivos",
            "api",
            "direccion_fiscal",
            "entramado_id",
        ],
        "relations": {
            "entramado_id": {"view": "entramado_empresas", "display_field": "nombre"}
        },
        "child_relations": [
            {"table": "bloques", "foreign_key": "empresa_id"},
        ],
    },
    "usuario_credenciales": {
        "display_name": "Credenciales de Usuario",
        "id_field": "usuario_id",
        "hidden_fields": ["password_hash"],  # Hide sensitive data
        "fields": ["usuario_id", "password_hash"],
        "relations": {"usuario_id": {"view": "usuarios", "display_field": "alias"}},
    },
    "usuario_roles": {
        "display_name": "Roles Asignados",
        "id_field": "usuario_id,role_id",  # Composite key
        "hidden_fields": [],
        "fields": ["usuario_id", "role_id"],
        "relations": {
            "usuario_id": {"view": "usuarios", "display_field": "alias"},
            "role_id": {"view": "roles", "display_field": "nombre"},
        },
    },
    "bloques": {
        "display_name": "Bloques",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": ["direccion", "estado", "api", "empresa_id", "nodo_id"],
        "relations": {
            "empresa_id": {"view": "empresas", "display_field": "nombre"},
            "nodo_id": {"view": "nodos", "display_field": "nombre"},
        },
        "child_relations": [
            {"table": "pisos", "foreign_key": "bloque_id"},
        ],
    },
    "pisos": {
        "display_name": "Pisos",
        "id_field": "id",
        "hidden_fields": ["id"],
        "fields": [
            "direccion",
            "municipio",
            "cp",
            "api",
            "prop_vertical",
            "por_habitaciones",
            "bloque_id",
        ],
        "relations": {"bloque_id": {"view": "bloques", "display_field": "direccion"}},
        "child_relations": [
            {"table": "afiliadas", "foreign_key": "piso_id"},
        ],
    },
    "afiliadas": {
        "display_name": "Afiliadas",
        "id_field": "id",
        "hidden_fields": [
            "id",
            "seccion_sindical",
            "nivel_participacion",
            "comision",
            "cuota",
            "frecuencia_pago",
            "forma_pago",
            "cuenta_corriente",
            "prop_vertical",
            "api",
            "propiedad",
            "entramado",
        ],
        "fields": [
            "num_afiliada",
            "nombre",
            "apellidos",
            "cif",
            "genero",
            "email",
            "telefono",
            "regimen",
            "estado",
            "fecha_alta",
            "fecha_baja",
            "piso_id",
        ],
        "relations": {"piso_id": {"view": "pisos", "display_field": "direccion"}},
        "child_relations": [
            {"table": "facturacion", "foreign_key": "afiliada_id"},
            {"table": "asesorias", "foreign_key": "afiliada_id"},
            {"table": "conflictos", "foreign_key": "afiliada_id"},
        ],
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
        "hidden_fields": ["id"],
        "fields": [
            "estado",
            "ambito",
            "causa",
            "tarea_actual",
            "fecha_apertura",
            "fecha_cierre",
            "descripcion",
            "resolucion",
            "afiliada_id",
            "usuario_responsable_id",
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
        "hidden_fields": ["id", "entramado_id", "empresa_id", "nodo_id"],
    },
    "v_afiliadas_detalle": {
        "display_name": "Detalle de Afiliadas",
        "base_table": "afiliadas",
        "hidden_fields": ["id", "entramado_id", "empresa_id", "nodo_id"],
    },
    "v_conflictos_detalle": {
        "display_name": "Detalle de Conflictos",
        "base_table": "conflictos",
        "hidden_fields": ["id", "entramado_id", "empresa_id", "nodo_id"],
    },
    "v_diario_conflictos_con_afiliada": {
        "display_name": "Historial de Conflictos (Diario)",
        "base_table": "diario_conflictos",
        "hidden_fields": ["id", "entramado_id", "empresa_id", "nodo_id"],
    },
    "comprobar_link_pisos_bloques": {"display_name": "Comprobar Vínculo Pisos-Bloques"},
}

config = Config()
