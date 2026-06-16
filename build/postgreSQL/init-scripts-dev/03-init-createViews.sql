-- =====================================================================
-- PASO 03: CREACIÓN DE VISTAS (VERSIÓN REFACTORIZADA Y CORREGIDA)
-- =====================================================================
-- Este script se ejecuta después del 01. Asume que todas las tablas
-- y datos ya existen y crea las vistas para facilitar las consultas.
--
-- NOTA: Se garantiza que cada vista principal exponga la clave primaria
-- de su tabla base como 'id' para permitir la funcionalidad del explorador
-- de relaciones en la interfaz.
-- =====================================================================

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- LISTADO DE VISTAS DISPONIBLES EN LA INTERFAZ NICEGUI
-- (Definidas en build/niceGUI/config.py)
-- =====================================================================

-- ---------------------------------------------------------------------
-- VISTA: v_resumen_entramados_empresas
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_resumen_entramados_empresas CASCADE;

CREATE OR REPLACE VIEW v_resumen_entramados_empresas AS
SELECT
    ee.id, -- ID primario del entramado
    ee.nombre AS "Entramado",
    ee.descripcion AS "Descripción",
    e.nombre AS "Empresa",
    COUNT(DISTINCT b.id) AS "Núm. Bloques",
    COUNT(DISTINCT p.id) AS "Núm. Pisos",
    COUNT(DISTINCT a.id) AS "Núm. Afiliadas"
FROM entramado_empresas ee
    LEFT JOIN empresas e ON ee.id = e.entramado_id
    LEFT JOIN bloques b ON e.id = b.empresa_id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY ee.id, ee.nombre, ee.descripcion, e.nombre;

-- ---------------------------------------------------------------------
-- VISTA: v_resumen_nodos
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_resumen_nodos CASCADE;

CREATE OR REPLACE VIEW v_resumen_nodos AS
SELECT
    COALESCE(n.id, 0) AS id,
    COALESCE(n.nombre, 'Sin Nodo') AS "Nodo Territorial",
    COALESCE(n.descripcion, 'Afiliadas sin nodo territorial asignado') AS "Descripcion",
    COUNT(DISTINCT p.id) AS "Num. Pisos",
    COUNT(DISTINCT a.id) FILTER (
        WHERE a.estado = 'Alta') AS "Afiliadas Alta",
    COUNT(DISTINCT a.id) FILTER (
        WHERE a.estado = 'Alta' AND f.cuota > 0) AS "Afiliadas con Cuota",
    COUNT(DISTINCT c.id) AS "Total Conflictos",
    COUNT(DISTINCT c.id) FILTER (
        WHERE a.estado = 'Alta' AND c.estado = 'Abierto'
    ) AS "Conflictos Abiertos",
    -- 1. Nueva métrica para ordenar por conflictos abiertos de ámbito bloque
    COUNT(DISTINCT c.id) FILTER (
        WHERE c.estado = 'Abierto' AND LOWER(c.ambito) = 'bloque'
    ) AS "Conf. Abiertos Bloque",
    -- 4. Cálculo del % del total de afiliadas de alta que pertenecen a este nodo
    ROUND(
        100.0 * COUNT(DISTINCT a.id) FILTER (WHERE a.estado = 'Alta') / 
        NULLIF(SUM(COUNT(DISTINCT a.id) FILTER (WHERE a.estado = 'Alta')) OVER (), 0), 
        2
    ) AS "% Afiliadas Alta"
FROM nodos n
    LEFT JOIN nodos_cp_mapping ncm ON n.id = ncm.nodo_id
    LEFT JOIN pisos p ON p.cp = ncm.cp
    -- 3. Cambiado a FULL OUTER JOIN para capturar afiliadas cuyos pisos/CPs no mapean a ningún nodo
    FULL OUTER JOIN afiliadas a ON p.id = a.piso_id
    LEFT JOIN conflictos c ON a.id = c.afiliada_id
    LEFT JOIN facturacion f ON a.id = f.afiliada_id
GROUP BY n.id, n.nombre, n.descripcion
-- 1. Ordenación prioritaria solicitada
ORDER BY "Conf. Abiertos Bloque" DESC;

-- ---------------------------------------------------------------------
-- VISTA: v_conflictos_detalle (Con ordenación de campos personalizada)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_conflictos_detalle CASCADE;

