from dataclasses import dataclass
from typing import Dict

@dataclass
class Config:
    API_BASE_URL: str = "http://localhost:3001"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8081
    APP_TITLE: str = "Gestión Sindicato INQ"
    PAGE_SIZE_OPTIONS: list = None

    def __post_init__(self):
        if self.PAGE_SIZE_OPTIONS is None:
            self.PAGE_SIZE_OPTIONS = [5, 10, 25, 50, 100]

# Table and view metadata
TABLE_INFO = {
    'entramado_empresas': {'display_name': 'Entramado Empresas', 'id_field': 'id'},
    'empresas': {'display_name': 'Empresas', 'id_field': 'id'},
    'bloques': {'display_name': 'Bloques', 'id_field': 'id'},
    'pisos': {'display_name': 'Pisos', 'id_field': 'id'},
    'usuarios': {'display_name': 'Usuarios', 'id_field': 'id'},
    'afiliadas': {'display_name': 'Afiliadas', 'id_field': 'id'},
    'facturacion': {'display_name': 'Facturación', 'id_field': 'id'},
    'asesorias': {'display_name': 'Asesorías', 'id_field': 'id'},
    'conflictos': {'display_name': 'Conflictos', 'id_field': 'id'},
    'diario_conflictos': {'display_name': 'Diario Conflictos', 'id_field': 'id'}
}

VIEW_INFO = {
    'vista_conflictos_activos': {'display_name': 'Conflictos Activos'},
    'vista_resumen_facturacion_empresa': {'display_name': 'Resumen de Facturación por Empresa'},
    'vista_usuarios_afiliados': {'display_name': 'Usuarios Afiliados'},
}

config = Config()