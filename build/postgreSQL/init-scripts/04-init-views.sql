-- =====================================================================
-- ARCHIVO 02: CREACIÓN DE VISTAS (VERSIÓN MEJORADA CON IDs)
-- =====================================================================
-- Este script se ejecuta después del 01. Asume que todas las tablas
-- y datos ya existen y crea las vistas para facilitar las consultas.
-- NOTA: Se han añadido los IDs primarios y foráneos para permitir
-- la funcionalidad del explorador de relaciones en la interfaz.
-- =====================================================================

SET search_path TO sindicato_inq, public;

-- VISTA 1: AFILIADAS (AHORA INCLUYE IDs Y NOMBRE DEL NODO)
CREATE OR REPLACE VIEW v_afiliadas AS
SELECT
    a.id, -- ID primario de la afiliada (para buscar hijos)
    a.piso_id, -- ID foráneo del piso (para buscar padres)
    a.num_afiliada AS "Núm.Afiliada",
    a.nombre AS "Nombre",
    a.apellidos AS "Apellidos",
    a.cif AS "CIF",
    a.genero AS "Género",
    TRIM(CONCAT_WS(', ', p.direccion, p.municipio, p.cp::text)) AS "Dirección",
    a.regimen AS "Régimen",
    a.estado AS "Estado",
    e.api AS "API",
    e.nombre AS "Propiedad",
    COALESCE(ee.nombre, 'Sin Entramado') AS "Entramado",
    COALESCE(n.nombre, 'Sin Nodo Asignado') AS "Nodo"
FROM afiliadas a
LEFT JOIN pisos p ON a.piso_id = p.id
LEFT JOIN bloques b ON p.bloque_id = b.id
LEFT JOIN empresas e ON b.empresa_id = e.id
LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
LEFT JOIN nodos n ON b.nodo_id = n.id;

-- VISTA 2: ENTRAMADO_EMPRESAS (AHORA CON MÉTRICAS AMPLIADAS Y AGRUPACIÓN CORRECTA)
CREATE OR REPLACE VIEW entramado_empresas_detalle AS
SELECT
    ee.id, -- ID primario del entramado
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
    ee.id, ee.nombre, ee.descripcion;

-- VISTA 3: BLOQUES (YA TENÍA ID, PERO SE AÑADEN FORÁNEOS PARA CLARIDAD)
CREATE OR REPLACE VIEW v_bloques AS
SELECT b.id, -- ID primario del bloque
    b.empresa_id, -- ID foráneo de la empresa
    b.direccion AS "Dirección", b.estado AS "Estado", b.api AS "API", e.nombre AS "Propiedad", ee.nombre AS "Entramado", COUNT(DISTINCT a.id) AS "Núm.Afiliadas"
FROM
    bloques b
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY
    b.id,
    e.nombre,
    ee.nombre;

-- VISTA 4: VISTA DE DETALLE DE CONFLICTOS (UNIFICADA)
-- Esta vista combina la información de la afiliada, el nodo y el responsable, reemplazando las vistas anteriores.
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


-- VISTA 5: RESUMEN POR NODO TERRITORIAL
CREATE OR REPLACE VIEW v_resumen_nodos AS
SELECT
    n.id,
    n.nombre AS "Nodo Territorial",
    n.descripcion AS "Descripción",
    COUNT(DISTINCT b.id) AS "Núm. Bloques",
    COUNT(DISTINCT e.id) AS "Núm. Empresas Activas",
    COUNT(DISTINCT a.id) AS "Núm. Afiliadas",
    COUNT(DISTINCT c.id) AS "Total Conflictos",
    COUNT(DISTINCT c.id) FILTER (WHERE c.estado = 'Abierto') AS "Conflictos Abiertos"
FROM
    nodos n
    LEFT JOIN bloques b ON n.id = b.nodo_id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
    LEFT JOIN conflictos c ON a.id = c.afiliada_id
GROUP BY
    n.id, n.nombre, n.descripcion
ORDER BY
    "Núm. Afiliadas" DESC;




-- VISTA 6: VISTA INTERNA (NO PARA USUARIOS) MEJORADA PARA LA INTERFAZ DE CONFLICTOS
CREATE OR REPLACE VIEW sindicato_inq.v_conflictos_enhanced AS
SELECT
    c.id,
    c.estado,
    c.ambito,
    c.causa,
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