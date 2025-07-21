-- =====================================================================
-- ESQUEMA COMPLETO Y FINAL DEL SINDICATO DE INQUILINAS (v3)
-- =====================================================================

-- Creación del esquema
CREATE SCHEMA IF NOT EXISTS sindicato_inq;

-- =====================================================================
-- 1. TABLAS DE ESTRUCTURA Y PROPIEDADES
-- =====================================================================

CREATE TABLE sindicato_inq.entramado_empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    descripcion TEXT
);

CREATE TABLE sindicato_inq.empresas (
    id SERIAL PRIMARY KEY,
    entramado_id INTEGER REFERENCES sindicato_inq.entramado_empresas(id) ON DELETE SET NULL,
    nombre TEXT,
    cif_nif_nie TEXT UNIQUE,
    directivos TEXT,
    api TEXT,
    direccion_fiscal TEXT
);

CREATE TABLE sindicato_inq.bloques (
    id SERIAL PRIMARY KEY,
    direccion TEXT,
    estado TEXT,
    api TEXT,
    empresa_id INTEGER REFERENCES sindicato_inq.empresas (id) ON DELETE SET NULL
);

CREATE TABLE sindicax|to_inq.pisos (
    id SERIAL PRIMARY KEY,
    direccion TEXT NOT NULL,
    municipio TEXT,
    cp INTEGER,
    api TEXT,
    prop_vertical BOOLEAN,
    por_habitaciones BOOLEAN,
    bloque_id INTEGER REFERENCES sindicato_inq.bloques (id) ON DELETE SET NULL
);

-- =====================================================================
-- 2. TABLAS DE PERSONAS Y GESTIÓN
-- =====================================================================

CREATE TABLE sindicato_inq.usuarios (
    id SERIAL PRIMARY KEY,
    alias TEXT UNIQUE,
    nombre TEXT,
    apellidos TEXT,
    email TEXT,
    telefono TEXT,
    grupo_por_defecto TEXT,
    grupos TEXT,
    roles TEXT,
    activo TEXT DEFAULT NULL
);

CREATE TABLE sindicato_inq.afiliadas (
    id SERIAL PRIMARY KEY,
    num_afiliada TEXT UNIQUE,
    nombre TEXT,
    apellidos TEXT,
    cif TEXT UNIQUE,
    genero TEXT,
    email TEXT,
    regimen TEXT,
    estado TEXT DEFAULT NULL,
    fecha_alta DATE,
    fecha_baja DATE DEFAULT NULL,
    piso_id INTEGER REFERENCES sindicato_inq.pisos (id) ON DELETE SET NULL
);

CREATE TABLE sindicato_inq.facturacion (
    id SERIAL PRIMARY KEY,
    cuota DECIMAL(8, 2) NOT NULL,
    periodicidad SMALLINT NOT NULL,
    forma_pago TEXT,
    iban TEXT,
    afiliada_id INTEGER REFERENCES sindicato_inq.afiliadas (id) ON DELETE SET NULL
);

-- =====================================================================
-- 3. TABLAS DE ACTIVIDAD Y CONFLICTOS
-- =====================================================================

-- NUEVA TABLA para gestionar las asesorías
CREATE TABLE sindicato_inq.asesorias (
    id SERIAL PRIMARY KEY,
    estado TEXT,
    fecha_asesoria DATE,
    fecha_contacto DATE,
    fecha_finalizacion DATE,
    tipo_beneficiaria TEXT,
    beneficiaria_nombre TEXT,
    tipo TEXT,
    resultado TEXT,
    afiliada_id INTEGER REFERENCES sindicato_inq.afiliadas(id) ON DELETE SET NULL,
    tecnica_id INTEGER REFERENCES sindicato_inq.usuarios(id) ON DELETE SET NULL
);

