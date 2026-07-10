import logging
from typing import Dict, Any, List, Optional
from nicegui import ui, events, app

from api.client import APIClient
from services.relational_import_service import MultiTableImportService
from components.upload_event_utils import read_upload_event_bytes

log = logging.getLogger(__name__)

class GenericRelationalImporterView:
    """
    Una vista guiada por configuración. Genera documentación técnica de campos
    y plantillas CSV vacías directamente a partir de esquemas declarativos.
    """
    def __init__(self, api_client: APIClient, schema_config: Dict[str, Any]):
        self.api = api_client
        self.service = MultiTableImportService(api_client, schema_config)
        
        # Seguimiento en memoria por pestaña de cliente (sesión de navegador)
        if "generic_importer_records" not in app.storage.client:
            app.storage.client["generic_importer_records"] = []
            
        self.raw_records: List[Dict[str, Any]] = app.storage.client["generic_importer_records"]
        self.import_button: Optional[ui.button] = None
        self.summary_log: Optional[ui.log] = None

        # ---- NÚCLEO DE INTROSPECCIÓN DINÁMICA DE CABECERAS ----
        self.required_headers: List[str] = []
        for table, field_map in self.service.table_mappings.items():
            for db_col, csv_header in field_map.items():
                if not str(csv_header).startswith("__fk__") and csv_header not in self.required_headers:
                    self.required_headers.append(csv_header)

        # Campos considerados estrictamente obligatorios por el modelo de negocio
        self.mandatory_fields = {
            "direccion_vivienda_completa", 
            "nombre_afiliada", 
            "apellidos_afiliada", 
            "dni_nie", 
            "cuota", 
            "periodicidad",
            "propiedad_vertical"
        }

        # Diccionario explicativo en castellano para la documentación interactiva
        self.field_descriptions: Dict[str, str] = {
            "direccion_bloque": "Dirección general de la finca (Opcional. Dejar vacío si se alquila a un particular sin bloque corporativo).",
            "empresa_propietaria": "Nombre de la empresa rentista dueña del inmueble (Opcional. Volca en texto libre a pisos.propiedad).",
            "direccion_vivienda_completa": "Dirección exacta del piso incluyendo puerta, planta, escalera y letra.",
            "localidad": "Municipio o ciudad donde se ubica la vivienda (Opcional).",
            "codigo_postal": "Código postal numérico oficial de 5 dígitos (Opcional).",
            "propiedad_vertical": "Indica si el edificio entero pertenece a un único dueño. Si se deja vacío, el sistema asignará 'No' automáticamente.",
            "agencia_inmobiliaria": "Nombre de la agencia intermediaria del alquiler (Opcional).",
            "alquiler_por_habitaciones": "Especificar TRUE o FALSE si el contrato es por habitaciones sueltas (Opcional).",
            "numero_de_inquilinos": "Número entero de personas que habitan el piso habitualmente (Opcional).",
            "fecha_firma_contrato": "Fecha de formalización del contrato actual (Formato AAAA-MM-DD) (Opcional).",
            "es_vpo": "TRUE o FALSE si la vivienda cuenta con protección oficial (Opcional).",
            "fecha_vencimiento_vpo": "Fecha límite de la calificación VPO (Formato AAAA-MM-DD) (Opcional).",
            "referencia_catastral": "Código oficial del catastro español de 20 caracteres (Opcional).",
            "numero_afiliada": "Código interno del sindicato identificativo de la ficha (Opcional).",
            "nombre_afiliada": "Nombre de pila de la afiliada inscrita.",
            "apellidos_afiliada": "Apellidos completos de la afiliada inscrita.",
            "dni_nie": "Documento oficial de identidad (NIF / NIE / Pasaporte) sin guiones ni espacios.",
            "fecha_nacimiento": "Fecha de nacimiento de la afiliada (Formato AAAA-MM-DD) (Opcional).",
            "genero": "Identidad de género declarada por la afiliada (Opcional).",
            "email": "Correo electrónico de contacto (Opcional).",
            "telefono": "Teléfono móvil o fijo de contacto directo (Opcional).",
            "estado_afiliada": "Estado de la ficha dentro de la organización (Alta, Baja, Bienvenida) (Opcional).",
            "regimen_arrendamiento": "Régimen legal del uso de la vivienda (Alquiler, LAU, etc.) (Opcional).",
            "cuota": "Importe numérico de la cuota asignada (ejemplo: 15.00).",
            "periodicidad": "Frecuencia de cobro obligatoria. Valores admitidos estrictamente: 1 (Mensual) o 12 (Anual).",
            "forma_pago": "Método de abono seleccionado (ejemplo: Transferencia, Efectivo) (Opcional).",
            "cuenta_bancaria_iban": "Código de cuenta bancaria internacional completo de la afiliada (formato IBAN) (Opcional)."
        }

    def create(self) -> ui.column:
        """Dibuja el espacio de trabajo con autodocumentación y subida de archivos."""
        with ui.column().classes("w-full p-4 gap-4") as container:
            # Sección de Cabecera Principal
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column():
                    ui.label(f"Importador General Relacional: {self.service.config.get('name', 'Bespoke Tooling')}").classes("text-h6")
                    ui.markdown("Sube archivos CSV estructurados con los datos de las afiliadas. El motor enlazará las tablas de forma automática.")
                
                ui.button(
                    "Descargar Plantilla Completa", 
                    icon="download_for_offline", 
                    on_click=self._download_empty_csv_template
                ).props("color=blue-grey-7 outline").tooltip("Descargar un archivo CSV vacío configurado con todas las columnas relacionales")

            # Panel de Especificaciones Técnicas (Instrucciones en Castellano)
            with ui.expansion("📋 Ver Especificaciones de las Columnas del Archivo", icon="help_outline").classes("w-full border rounded-md bg-slate-50"):
                with ui.column().classes("p-2 gap-2 w-full"):
                    ui.markdown(
                        f"El archivo CSV cargado debe contener una fila de cabecera con las siguientes **{len(self.required_headers)} columnas disponibles**. "
                        "Los nombres de las columnas deben coincidir con exactitud:"
                    )
                    
                    # Renderizado en rejilla de las directrices de los campos
                    with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 gap-3 w-full mt-2"):
                        for header in self.required_headers:
                            is_mandatory = header in self.mandatory_fields
                            badge_color = "red-9" if is_mandatory else "blue-grey-6"
                            badge_label = f"{header} (Obligatorio)" if is_mandatory else f"{header} (Opcional)"
                            
                            with ui.card().classes("p-3 bg-white border border-gray-100 shadow-sm"):
                                with ui.row().classes("items-center justify-between w-full"):
                                    ui.badge(badge_label, color=badge_color + " text-white font-mono")
                                    if header == "propiedad_vertical":
                                        ui.badge("Coercitivo 'No'", color="orange-8").tooltip("Si se deja vacío toma 'No'")
                                desc = self.field_descriptions.get(header, "Campo de datos relacionales configurado en la cadena de importación.")
                                ui.label(desc).classes("text-xs text-gray-600 mt-1")

            # Zona de Carga y Ingesta
            with ui.row().classes("w-full gap-4 items-center mt-2"):
                ui.upload(
                    on_upload=self._handle_upload_flow,
                    auto_upload=True,
                    label="Seleccionar CSV de Ingesta",
                ).props('accept=".csv"').classes("w-1/2")
                
                self.import_button = ui.button(
                    "Procesar e Insertar", icon="play_arrow", on_click=self._execute_pipeline
                ).props("color=orange-600").set_enabled(False)

            # Mapa de Ruta Visual de Inserción Relacional
            with ui.card().classes("w-full p-4"):
                ui.label("Estructura de Destino Mapeada (Orden de Inserción Automatizado)").classes("text-subtitle2 mb-2")
                with ui.row().classes("gap-2 items-center"):
                    for i, table in enumerate(self.service.execution_order):
                        if i > 0:
                            ui.icon("arrow_forward_ios", size="xs").classes("text-gray-400")
                        ui.chip(f"{table}").props("icon=lan color=blue-10 text-white")

            # Consola Logger Terminal del Pipeline
            with ui.card().classes("w-full p-2 h-64 bg-gray-50"):
                ui.label("Consola de Operaciones Directas").classes("text-caption text-gray-600 mb-1")
                self.summary_log = ui.log(max_lines=50).classes("w-full h-48 bg-white font-mono text-xs border rounded p-2")

        return container

    def _download_empty_csv_template(self):
        """
        Genera dinámicamente un archivo CSV de plantilla con dos filas fijas:
        Fila 1: Cabeceras relacionales legibles por la base de datos.
        Fila 2: Etiquetas de metadatos guía (Obligatorio / Opcional) para el usuario.
        """
        # 1. Primera fila: Nombres exactos de las columnas
        header_row = ",".join(self.required_headers) + "\n"
        
        # 2. Segunda fila: Determinar dinámicamente el estado de obligatoriedad
        meta_row_items = []
        for header in self.required_headers:
            if header in self.mandatory_fields:
                meta_row_items.append("Obligatorio")
            else:
                meta_row_items.append("Opcional")
        meta_row = ",".join(meta_row_items) + "\n"
        
        # Concatener ambas estructuras planas de texto
        csv_content = header_row + meta_row
        
        # Firma UTF-8 BOM (\xef\xbb\xbf) para asegurar la compatibilidad nativa de caracteres en Excel
        template_bytes = b"\xef\xbb\xbf" + csv_content.encode("utf-8")
        
        filename = f"plantilla_completa_afiliadas.csv"
        ui.download(template_bytes, filename)
        ui.notify("Plantilla completa con etiquetas de guía generada con éxito.", type="positive")

    async def _handle_upload_flow(self, e: events.UploadEventArguments):
        """Lee el stream de bytes, extrae cabeceras y precarga la información en memoria."""
        try:
            csv_bytes = await read_upload_event_bytes(e)
            parsed_data = await self.service.parse_csv_bytes(csv_bytes)
            
            self.raw_records.clear()
            self.raw_records.extend(parsed_data)
            
            if self.summary_log:
                self.summary_log.clear()
                self.summary_log.push(f"Archivo cargado correctamente. Registros detectados en plantilla: {len(self.raw_records)}")
                
            if self.import_button:
                self.import_button.set_enabled(len(self.raw_records) > 0)
                
            ui.notify(f"Archivo cargado: {len(self.raw_records)} registros listos para procesar.", type="info")
        except Exception as ex:
            log.error("Fallo de pre-extracción en el flujo de subida de datos", exc_info=True)
            ui.notify(f"Error procesando archivo CSV: {ex}", type="negative")

    async def _execute_pipeline(self):
        """Consume el generador asíncronico del servicio para imprimir logs en tiempo real en la interfaz."""
        if not self.raw_records:
            return
            
        if self.import_button:
            self.import_button.set_enabled(False)

        if self.summary_log:
            self.summary_log.clear()

        try:
            async for status_update in self.service.process_relational_import(self.raw_records):
                if self.summary_log:
                    self.summary_log.push(status_update)
            
            self.raw_records.clear()
            ui.notify("Proceso de carga de afiliadas finalizado con éxito.", type="positive")
        except Exception as ex:
            ui.notify(f"Fallo crítico en ejecución: {ex}", type="negative")
            if self.summary_log:
                self.summary_log.push(f"\nCRITICAL TRACEBACK: {str(ex)}")