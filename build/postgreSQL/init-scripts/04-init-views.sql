-- =====================================================================
-- ARCHIVO 02: CREACIÓN DE VISTAS (VERSIÓN MEJORADA CON IDs)
-- =====================================================================
-- Este script se ejecuta después del 01. Asume que todas las tablas
-- y datos ya existen y crea las vistas para facilitar las consultas.
-- NOTA: Se han añadido los IDs primarios y foráneos para permitir
-- la funcionalidad del explorador de relaciones en la interfaz.
-- =====================================================================

SET search_path TO sindicato_inq, public;

-- VISTA 1: AFILIADAS (AHORA INCLUYE IDs)
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
    COALESCE(ee.nombre, 'Sin Entramado') AS "Entramado"
FROM afiliadas a
LEFT JOIN pisos p ON a.piso_id = p.id
LEFT JOIN bloques b ON p.bloque_id = b.id
LEFT JOIN empresas e ON b.empresa_id = e.id
LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id;

-- VISTA 2: ENTRAMADO_EMPRESAS (AHORA INCLUYE IDs)
CREATE OR REPLACE VIEW v_entramado_empresas AS
SELECT
    e.id, -- ID primario de la empresa (para buscar hijos)
    e.entramado_id, -- ID foráneo del entramado (para buscar padres)
    e.nombre AS "Nombre",
    e.cif_nif_nie AS "CIF/NIF/NIE",
    ee.nombre AS "Entramado",
    e.directivos AS "Directivos",
    e.api AS "API",
    e.direccion_fiscal AS "Dirección",
    COUNT(DISTINCT a.id) AS "Núm.Afiliadas"
FROM
    entramado_empresas ee
    LEFT JOIN empresas e ON ee.id = e.entramado_id
    LEFT JOIN bloques b ON e.id = b.empresa_id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY
    e.id,
    e.nombre,
    e.cif_nif_nie,
    ee.nombre,
    e.directivos,
    e.api,
    e.direccion_fiscal;

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

-- Las siguientes vistas usan 'SELECT *', por lo que ya incluyen los IDs necesarios.
-- No se necesitan cambios en ellas.

CREATE OR REPLACE VIEW v_conflictos_con_afiliada AS
SELECT
    c.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo
FROM conflictos c
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id;

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

CREATE OR REPLACE VIEW sindicato_inq.v_conflictos_con_nodo AS
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