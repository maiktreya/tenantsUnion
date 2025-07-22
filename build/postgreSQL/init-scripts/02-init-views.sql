-- =====================================================================
-- ARCHIVO 02: CREACIÓN DE VISTAS MATERIALIZADAS
-- =====================================================================
-- Este script se ejecuta después del 01. Asume que todas las tablas
-- y datos ya existen y crea las vistas para facilitar las consultas.
-- =====================================================================

SET search_path TO sindicato_inq, public;

-- VISTA 1: AFILIADAS (replica la estructura del CSV principal)
CREATE MATERIALIZED VIEW v_afiliadas AS
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
CREATE MATERIALIZED VIEW v_empresas AS
SELECT e.nombre AS "Nombre", e.cif_nif_nie AS "CIF/NIF/NIE", ee.nombre AS "Entramado", e.directivos AS "Directivos", e.api AS "API", e.direccion_fiscal AS "Dirección", COUNT(DISTINCT a.id) AS "Núm.Afiliadas"
FROM
    empresas e
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
    LEFT JOIN bloques b ON e.id = b.empresa_id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY
    e.id,
    ee.nombre;

-- VISTA 3: BLOQUES (replica la estructura de Bloques.csv con conteos)
CREATE MATERIALIZED VIEW v_bloques AS
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