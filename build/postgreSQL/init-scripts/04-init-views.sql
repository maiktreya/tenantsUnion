-- =====================================================================
-- ARCHIVO 04: CREACIÓN DE VISTAS (VERSIÓN REFACTORIZADA Y CORREGIDA)
-- =====================================================================
-- Este script se ejecuta después del 01. Asume que todas las tablas
-- y datos ya existen y crea las vistas para facilitar las consultas.
-- NOTA: Se ha garantizado que cada vista principal exponga la clave
-- primaria de su tabla base como 'id' para permitir la funcionalidad
-- del explorador de relaciones en la interfaz.
-- =====================================================================

-- =====================================================================
-- LISTADO DE VISTAS DISPONIBLES EN LA INTERFAZ NICEGUI (DESCRITAS EN build/niceGUI/config.py)
-- =====================================================================

SET search_path TO sindicato_inq, public;

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- VISTA 1: ENTRAMADO_EMPRESAS (CORREGIDA CON 'id' EXPLÍCITO)
-- NOTA: Esta es una vista de resumen. Al hacer clic en una fila, se mostrarán las empresas hijas (child records).
CREATE OR REPLACE VIEW v_resumen_entramados_empresas AS
SELECT
    ee.id, -- FIX: Se asegura que el ID primario del entramado esté presente como 'id'.
    ee.nombre AS "Entramado",
    ee.descripcion AS "Descripción",
    COUNT(DISTINCT e.id) AS "Núm. Empresas",
    COUNT(DISTINCT b.id) AS "Núm. Bloques",
    COUNT(DISTINCT p.id) AS "Núm. Pisos",
    COUNT(DISTINCT a.id) AS "Núm. Afiliadas"
FROM
    entramado_empresas ee
    LEFT JOIN empresas e ON ee.id = e.entramado_id
    LEFT JOIN bloques b ON e.id = b.empresa_id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY
    ee.id,
    ee.nombre,
    ee.descripcion;

-- VISTA 2: RESUMEN POR NODO TERRITORIAL (CORREGIDA CON 'id' EXPLÍCITO)
CREATE OR REPLACE VIEW v_resumen_nodos AS
SELECT
    n.id, -- FIX: Se asegura que el ID primario del nodo esté presente como 'id'.
    n.nombre AS "Nodo Territorial",
    n.descripcion AS "Descripción",
    COUNT(DISTINCT b.id) AS "Núm. Bloques",
    COUNT(DISTINCT e.id) AS "Núm. Empresas Activas",
    COUNT(DISTINCT a.id) AS "Núm. Afiliadas",
    COUNT(DISTINCT c.id) AS "Total Conflictos",
    COUNT(DISTINCT c.id) FILTER (
        WHERE
            c.estado = 'Abierto'
    ) AS "Conflictos Abiertos"
FROM
    nodos n
    LEFT JOIN bloques b ON n.id = b.nodo_id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
    LEFT JOIN conflictos c ON a.id = c.afiliada_id
GROUP BY
    n.id,
    n.nombre,
    n.descripcion
ORDER BY "Núm. Afiliadas" DESC;

-- VISTA 3: VISTA DE DETALLE DE CONFLICTOS (UNIFICADA)
-- Esta vista ya incluye 'c.id' a través de 'c.*', por lo que es correcta.
CREATE OR REPLACE VIEW v_conflictos_detalle AS
SELECT
    c.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo,
    u.alias AS usuario_responsable_alias,
    n.nombre AS nodo_nombre,
    p.direccion AS direccion_piso
FROM
    sindicato_inq.conflictos c
    LEFT JOIN sindicato_inq.afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN sindicato_inq.pisos p ON a.piso_id = p.id
    LEFT JOIN sindicato_inq.bloques b ON p.bloque_id = b.id
    LEFT JOIN sindicato_inq.nodos n ON b.nodo_id = n.id
    LEFT JOIN sindicato_inq.usuarios u ON c.usuario_responsable_id = u.id;

-- VISTA 4: AFILIADAS (ESTA VISTA YA ERA CORRECTA)
CREATE OR REPLACE VIEW v_afiliadas_detalle AS
SELECT
    a.id, -- ID primario de la afiliada (para buscar hijos)
    a.piso_id, -- ID foráneo del piso (para buscar padres)
    a.num_afiliada AS "Núm.Afiliada",
    a.nombre AS "Nombre",
    a.apellidos AS "Apellidos",
    a.cif AS "CIF",
    a.genero AS "Género",
    TRIM(
        CONCAT_WS(
            ', ',
            p.direccion,
            p.municipio,
            p.cp::text
        )
    ) AS "Dirección",
    a.regimen AS "Régimen",
    a.estado AS "Estado",
    p.inmobiliaria AS "Inmobiliaria",
    e.nombre AS "Propiedad",
    COALESCE(ee.nombre, 'Sin Entramado') AS "Entramado",
    COALESCE(n.nombre, 'Sin Nodo Asignado') AS "Nodo"
