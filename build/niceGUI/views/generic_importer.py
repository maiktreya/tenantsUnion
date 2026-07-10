# build/niceGUI/views/generic_importer.py
import asyncio
import logging
from typing import Any, Dict, List, Optional

from nicegui import app, events, ui

from api.client import APIClient
from components.data_table import DataTable
from components.dialogs import ConfirmationDialog
from components.filters import FilterPanel
from components.upload_event_utils import read_upload_event_bytes
from config import TABLE_INFO
from services.geolink_service import RATE_LIMIT_SLEEP, lookup_cadastral_data, to_ewkt_point
from services.relational_import_service import MultiTableImportService
from state.base import BaseTableState

log = logging.getLogger(__name__)

# View exposed by build/postgreSQL/init-scripts/03-init-createViews.sql.
# Columns: id, piso_id, "Dirección Piso", "Municipio", "ID Bloque Sugerido",
# "Dirección Bloque Sugerido", "Score" (already floored at score > 0.5 by the view itself).
PISOS_HUERFANOS_VIEW = "v_sugerencias_pisos_huerfanos"
COL_PISO_ID = "piso_id"
COL_BLOQUE_ID = "ID Bloque Sugerido"
COL_PISO_DIR = "Dirección Piso"
COL_SCORE = "Score"

MIN_LINK_SCORE = 0.80
MAX_LINK_SCORE = 1.00
DEFAULT_LINK_SCORE = 0.85


