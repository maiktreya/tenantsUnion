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

CREATE EXTENSION IF NOT EXISTS pg_trgm;

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
    COUNT(DISTINCT e.id) AS "Núm. Empresas",
    COUNT(DISTINCT b.id) AS "Núm. Bloques",
    COUNT(DISTINCT p.id) AS "Núm. Pisos",
    COUNT(DISTINCT a.id) AS "Núm. Afiliadas"
FROM entramado_empresas ee
    LEFT JOIN empresas e ON ee.id = e.entramado_id
    LEFT JOIN bloques b ON e.id = b.empresa_id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY ee.id, ee.nombre, ee.descripcion;

-- ---------------------------------------------------------------------
-- VISTA: v_resumen_nodos
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_resumen_nodos CASCADE;

CREATE OR REPLACE VIEW v_resumen_nodos AS
SELECT
    n.id,
    n.nombre AS "Nodo Territorial",
    n.descripcion AS "Descripcion",
    COUNT(DISTINCT p.id) AS "Num. Pisos",
    COUNT(DISTINCT b.id) AS "Num. Bloques",
    COUNT(DISTINCT a.id) FILTER (
        WHERE a.estado = 'Alta') AS "Afiliadas Alta",
    COUNT(DISTINCT a.id) FILTER (
        WHERE a.estado = 'Alta' AND f.cuota > 0) AS "Afiliadas con Cuota",
    COUNT(DISTINCT c.id) AS "Total Conflictos",
    COUNT(DISTINCT c.id) FILTER (
        WHERE a.estado = 'Alta' AND c.estado = 'Abierto'
    ) AS "Conflictos Abiertos"
FROM nodos n
    LEFT JOIN nodos_cp_mapping ncm ON n.id = ncm.nodo_id
    LEFT JOIN pisos p ON p.cp = ncm.cp
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
    LEFT JOIN conflictos c ON a.id = c.afiliada_id
    LEFT JOIN facturacion f ON a.id = f.afiliada_id
GROUP BY n.id, n.nombre, n.descripcion
ORDER BY "Afiliadas Alta" DESC;
-- ---------------------------------------------------------------------
-- VISTA: v_conflictos_detalle
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_conflictos_detalle CASCADE;

CREATE OR REPLACE VIEW v_conflictos_detalle AS
SELECT
    c.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo,
    n.nombre AS nodo_nombre,
    p.direccion AS direccion_piso
FROM sindicato_inq.conflictos c
    LEFT JOIN sindicato_inq.afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN sindicato_inq.pisos p ON a.piso_id = p.id
    LEFT JOIN sindicato_inq.bloques b ON p.bloque_id = b.id
    LEFT JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN sindicato_inq.nodos n ON ncm.nodo_id = n.id;

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
    e.nombre AS "Propiedad",
    p.prop_vertical AS "Prop. Vertical",
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
    COALESCE(MAX(n.nombre), 'Sin Nodo Asignado') AS "Nodo Territorial",
    COUNT(DISTINCT p.id) AS "Pisos en el bloque",
    COUNT(DISTINCT a.id) AS "Afiliadas en el bloque"
FROM bloques b
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN nodos n ON ncm.nodo_id = n.id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY b.id, b.empresa_id, b.direccion, e.nombre;

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
    LEFT JOIN sindicato_inq.nodos n ON ncm.nodo_id = n.id;

-- ---------------------------------------------------------------------
-- VISTA: comprobar_link_pisos_bloques
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS comprobar_link_pisos_bloques CASCADE;

CREATE OR REPLACE VIEW comprobar_link_pisos_bloques AS
SELECT
    p.id,
    p.direccion AS direccion1_piso,
    p.bloque_id,
    b.direccion AS direccion2_bloque,
    (p.bloque_id IS NOT NULL) AS linked,
    similarity(
        TRIM(split_part(b.direccion, ',', 1)) || ', ' ||
        TRIM(split_part(b.direccion, ',', 2)),
        TRIM(split_part(p.direccion, ',', 1)) || ', ' ||
        TRIM(split_part(p.direccion, ',', 2))
    ) AS score
FROM pisos p
    LEFT JOIN bloques b ON p.bloque_id = b.id
ORDER BY linked DESC, score DESC;

-- ---------------------------------------------------------------------
-- VISTA: v_consolidar_pisos_bloques
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
    CASE
        WHEN b.empresa_id IS NULL THEN 'Falta empresa Bloque'
        WHEN COALESCE(NULLIF(LOWER(TRIM(p.propiedad)), ''), '') =
             COALESCE(NULLIF(LOWER(TRIM(e.nombre)), ''), '') THEN ''
        WHEN p.propiedad IS NULL AND b.empresa_id IS NOT NULL THEN ''
        ELSE 'Inconsistente'
    END AS "Consistencia Propiedad"
FROM pisos p
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN empresas e ON b.empresa_id = e.id;