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
-- NOTA: Esta es una vista de resumen. Al hacer clic en una fila, se mostrarán las empresas hijas (child records).
CREATE OR REPLACE VIEW v_entramado_empresas AS
SELECT
    ee.id, -- ID primario del entramado (para buscar hijos)
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
SELECT
    b.id, -- ID primario del bloque (para buscar hijos)
    b.empresa_id, -- ID foráneo de la empresa (para buscar padre)
    b.nodo_id, -- ID foráneo del nodo (para buscar padre)
    b.direccion AS "Dirección",
    b.estado AS "Estado",
    b.api AS "API",
    e.nombre AS "Propiedad",
    ee.nombre AS "Entramado",
    COUNT(DISTINCT a.id) AS "Núm.Afiliadas"
FROM
    bloques b
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY
    b.id, e.nombre, ee.nombre;

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

-- VISTA 5: DIARIO DE CONFLICTOS CON DETALLES
CREATE OR REPLACE VIEW v_diario_conflictos_con_afiliada AS
SELECT
    d.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo,
    u.alias AS autor_nota_alias,
    ac.nombre AS accion_nombre
FROM
    diario_conflictos d
    LEFT JOIN conflictos c ON d.conflicto_id = c.id
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN usuarios u ON d.usuario_id = u.id
    LEFT JOIN acciones ac ON d.accion_id = ac.id;

-- VISTA 6: VISTA MEJORADA PARA LA INTERFAZ DE CONFLICTOS
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

-- VISTA 7: RESUMEN POR NODO TERRITORIAL
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

-- =====================================================================
-- PROCEDIMIENTO: SINCRONIZACIÓN MASIVA DE NODOS PARA BLOQUES
-- =====================================================================
-- Este procedimiento actualiza el campo 'nodo_id' para todos los bloques
-- que actualmente no lo tienen asignado. Determina el nodo más apropiado
-- basándose en el código postal más frecuente de los pisos asociados.
-- Para ejecutarlo, usar: CALL sync_all_bloques_to_nodos();
-- =====================================================================
CREATE OR REPLACE PROCEDURE sync_all_bloques_to_nodos()
LANGUAGE plpgsql
AS $$
DECLARE
    bloque_record RECORD;
    most_common_nodo_id INTEGER;
BEGIN
    -- Itera sobre cada bloque que no tiene un nodo asignado
    FOR bloque_record IN SELECT id FROM sindicato_inq.bloques WHERE nodo_id IS NULL LOOP
        -- Encuentra el nodo_id más común entre los pisos de este bloque
        SELECT ncm.nodo_id INTO most_common_nodo_id
        FROM sindicato_inq.pisos p
        JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
        WHERE p.bloque_id = bloque_record.id
        GROUP BY ncm.nodo_id
        ORDER BY COUNT(*) DESC
        LIMIT 1;

        -- Si se encontró un nodo común, actualiza el bloque
        IF FOUND AND most_common_nodo_id IS NOT NULL THEN
            UPDATE sindicato_inq.bloques
            SET nodo_id = most_common_nodo_id
            WHERE id = bloque_record.id;
        END IF;
    END LOOP;
END;
$$;