CREATE OR REPLACE VIEW v_conflictos_detalle AS
SELECT
    c.id,                                              -- ID principal requerido por NiceGUI
    c.estado AS "Estado",
    c.ambito AS "Ámbito",
    a.nombre || ' ' || a.apellidos AS "Afiliada",
    p.direccion AS "Dirección",
    c.causa AS "Causa",
    c.fecha_apertura AS "Fecha de Apertura",
    ult_act.ultima_actualizacion AS "Fecha Última Actualización",
    c.descripcion AS "Descripción",
    c.tarea_actual AS "Tarea Actual",
    c.fecha_cierre AS "Fecha de Cierre",
    c.resolucion AS "Resolución",
    COALESCE(n.nombre, 'Sin Nodo') AS "Nodo",
    c.afiliada_id AS "Afiliada ID"
FROM sindicato_inq.conflictos c
    LEFT JOIN sindicato_inq.afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN sindicato_inq.pisos p ON a.piso_id = p.id
    LEFT JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN sindicato_inq.nodos n ON ncm.nodo_id = n.id
    LEFT JOIN (
        -- Subconsulta para obtener la última vez que el conflicto tuvo actividad en el diario
        SELECT conflicto_id, MAX(created_at) AS ultima_actualizacion
        FROM sindicato_inq.diario_conflictos
        GROUP BY conflicto_id
    ) ult_act ON c.id = ult_act.conflicto_id
ORDER BY c.fecha_apertura DESC;

-- ---------------------------------------------------------------------
-- VISTA: v_afiliadas_detalle
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_afiliadas_detalle CASCADE;

CREATE OR REPLACE VIEW v_afiliadas_detalle AS
SELECT
    a.id,
    a.piso_id,
    a.num_afiliada AS "Nº Afiliada",
    CONCAT(a.nombre, ' ', a.apellidos) AS "Nombre Completo",
    a.cif AS "CIF",
    a.email AS "Correo",
    a.telefono AS "Teléfono",
    TRIM(CONCAT_WS(', ', p.direccion, p.municipio, p.cp::TEXT)) AS "Direccion",
    a.regimen AS "Regimen",
    a.estado AS "Estado",
    a.fecha_alta AS "Fecha Alta",
    a.fecha_baja AS "Fecha Baja",
    p.fecha_firma AS "Fecha Firma",
    p.inmobiliaria AS "Inmob.",
    p.prop_vertical AS "Prop. Vert.",
    e.nombre AS "Prop. (afiliada)",
    p.propiedad AS "Prop. (piso)",
    COALESCE(ee.nombre, 'Sin Entramado') AS "Entramado",
    COALESCE(n.nombre, 'Sin Nodo Asignado') AS "Nodo"
FROM afiliadas a
    LEFT JOIN pisos p ON a.piso_id = p.id
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
    LEFT JOIN nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN nodos n ON ncm.nodo_id = n.id;

-- ---------------------------------------------------------------------
-- VISTA: v_resumen_bloques
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_resumen_bloques CASCADE;

CREATE OR REPLACE VIEW v_resumen_bloques AS
SELECT
    b.id,
    b.empresa_id,
    MIN(ncm.nodo_id) AS nodo_id,
    b.direccion AS "Direccion",
    e.nombre AS "Empresa Propietaria",
    ee.nombre AS "Entramado", -- Obtenemos el nombre real desde entramado_empresas
    COALESCE(MAX(n.nombre), 'Sin Nodo Asignado') AS "Nodo Territorial",
    COUNT(DISTINCT p.id) AS "Pisos en el bloque",
    COUNT(DISTINCT a.id) AS "Afiliadas en el bloque",
    -- Conteo de afiliadas activas (Alta) con cuota estrictamente mayor a 1
    COUNT(DISTINCT a.id) FILTER (
        WHERE a.estado = 'Alta' AND f.cuota > 1
    ) AS "Afiliadas Alta (Cuota > 1)",
    -- Conteo de afiliadas registradas como 'Baja'
    COUNT(DISTINCT a.id) FILTER (
        WHERE a.estado = 'Baja'
    ) AS "Afiliadas Baja"
FROM bloques b
    LEFT JOIN empresas e ON b.empresa_id = e.id
    -- Nuevo JOIN utilizando la clave foránea esperada (entramado_id)
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id 
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN nodos n ON ncm.nodo_id = n.id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
    LEFT JOIN facturacion f ON a.id = f.afiliada_id
GROUP BY b.id, b.empresa_id, b.direccion, e.nombre, ee.nombre;

-- ---------------------------------------------------------------------
-- VISTA: v_facturacion
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_facturacion CASCADE;

