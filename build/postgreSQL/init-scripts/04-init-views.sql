-- =====================================================================
-- ARCHIVO 02: CREACIÓN DE VISTAS MATERIALIZADAS
-- =====================================================================
-- Este script se ejecuta después del 01. Asume que todas las tablas
-- y datos ya existen y crea las vistas para facilitar las consultas.
-- =====================================================================

SET search_path TO sindicato_inq, public;

-- VISTA 1: AFILIADAS (replica la estructura del CSV principal)
CREATE OR REPLACE VIEW v_afiliadas AS
SELECT
    a.num_afiliada AS "Núm.Afiliada", a.nombre AS "Nombre", a.apellidos AS "Apellidos", a.cif AS "CIF", a.genero AS "Género",
    TRIM(CONCAT_WS(', ', p.direccion, p.municipio, p.cp::text)) AS "Dirección",
    f.cuota AS "Cuota",
    CASE f.periodicidad WHEN 1 THEN 'Mensual' WHEN 3 THEN 'Trimestral' WHEN 6 THEN 'Semestral' WHEN 12 THEN 'Anual' ELSE 'Otra' END AS "Frecuencia de Pago",
    f.forma_pago AS "Forma de Pago", f.iban AS "Cuenta Corriente", a.regimen AS "Régimen", a.estado AS "Estado", e.api AS "API", e.nombre AS "Propiedad", ee.nombre AS "Entramado"
FROM afiliadas a
LEFT JOIN facturacion f ON a.id = f.afiliada_id
LEFT JOIN pisos p ON a.piso_id = p.id
LEFT JOIN bloques b ON p.bloque_id = b.id
LEFT JOIN empresas e ON b.empresa_id = e.id
LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id;

-- VISTA 2: EMPRESAS (replica la estructura de Empresas.csv con conteos)
CREATE OR REPLACE VIEW v_entramado_empresas AS
SELECT e.nombre AS "Nombre", e.cif_nif_nie AS "CIF/NIF/NIE", ee.nombre AS "Entramado", e.directivos AS "Directivos", e.api AS "API", e.direccion_fiscal AS "Dirección", COUNT(DISTINCT a.id) AS "Núm.Afiliadas"
FROM
    entramado_empresas ee
    LEFT JOIN empresas e ON ee.id = e.entramado_id
    LEFT JOIN bloques b ON e.id = b.empresa_id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY
    e.id,
    ee.nombre;

-- VISTA 3: BLOQUES (replica la estructura de Bloques.csv con conteos)
CREATE OR REPLACE VIEW v_bloques AS
SELECT b.direccion AS "Dirección", b.estado AS "Estado", b.api AS "API", e.nombre AS "Propiedad", ee.nombre AS "Entramado", COUNT(DISTINCT a.id) AS "Núm.Afiliadas"
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

-- View for conflicts with the affiliate's full name
CREATE OR REPLACE VIEW v_conflictos_con_afiliada AS
SELECT
    c.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo
FROM conflictos c
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id;

-- View for diary entries with the affiliate's full name

CREATE OR REPLACE VIEW v_diario_conflictos_con_afiliada AS
SELECT
    d.*,
    -- Get the full name of the affiliate related to the conflict.
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo,

-- Get the alias of the user who created the diary entry.
u.alias AS autor_nota_alias,

-- Get the name of the action performed.
ac.nombre AS accion_nombre
FROM
    diario_conflictos d
    -- Join to get the conflict (and from there, the affiliate).
    LEFT JOIN conflictos c ON d.conflicto_id = c.id
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN usuarios u ON d.usuario_id = u.id
    LEFT JOIN acciones ac ON d.accion_id = ac.id;

CREATE OR REPLACE VIEW sindicato_inq.v_conflictos_con_nodo AS
SELECT
    c.*,
    -- Get the full name of the affiliate involved in the conflict.
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo,

-- Get the alias of the user responsible for managing the conflict.
u.alias AS usuario_responsable_alias,

-- Get the name of the territorial node associated with the conflict's location.
n.nombre AS nodo_nombre,

-- Include the full address of the property for context.
p.direccion AS direccion_piso
FROM
    sindicato_inq.conflictos c
    -- Join path to find the territorial node from the conflict.
    LEFT JOIN sindicato_inq.afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN sindicato_inq.pisos p ON a.piso_id = p.id
    LEFT JOIN sindicato_inq.bloques b ON p.bloque_id = b.id
    LEFT JOIN sindicato_inq.nodos n ON b.nodo_id = n.id
    -- Join to get the user responsible for the conflict.
    LEFT JOIN sindicato_inq.usuarios u ON c.usuario_responsable_id = u.id;

-- Create an enhanced view that includes all the information we need
CREATE OR REPLACE VIEW sindicato_inq.v_conflictos_enhanced AS
SELECT c.id, c.estado, c.ambito, c.causa, c.fecha_apertura, c.fecha_cierre, c.descripcion, c.resolucion, c.afiliada_id, c.usuario_responsable_id,

-- Afiliada info
a.nombre AS afiliada_nombre,
a.apellidos AS afiliada_apellidos,
CONCAT(a.nombre, ' ', a.apellidos) AS afiliada_nombre_completo,
a.num_afiliada,

-- Piso info
p.id AS piso_id,
p.direccion AS piso_direccion,
p.municipio AS piso_municipio,
p.cp AS piso_cp,

-- Bloque info
b.id AS bloque_id, b.direccion AS bloque_direccion,

-- Nodo info (from both sources - direct bloque relation and CP mapping)
COALESCE(n1.id, n2.id) AS nodo_id,
COALESCE(n1.nombre, n2.nombre) AS nodo_nombre,

-- Usuario responsable
u.alias AS usuario_responsable_alias,

-- Create a comprehensive label for selection
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