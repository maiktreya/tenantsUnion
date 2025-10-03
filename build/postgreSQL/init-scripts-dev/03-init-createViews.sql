-- =====================================================================
-- PASO 3: VISTAS PARA PRESENTACIÓN DE DATOS (REVISADAS)
-- =====================================================================

SET search_path TO sindicato_inq, public;

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
FROM
    bloques b
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN nodos n ON ncm.nodo_id = n.id
WHERE
    a.estado = 'Alta'
GROUP BY
    b.id,
    b.empresa_id,
    b.direccion,
    e.nombre
ORDER BY "Afiliadas en el bloque" DESC;

DROP VIEW IF EXISTS v_resumen_nodos CASCADE;
CREATE OR REPLACE VIEW v_resumen_nodos AS
SELECT
    n.id,
    n.nombre,
    n.descripcion,
    COUNT(DISTINCT b.id) as num_bloques,
    COUNT(DISTINCT p.id) as num_pisos,
    COUNT(DISTINCT a.id) as num_afiliadas
FROM
    nodos n
    LEFT JOIN nodos_cp_mapping ncm ON n.id = ncm.nodo_id
    LEFT JOIN pisos p ON ncm.cp = p.cp
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
WHERE
    a.estado = 'Alta'
GROUP BY
    n.id,
    n.nombre,
    n.descripcion;

CREATE OR REPLACE VIEW v_resumen_entramados_empresas AS
SELECT
    ee.id,
    ee.nombre,
    ee.descripcion,
    COUNT(DISTINCT e.id) as num_empresas,
    COUNT(DISTINCT b.id) as num_bloques,
    COUNT(DISTINCT a.id) as num_afiliadas
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

DROP VIEW IF EXISTS v_afiliadas_detalle CASCADE;
CREATE OR REPLACE VIEW v_afiliadas_detalle AS
SELECT
    a.id,
    a.piso_id,
    a.num_afiliada AS "Num.Afiliada",
    a.nombre AS "Nombre",
    a.apellidos AS "Apellidos",
    a.cif AS "CIF",
    a.genero AS "Genero",
    TRIM(
        CONCAT_WS(
            ', ',
            p.direccion,
            p.municipio,
            p.cp::text
        )
    ) AS "Direccion",
    a.regimen AS "Regimen",
    a.estado AS "Estado",
    a.fecha_alta as "Fecha Alta",
    a.fecha_baja as "Fecha Baja",
    p.fecha_firma as "Fecha Firma",
    p.inmobiliaria AS "Inmob.",
    e.nombre AS "Propiedad",
    COALESCE(ee.nombre, 'Sin Entramado') AS "Entramado",
    COALESCE(n.nombre, 'Sin Nodo Asignado') AS "Nodo"
FROM
    afiliadas a
    LEFT JOIN pisos p ON a.piso_id = p.id
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
    LEFT JOIN nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN nodos n ON ncm.nodo_id = n.id;

DROP VIEW IF EXISTS v_conflictos_detalle CASCADE;
CREATE OR REPLACE VIEW v_conflictos_detalle AS
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
    a.nombre as afiliada_nombre,
    a.apellidos as afiliada_apellidos,
    CONCAT(a.nombre, ' ', a.apellidos) as afiliada_nombre_completo,
    a.num_afiliada,
    p.direccion as direccion_piso,
    n.nombre as nodo_nombre
FROM
    conflictos c
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN pisos p ON a.piso_id = p.id
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN nodos n ON ncm.nodo_id = n.id;

CREATE OR REPLACE VIEW v_diario_conflictos_con_afiliada AS
SELECT
    dc.id,
    dc.conflicto_id,
    dc.estado,
    dc.accion,
    dc.notas,
    dc.tarea_actual,
    dc.created_at,
    u.alias as usuario_alias,
    a.nombre as afiliada_nombre,
    a.apellidos as afiliada_apellidos,
    CONCAT(a.nombre, ' ', a.apellidos) as afiliada_nombre_completo
FROM
    diario_conflictos dc
    LEFT JOIN usuarios u ON dc.usuario_id = u.id
    LEFT JOIN conflictos c ON dc.conflicto_id = c.id
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id;

CREATE OR REPLACE VIEW comprobar_link_pisos_bloques AS
SELECT
    p.id, -- --- MEJORA: Se usa 'id' en lugar de 'piso_id' para consistencia.
    p.direccion as piso_direccion,
    p.bloque_id,
    b.direccion as bloque_direccion,
    CASE
        WHEN p.bloque_id IS NULL THEN 'Sin bloque asignado'
        WHEN b.id IS NULL THEN 'Bloque referenciado no existe'
        ELSE 'Vinculación correcta'
    END as estado_vinculacion
FROM pisos p
    LEFT JOIN bloques b ON p.bloque_id = b.id;

--
CREATE OR REPLACE VIEW v_consolidar_pisos_bloques AS
SELECT
    p.id,
    p.bloque_id,
    b.empresa_id,
    p.direccion AS "Dirección Piso",
    b.direccion AS "Dirección Bloque",
    p.propiedad AS "Empresa Propietaria (Piso)",
    e.nombre AS "Empresa Propietaria (Bloque, real)",
    CASE
    WHEN b.empresa_id = NULL THEN 'Bloque sin empresa'
        WHEN COALESCE(NULLIF(LOWER(TRIM(p.propiedad)), ''), '') = COALESCE(NULLIF(LOWER(TRIM(e.nombre)), ''), '') THEN ''
        ELSE 'Inconsistente'
    END AS "Consistencia Propiedad"
FROM
    pisos p
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN empresas e ON b.empresa_id = e.id;

-- TABLE USED BY NICEGUI "conflictos.py" view interrnally. Not user accessible in niceGUI
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
    b.id AS bloque_id,
    b.direccion AS bloque_direccion,
    ncm.nodo_id AS nodo_id,
    n.nombre AS nodo_nombre,
    CONCAT(
        '(',
        c.id,
        '-',
        ' ',
        c.ambito,
        ') ',
        COALESCE(
            p.direccion,
            b.direccion,
            'Sin direccion'
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
    LEFT JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN sindicato_inq.nodos n ON ncm.nodo_id = n.id;

-- VISTA 6: VISTA CON INFORMACIÓN DE FACTURACIÓN EXTENDIDA
CREATE OR REPLACE VIEW v_facturacion AS
SELECT
    -- Fields from 'afiliadas' table
    a.id AS "id",
    CONCAT(a.nombre, ' ', a.apellidos) as afiliada_nombre_completo,
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
        WHEN 12 THEN 'Mensual'
        WHEN 3 THEN 'Trimestral' -- Added for completeness
        ELSE 'Otra'
    END AS "Periodicidad",
    f.forma_pago AS "Forma de pago",
    a.estado as "Estado",
    a.fecha_alta as "Fecha Alta",
    a.fecha_baja as "Fecha Baja"
FROM
    afiliadas AS a
LEFT JOIN
    facturacion AS f ON a.id = f.afiliada_id
LEFT JOIN
	pisos as p on a.piso_id = p.id
ORDER BY
    a.apellidos;