CREATE OR REPLACE VIEW v_facturacion AS
SELECT
    a.id AS id,
    CONCAT(a.nombre, ' ', a.apellidos) AS "Nombre Completo",
    a.email AS "Email",
    a.cif AS "NIF",
    p.direccion AS "Direccion",
    p.municipio AS "Municipio",
    p.cp AS "Codigo Postal",
    'España' AS "Pais (siempre es España)",
    a.telefono AS "Teléfono",
    f.iban AS "IBAN",
    f.cuota AS "Cuota",
    CASE f.periodicidad
        WHEN 1 THEN 'Anual'
        WHEN 3 THEN 'Trimestral'
        WHEN 12 THEN 'Mensual'
        ELSE 'Otra'
    END AS "Periodicidad",
    f.forma_pago AS "Forma de pago",
    a.estado AS "Estado",
    a.fecha_alta AS "Fecha Alta",
    a.fecha_baja AS "Fecha Baja"
FROM afiliadas a
    LEFT JOIN facturacion f ON a.id = f.afiliada_id
    LEFT JOIN pisos p ON a.piso_id = p.id
ORDER BY a.apellidos;

-- =====================================================================
-- VISTAS INTERNAS (NO DISPONIBLES EN INTERFAZ NICEGUI)
-- =====================================================================

-- ---------------------------------------------------------------------
-- VISTA: v_diario_conflictos_con_afiliada
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_diario_conflictos_con_afiliada CASCADE;

CREATE OR REPLACE VIEW v_diario_conflictos_con_afiliada AS
SELECT
    dc.id,
    dc.conflicto_id,
    dc.estado,
    dc.accion,
    dc.notas,
    dc.tarea_actual,
    dc.created_at,
    u.alias AS usuario_alias,
    a.nombre AS afiliada_nombre,
    a.apellidos AS afiliada_apellidos,
    CONCAT(a.nombre, ' ', a.apellidos) AS afiliada_nombre_completo
FROM diario_conflictos dc
    LEFT JOIN usuarios u ON dc.usuario_id = u.id
    LEFT JOIN conflictos c ON dc.conflicto_id = c.id
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id;

-- ---------------------------------------------------------------------
-- VISTA: v_conflictos_enhanced
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_conflictos_enhanced CASCADE;

CREATE OR REPLACE VIEW v_conflictos_enhanced AS
SELECT
    c.id,
    c.estado,
    c.ambito,
    c.causa,
    c.tarea_actual,
    c.fecha_apertura,
    c.fecha_cierre,
    c.descripcion,
    c.resolucion,
    c.afiliada_id,
    a.nombre AS afiliada_nombre,
    a.apellidos AS afiliada_apellidos,
    CONCAT(a.nombre, ' ', a.apellidos) AS afiliada_nombre_completo,
    a.num_afiliada,
    p.id AS piso_id,
    p.direccion AS piso_direccion,
    p.municipio AS piso_municipio,
    p.cp AS piso_cp,
    p.propiedad AS piso_propiedad,
    p.inmobiliaria AS piso_inmobiliaria,
    b.id AS bloque_id,
    b.direccion AS bloque_direccion,
    ncm.nodo_id AS nodo_id,
    n.nombre AS nodo_nombre,
    ult_act.ultima_actualizacion,  
    CONCAT(
        '(', c.id, '-', ') ',
        COALESCE(a.nombre || ' ' || a.apellidos, 'Sin afiliada'),
        ', ',
        COALESCE(p.direccion, b.direccion, 'Sin direccion')
    ) AS conflict_label
FROM sindicato_inq.conflictos c
    LEFT JOIN sindicato_inq.afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN sindicato_inq.pisos p ON a.piso_id = p.id
    LEFT JOIN sindicato_inq.bloques b ON p.bloque_id = b.id
    LEFT JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN sindicato_inq.nodos n ON ncm.nodo_id = n.id
    LEFT JOIN (
        SELECT conflicto_id, MAX(created_at) as ultima_actualizacion
        FROM sindicato_inq.diario_conflictos
        GROUP BY conflicto_id
    ) ult_act ON c.id = ult_act.conflicto_id;
    
SET search_path TO public, sindicato_inq;

-- =====================================================================
-- VISTA: v_sugerencias_pisos_huerfanos (Filtrado > 0.5 y Tiers de 0.05)
-- =====================================================================
DROP VIEW IF EXISTS sindicato_inq.v_sugerencias_pisos_huerfanos CASCADE;

CREATE OR REPLACE VIEW sindicato_inq.v_sugerencias_pisos_huerfanos AS
SELECT
    p.id AS piso_id,
    p.direccion AS "Dirección Piso",
    p.municipio AS "Municipio",
    s.id AS "ID Bloque Sugerido",
    s.direccion AS "Dirección Bloque Sugerido",
    (ROUND(s.score::numeric * 20) / 20)::numeric(3,2) AS "Score"