FROM
    afiliadas a
    LEFT JOIN pisos p ON a.piso_id = p.id
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
    LEFT JOIN nodos n ON b.nodo_id = n.id;

-- VISTA 5: RESUMEN DE BLOQUES (ESTA VISTA YA ERA CORRECTA)
CREATE OR REPLACE VIEW v_resumen_bloques AS
SELECT
    b.id, -- Primary key for the block
    b.empresa_id, -- Foreign key to empresas
    b.nodo_id, -- Foreign key to nodos
    b.direccion AS "Dirección",
    e.nombre AS "Empresa Propietaria",
    n.nombre AS "Nodo Territorial",
    COUNT(DISTINCT p.id) AS "Pisos en el bloque",
    COUNT(DISTINCT a.id) AS "Afiliadas en el bloque"
FROM
    bloques b
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN nodos n ON b.nodo_id = n.id
GROUP BY
    b.id,
    e.nombre,
    n.nombre
ORDER BY "Afiliadas en el bloque" DESC;
-- =====================================================================
-- VISTAS INTERNAS VISTA CONFLICTOS (NO DISPONIBLE EN LA INTERFAZ NI EN CONFIG.PY)
-- =====================================================================
CREATE OR REPLACE VIEW v_diario_conflictos_con_afiliada AS
SELECT
    d.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo,
    u.alias AS autor_nota_alias
FROM
    diario_conflictos d
    LEFT JOIN conflictos c ON d.conflicto_id = c.id
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN usuarios u ON d.usuario_id = u.id;

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
    c.usuario_responsable_id,
    a.nombre AS afiliada_nombre,
    a.apellidos AS afiliada_apellidos,
    CONCAT(a.nombre, ' ', a.apellidos) AS afiliada_nombre_completo,
    a.num_afiliada,
    p.id AS piso_id,
    p.direccion AS piso_direccion,
    p.municipio AS piso_municipio,
    p.cp AS piso_cp,
    b.id AS bloque_id,
    b.direccion AS bloque_direccion,
    COALESCE(n1.id, n2.id) AS nodo_id,
    COALESCE(n1.nombre, n2.nombre) AS nodo_nombre,
    u.alias AS usuario_responsable_alias,
    CONCAT(
        'ID ',
        c.id,
        ' - ',
        COALESCE(
            p.direccion,
            b.direccion,
            'Sin dirección'
        ),
        ' | ',
        COALESCE(
            a.nombre || ' ' || a.apellidos,
            'Sin afiliada'
        ),
        CASE
            WHEN c.estado IS NOT NULL THEN ' [' || c.estado || ']'
            ELSE ''
        END
    ) AS conflict_label
FROM
    sindicato_inq.conflictos c
    LEFT JOIN sindicato_inq.afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN sindicato_inq.pisos p ON a.piso_id = p.id
    LEFT JOIN sindicato_inq.bloques b ON p.bloque_id = b.id
    LEFT JOIN sindicato_inq.nodos n1 ON b.nodo_id = n1.id
    LEFT JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN sindicato_inq.nodos n2 ON ncm.nodo_id = n2.id
    LEFT JOIN sindicato_inq.usuarios u ON c.usuario_responsable_id = u.id;

-- =====================================================================
-- PROCEDIMIENTO: SINCRONIZACIÓN MASIVA DE NODOS PARA BLOQUES
-- =====================================================================
CREATE OR REPLACE VIEW comprobar_link_pisos_bloques AS

SELECT
    p.id,
    p.direccion AS direccion1_piso,
    p.bloque_id,
    b.direccion AS direccion2_bloque,
    (p.bloque_id IS NOT NULL) AS linked,
    similarity (
        trim(
            split_part(b.direccion, ',', 1)
        ) || ', ' || trim(
            split_part(b.direccion, ',', 2)
        ),
        trim(
            split_part(p.direccion, ',', 1)
        ) || ', ' || trim(
            split_part(p.direccion, ',', 2)
        )
    ) AS score
FROM pisos p
    LEFT JOIN bloques b ON p.bloque_id = b.id
ORDER BY linked DESC, score DESC;