class GenericRelationalImporterView:
    """
    Vista guiada por configuración, dividida en tres pestañas:

      1. Importador CSV Relacional (comportamiento original, sin cambios).
      2. Vinculación automática Piso -> Bloque, basada en la vista SQL
         `v_sugerencias_pisos_huerfanos`.
      3. Enriquecimiento Geolink: relanza `pisos` sin `ref_catastral`/`coordenadas`
         contra CartoCiudad para completar esos campos.
    """

    def __init__(self, api_client: APIClient, schema_config: Dict[str, Any]):
        # ---------------------------------------------------------------
        # TAB 1: estado original, intacto.
        # ---------------------------------------------------------------
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
            "propiedad_vertical",
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
            "cuenta_bancaria_iban": "Código de cuenta bancaria internacional completo de la afiliada (formato IBAN) (Opcional).",
        }

        # ---------------------------------------------------------------
        # TAB 2: estado del vinculador automático Piso -> Bloque.
        # ---------------------------------------------------------------
        self.link_threshold: float = DEFAULT_LINK_SCORE
        self._all_link_suggestions: List[Dict[str, Any]] = []
        self.link_state = BaseTableState()
        self.link_state.page_size.set(10)
        self.link_table: Optional[DataTable] = None
        self.link_log: Optional[ui.log] = None
        self.link_execute_button: Optional[ui.button] = None

        # ---------------------------------------------------------------
        # TAB 3: estado del enriquecimiento Geolink.
        # ---------------------------------------------------------------
        self.geolink_state = BaseTableState()
        self.geolink_state.page_size.set(10)
        self.geolink_table: Optional[DataTable] = None
        self.geolink_filter_container: Optional[ui.column] = None
        self.geolink_filter_panel: Optional[FilterPanel] = None
        self.geolink_log: Optional[ui.log] = None
        self.geolink_execute_button: Optional[ui.button] = None

    def create(self) -> ui.column:
        """Construye el contenedor de pestañas y delega cada panel a su renderer."""
        with ui.column().classes("w-full") as container:
            with ui.tabs().classes("w-full border-b") as tabs:
                tab_importer = ui.tab("1. Importador CSV", icon="cloud_upload")
                tab_linker = ui.tab("2. Vinculación Piso-Bloque", icon="hub")
                tab_geolink = ui.tab("3. Enriquecimiento Geolink", icon="explore")

            with ui.tab_panels(tabs, value=tab_importer).classes("w-full bg-transparent p-0"):
                with ui.tab_panel(tab_importer):
                    self._render_generic_importer_tab()
                with ui.tab_panel(tab_linker):
                    self._render_piso_bloque_linker_tab()
                with ui.tab_panel(tab_geolink):
                    self._render_geolink_enrichment_tab()

        return container

    # =====================================================================
    # TAB 1: IMPORTADOR CSV GENÉRICO (comportamiento original, sin cambios)
    # =====================================================================
    def _render_generic_importer_tab(self):
        """Dibuja el espacio de trabajo con autodocumentación y subida de archivos."""
        with ui.column().classes("w-full p-4 gap-4"):
            # Sección de Cabecera Principal
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column():
                    ui.label(f"Importador General Relacional: {self.service.config.get('name', 'Bespoke Tooling')}").classes("text-h6")
                    ui.markdown("Sube archivos CSV estructurados con los datos de las afiliadas. El motor enlazará las tablas de forma automática.")

                ui.button(
                    "Descargar Plantilla Completa",
                    icon="download_for_offline",
                    on_click=self._download_empty_csv_template,
                ).props("color=blue-grey-7 outline").tooltip("Descargar un archivo CSV vacío configurado con todas las columnas relacionales")

            # Panel de Especificaciones Técnicas (Instrucciones en Castellano)
            with ui.expansion("📋 Ver Especificaciones de las Columnas del Archivo", icon="help_outline").classes("w-full border rounded-md bg-slate-50"):
                with ui.column().classes("p-2 gap-2 w-full"):
                    ui.markdown(
                        f"El archivo CSV cargado debe contener una fila de cabecera con las siguientes **{len(self.required_headers)} columnas disponibles**. "
                        "Los nombres de las columnas deben coincidir con exactitud:"
                    )

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
                ).props("color=orange-600").set_enabled(len(self.raw_records) > 0)

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

    def _download_empty_csv_template(self):
        header_row = ",".join(self.required_headers) + "\n"
        template_bytes = b"\xef\xbb\xbf" + header_row.encode("utf-8")
        ui.download(template_bytes, "plantilla_completa_afiliadas.csv")
        ui.notify("Plantilla completa generada y lista para descargar.", type="positive")

    async def _handle_upload_flow(self, e: events.UploadEventArguments):
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

    # =====================================================================
    # TAB 2: VINCULACIÓN AUTOMÁTICA PISO -> BLOQUE
    # =====================================================================
    def _render_piso_bloque_linker_tab(self):
        with ui.column().classes("w-full p-4 gap-4"):
            with ui.column():
                ui.label("Vinculación Automática Piso → Bloque").classes("text-h6")
                ui.markdown(
                    f"Usa la vista `{PISOS_HUERFANOS_VIEW}` (similitud de direcciones, "
                    "`pg_trgm`) para sugerir a qué bloque pertenece cada piso todavía sin "
                    "asignar, y permite vincularlos en bloque a partir de un umbral de confianza."
                ).classes("text-sm text-gray-600")

            with ui.row().classes("w-full items-center gap-4 bg-gray-50 p-4 rounded-md"):
                ui.number(
                    label="Umbral mínimo de confianza",
                    value=self.link_threshold,
                    min=MIN_LINK_SCORE,
                    max=MAX_LINK_SCORE,
                    step=0.01,
                    format="%.2f",
                    on_change=lambda e: self._on_link_threshold_change(e.value),
                ).props("dense outlined").classes("w-64")

                ui.button(
                    "Buscar Sugerencias", icon="refresh", on_click=self._load_link_suggestions
                ).props("color=blue-grey-7 outline")

                self.link_execute_button = ui.button(
                    "Vincular Automáticamente", icon="bolt", on_click=self._confirm_bulk_link
                ).props("color=positive").set_enabled(False)

            # La tabla se crea una sola vez: como referencia un objeto `state` (no una
            # copia de sus registros), basta con reasignar `state.records` y llamar a
            # `.refresh()` cada vez que cambian los datos o el umbral.
            self.link_table = DataTable(
                state=self.link_state,
                show_actions=False,
                hidden_columns=["id"],  # duplica piso_id; se oculta para evitar confusión
            )
            self.link_table.create()

            with ui.card().classes("w-full p-2 h-40 bg-gray-50"):
                ui.label("Registro de Vinculación").classes("text-caption text-gray-600 mb-1")
                self.link_log = ui.log(max_lines=50).classes("w-full h-28 bg-white font-mono text-xs border rounded p-2")

        ui.timer(0.1, self._load_link_suggestions, once=True)

    def _on_link_threshold_change(self, value: Any):
        try:
            self.link_threshold = float(value)
        except (TypeError, ValueError):
            return
        self._refresh_link_table()

    async def _load_link_suggestions(self):
        """Recarga todas las sugerencias (la vista ya filtra score > 0.5) y vuelve a aplicar el umbral local."""
        try:
            self._all_link_suggestions = await self.api.get_records(
                PISOS_HUERFANOS_VIEW, order=f"{COL_SCORE}.desc", limit=5000
            )
        except Exception as ex:
            ui.notify(f"Error al consultar sugerencias: {ex}", type="negative")
            return

        self._refresh_link_table()
        ui.notify(
            f"Se encontraron {len(self._all_link_suggestions)} sugerencias candidatas (score > 0.50).",
            type="info",
        )

    def _refresh_link_table(self):
        """Filtra las sugerencias ya cargadas por el umbral actual y refresca la tabla."""
        qualifying = [r for r in self._all_link_suggestions if (r.get(COL_SCORE) or 0) >= self.link_threshold]
        self.link_state.set_records(qualifying)
        if self.link_table:
            self.link_table.refresh()
        if self.link_execute_button:
            self.link_execute_button.set_enabled(len(qualifying) > 0)

    def _confirm_bulk_link(self):
        """Pide confirmación antes de sobrescribir `pisos.bloque_id` en bloque."""
        qualifying = self.link_state.records
        if not qualifying:
            ui.notify("No hay sugerencias que superen el umbral configurado.", type="warning")
            return

        ConfirmationDialog(
            title="Confirmar vinculación masiva",
            message=(
                f"Se vincularán {len(qualifying)} pisos a su bloque sugerido "
                f"(umbral ≥ {self.link_threshold:.2f}). Esta acción sobrescribe el campo "
                "'bloque_id' de cada piso y no se puede deshacer automáticamente."
            ),
            on_confirm=self._execute_bulk_linking,
            confirm_button_text="Vincular",
            confirm_button_color="positive",
        )

    async def _execute_bulk_linking(self):
        targets = list(self.link_state.records)
        if self.link_execute_button:
            self.link_execute_button.set_enabled(False)
        if self.link_log:
            self.link_log.clear()

        success, failed = 0, 0
        for row in targets:
            piso_id = row.get(COL_PISO_ID)
            bloque_id = row.get(COL_BLOQUE_ID)
            piso_addr = row.get(COL_PISO_DIR, piso_id)

            if piso_id is None or bloque_id is None:
                failed += 1
                if self.link_log:
                    self.link_log.push(f"✘ Fila sin piso_id/bloque_id válidos: {row}")
                continue

            result = await self.api.update_record("pisos", piso_id, {"bloque_id": bloque_id})
            if result:
                success += 1
                if self.link_log:
                    self.link_log.push(f"✔ Piso #{piso_id} ({piso_addr}) → Bloque #{bloque_id}")
            else:
                failed += 1
                if self.link_log:
                    self.link_log.push(f"✘ Piso #{piso_id} ({piso_addr}): fallo al vincular")

        ui.notify(
            f"Vinculación completada: {success} correctas, {failed} fallidas.",
            type="positive" if failed == 0 else "warning",
        )
        await self._load_link_suggestions()

    # =====================================================================
    # TAB 3: ENRIQUECIMIENTO GEOLINK (ref_catastral + coordenadas)
    # =====================================================================
    def _render_geolink_enrichment_tab(self):
        with ui.column().classes("w-full p-4 gap-4"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column():
                    ui.label("Enriquecimiento Espacial y Catastral (Geolink)").classes("text-h6")
                    ui.markdown(
                        "Lista los pisos sin `ref_catastral` o sin `coordenadas`. Usa los "
                        "filtros para acotar el subconjunto a reprocesar (se asume que las "
                        "direcciones ya han sido corregidas) y vuelve a consultarlos contra "
                        "CartoCiudad."
                    ).classes("text-sm text-gray-600")

                ui.button(
                    "Refrescar Listado", icon="refresh", on_click=self._load_problematic_pisos
                ).props("color=blue-grey-7 outline")

            self.geolink_filter_container = ui.column().classes("w-full")

            # La tabla se crea una sola vez (misma lógica que en Tab 2). El FilterPanel,
            # en cambio, SÍ debe recrearse en cada carga de datos: captura una referencia
            # propia a la lista de registros en su constructor (`self.records = records`),
            # por lo que si `BaseTableState.set_records()` la reemplaza por una lista nueva,
            # un FilterPanel ya creado quedaría apuntando a la lista vieja. Este es el mismo
            # patrón que ya usa `views/views_explorer.py`.
            self.geolink_table = DataTable(state=self.geolink_state, show_actions=False)
            self.geolink_table.create()

            with ui.row().classes("w-full justify-end"):
                self.geolink_execute_button = ui.button(
                    "Reprocesar Filtrados", icon="explore", on_click=self._execute_geolink_enrichment
                ).props("color=primary").set_enabled(False)

            with ui.card().classes("w-full p-2 h-40 bg-gray-50"):
                ui.label("Registro de Enriquecimiento").classes("text-caption text-gray-600 mb-1")
                self.geolink_log = ui.log(max_lines=50).classes("w-full h-28 bg-white font-mono text-xs border rounded p-2")

        ui.timer(0.1, self._load_problematic_pisos, once=True)

    async def _load_problematic_pisos(self):
        try:
            records = await self.api.get_records(
                "pisos",
                filters={"or": "(ref_catastral.is.null,coordenadas.is.null)"},
                order="direccion.asc",
                limit=5000,
            )
        except Exception as ex:
            ui.notify(f"Error al consultar pisos incompletos: {ex}", type="negative")
            return

        pisos_config = TABLE_INFO.get("pisos", {})
        self.geolink_state.set_records(records or [], pisos_config)

        self.geolink_filter_container.clear()
        with self.geolink_filter_container:
            self.geolink_filter_panel = FilterPanel(
                records=self.geolink_state.records,
                on_filter_change=self._update_geolink_filter,
                table_config=pisos_config,
            )
            self.geolink_filter_panel.create()

        if self.geolink_table:
            self.geolink_table.refresh()

        self._sync_geolink_execute_button()
        ui.notify(
            f"{len(self.geolink_state.records)} pisos con datos catastrales/espaciales incompletos.",
            type="info",
        )

    def _update_geolink_filter(self, column: str, value: Any):
        self.geolink_state.filters[column] = value
        self.geolink_state.apply_filters_and_sort()
        if self.geolink_table:
            self.geolink_table.refresh()
        self._sync_geolink_execute_button()

    def _sync_geolink_execute_button(self):
        if self.geolink_execute_button:
            self.geolink_execute_button.set_enabled(len(self.geolink_state.filtered_records) > 0)

    async def _execute_geolink_enrichment(self):
        """
        Reprocesa el subconjunto actualmente visible tras los filtros (esa es la
        'selección': acotar con los filtros de FilterPanel qué pisos entran en el
        lote). Si en el futuro se necesita selección fila-a-fila con checkboxes,
        habría que extender `components/data_table.py` — DataTable no expone hoy
        selección múltiple, solo `on_row_click`/`on_edit`/`on_delete`.
        """
        targets = list(self.geolink_state.filtered_records)
        if not targets:
            ui.notify("El filtro activo no selecciona ningún piso.", type="warning")
            return

        if self.geolink_execute_button:
            self.geolink_execute_button.set_enabled(False)
        if self.geolink_log:
            self.geolink_log.clear()

        updated = 0
        for piso in targets:
            piso_id = piso.get("id")
            direccion = piso.get("direccion")
            municipio = piso.get("municipio") or "Madrid"

            if not piso_id or not direccion:
                continue

            ref_catastral, lat, lng = await lookup_cadastral_data(direccion, municipio)
            await asyncio.sleep(RATE_LIMIT_SLEEP)  # misma cortesía de tasa que ETL/02-geolink.py

            payload: Dict[str, Any] = {}
            if ref_catastral:
                payload["ref_catastral"] = ref_catastral
            if lat is not None and lng is not None:
                payload["coordenadas"] = to_ewkt_point(lat, lng)

            if not payload:
                if self.geolink_log:
                    self.geolink_log.push(f"— Piso #{piso_id} ({direccion}): sin coincidencia en CartoCiudad")
                continue

            result = await self.api.update_record("pisos", piso_id, payload)
            if result:
                updated += 1
                if self.geolink_log:
                    self.geolink_log.push(f"✔ Piso #{piso_id} ({direccion}): {', '.join(payload.keys())} actualizado")
            else:
                if self.geolink_log:
                    self.geolink_log.push(f"✘ Piso #{piso_id} ({direccion}): fallo al guardar")

        ui.notify(
            f"Enriquecimiento finalizado: {updated}/{len(targets)} pisos actualizados.",
            type="positive",
        )
        # Los pisos recién completados dejan de cumplir el filtro `is.null` y
        # desaparecerán solos de la lista al recargar.
        await self._load_problematic_pisos()