FROM sindicato_inq.pisos p
CROSS JOIN LATERAL (
    SELECT
        b.id,
        b.direccion,
        public.similarity(
            sindicato_inq.normalize_address_for_match(p.direccion)::text, 
            sindicato_inq.normalize_address_for_match(b.direccion)::text
        ) AS score
    FROM sindicato_inq.bloques b
    WHERE sindicato_inq.normalize_address_for_match(p.direccion)::text OPERATOR(public.%) sindicato_inq.normalize_address_for_match(b.direccion)::text
    ORDER BY 
        sindicato_inq.normalize_address_for_match(p.direccion)::text OPERATOR(public.<->) sindicato_inq.normalize_address_for_match(b.direccion)::text ASC
    LIMIT 1
) s
WHERE p.bloque_id IS NULL             
  AND p.direccion IS NOT NULL 
  AND btrim(p.direccion) <> ''
  AND s.score > 0.5; -- 💡 Only report records whose match confidence is strictly above 0.5

-- ---------------------------------------------------------------------
-- VISTA: v_consolidar_pisos_bloques (Consolidada y de Alto Rendimiento)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_consolidar_pisos_bloques CASCADE;

CREATE OR REPLACE VIEW v_consolidar_pisos_bloques AS
SELECT
    p.id,
    p.bloque_id,
    b.empresa_id,
    p.prop_vertical AS "Prop. Vertical",
    p.direccion AS "Dirección Piso",
    b.direccion AS "Dirección Bloque",
    p.propiedad AS "Propiedad Piso",
    e.nombre AS "Propiedad Bloque",
    
    -- 1. Métrica de Auditoría: Calidad del enlace actual (Similitud de texto)
    CASE
        WHEN p.bloque_id IS NOT NULL AND b.id IS NOT NULL THEN
            public.similarity(
                sindicato_inq.normalize_address_for_match(p.direccion),
                sindicato_inq.normalize_address_for_match(b.direccion)
            )
        ELSE NULL
    END AS "Score Enlace Actual",

    -- 2. Métrica de Auditoría: Bloque alternativo sugerido por proximidad difusa
    s.id AS "ID Bloque Sugerido",
    s.direccion AS "Dirección Bloque Sugerido",
    s.score AS "Score Sugerido",

    -- 3. Bandera de Alerta: Indica si existe un bloque en el sistema que encaja mucho mejor
    (p.bloque_id IS DISTINCT FROM s.id AND s.score >= 0.88) AS "Alerta Dirección Subóptima",

    -- 4. Matriz combinada de Consistencia de Propiedad (Simplificada y extendida)
    CASE
        WHEN p.bloque_id IS NULL THEN 'No enlazado'
        WHEN b.empresa_id IS NULL AND p.propiedad IS NOT NULL THEN 'Falta empresa Bloque'
        WHEN p.propiedad IS NULL AND b.empresa_id IS NOT NULL THEN 'Falta propiedad Piso'
        WHEN COALESCE(NULLIF(LOWER(TRIM(p.propiedad)), ''), '') = 
             COALESCE(NULLIF(LOWER(TRIM(e.nombre)), ''), '') THEN 'OK'
        ELSE 'Inconsistente'
    END AS "Consistencia Propiedad"

FROM pisos p
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    -- Búsqueda lateral indexada de máxima velocidad
    LEFT JOIN LATERAL (
        SELECT
            b_sug.id,
            b_sug.direccion,
            public.similarity(
                sindicato_inq.normalize_address_for_match(p.direccion), 
                sindicato_inq.normalize_address_for_match(b_sug.direccion)
            ) AS score
        FROM bloques b_sug
        WHERE sindicato_inq.normalize_address_for_match(p.direccion) OPERATOR(public.%) sindicato_inq.normalize_address_for_match(b_sug.direccion)
        ORDER BY 
            sindicato_inq.normalize_address_for_match(p.direccion) OPERATOR(public.<->) sindicato_inq.normalize_address_for_match(b_sug.direccion) ASC
        LIMIT 1
    ) s ON p.direccion IS NOT NULL AND btrim(p.direccion) <> '';

CREATE INDEX IF NOT EXISTS bloques_normalized_gist_idx 
ON bloques USING gist (sindicato_inq.normalize_address_for_match(direccion) public.gist_trgm_ops);

CREATE INDEX IF NOT EXISTS pisos_normalized_gist_idx 
ON pisos USING gist (sindicato_inq.normalize_address_for_match(direccion) public.gist_trgm_ops);