CREATE TABLE sindicato_inq.conflictos (
    id SERIAL PRIMARY KEY,
    estado TEXT DEFAULT NULL,
    ambito TEXT,
    afectada TEXT,
    causa TEXT,
    fecha_apertura DATE,
    fecha_cierre DATE,
    descripcion TEXT,
    resolucion TEXT,
    afiliada_id INTEGER REFERENCES sindicato_inq.afiliadas (id) ON DELETE SET NULL,
    usuario_responsable_id INTEGER REFERENCES sindicato_inq.usuarios (id) ON DELETE SET NULL
);

-- =====================================================================
-- VISTAS MATERIALIZADAS PARA REPORTES
-- =====================================================================

-- VISTA 1: AFILIADAS (replica la estructura del CSV principal)
CREATE MATERIALIZED VIEW sindicato_inq.v_afiliadas AS
SELECT
    a.num_afiliada AS "Núm.Afiliada", a.nombre AS "Nombre", a.apellidos AS "Apellidos", a.cif AS "CIF", a.genero AS "Género",
    TRIM(CONCAT_WS(', ', p.direccion, p.municipio, p.cp::text)) AS "Dirección",
    f.cuota AS "Cuota",
    CASE f.periodicidad WHEN 1 THEN 'Mensual' WHEN 3 THEN 'Trimestral' WHEN 6 THEN 'Semestral' WHEN 12 THEN 'Anual' ELSE 'Otra' END AS "Frecuencia de Pago",
    f.forma_pago AS "Forma de Pago", f.iban AS "Cuenta Corriente", a.regimen AS "Régimen", a.estado AS "Estado", e.api AS "API", e.nombre AS "Propiedad", ee.nombre AS "Entramado"
FROM sindicato_inq.afiliadas a
LEFT JOIN sindicato_inq.facturacion f ON a.id = f.afiliada_id
LEFT JOIN sindicato_inq.pisos p ON a.piso_id = p.id
LEFT JOIN sindicato_inq.bloques b ON p.bloque_id = b.id
LEFT JOIN sindicato_inq.empresas e ON b.empresa_id = e.id
LEFT JOIN sindicato_inq.entramado_empresas ee ON e.entramado_id = ee.id;

-- VISTA 2: EMPRESAS (replica la estructura de Empresas.csv con conteos)
CREATE MATERIALIZED VIEW sindicato_inq.v_empresas AS
SELECT
    e.nombre AS "Nombre", e.cif_nif_nie AS "CIF/NIF/NIE", ee.nombre AS "Entramado", e.directivos AS "Directivos", e.api AS "API", e.direccion_fiscal AS "Dirección",
    COUNT(DISTINCT a.id) AS "Núm.Afiliadas"
FROM sindicato_inq.empresas e
LEFT JOIN sindicato_inq.entramado_empresas ee ON e.entramado_id = ee.id
LEFT JOIN sindicato_inq.bloques b ON e.id = b.empresa_id
LEFT JOIN sindicato_inq.pisos p ON b.id = p.bloque_id
LEFT JOIN sindicato_inq.afiliadas a ON p.id = a.piso_id
GROUP BY e.id, ee.nombre;

-- VISTA 3: BLOQUES (replica la estructura de Bloques.csv con conteos)
CREATE MATERIALIZED VIEW sindicato_inq.v_bloques AS
SELECT
    b.direccion AS "Dirección", b.estado AS "Estado", b.api AS "API", e.nombre AS "Propiedad", ee.nombre AS "Entramado",
    COUNT(DISTINCT a.id) AS "Núm.Afiliadas"
FROM sindicato_inq.bloques b
LEFT JOIN sindicato_inq.empresas e ON b.empresa_id = e.id
LEFT JOIN sindicato_inq.entramado_empresas ee ON e.entramado_id = ee.id
LEFT JOIN sindicato_inq.pisos p ON b.id = p.bloque_id
LEFT JOIN sindicato_inq.afiliadas a ON p.id = a.piso_id
GROUP BY b.id, e.nombre, ee.nombre;