-- For better data integrity, you could define ENUM types first:
-- CREATE TYPE genero_enum AS ENUM ('Mujer', 'Hombre', 'Otro', 'No especificado');
-- CREATE TYPE frecuencia_pago_enum AS ENUM ('Mensual', 'Trimestral', 'Semestral', 'Anual');
-- CREATE TYPE forma_pago_enum AS ENUM ('Domiciliación', 'Transferencia', 'Efectivo');
-- CREATE TYPE regimen_enum AS ENUM ('Alquiler', 'Propiedad', 'Otro');
-- CREATE TYPE estado_afiliado_enum AS ENUM ('Alta', 'Baja', 'Pendiente');

CREATE TABLE afiliados (
    -- Column 'Núm.Afiliada' from CSV
    id_afiliado VARCHAR(20) PRIMARY KEY,

    -- Columns 'Nombre' and 'Apellidos' from CSV
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,

    -- Column 'CIF' from CSV
    cif VARCHAR(20) NOT NULL UNIQUE,

    -- Column 'Género' from CSV
    genero VARCHAR(50), -- Recommended to use the 'genero_enum' type instead

    -- Column 'Dirección' from CSV
    direccion TEXT,

    -- Column 'Cuota' from CSV
    cuota NUMERIC(10, 2),

    -- Column 'Frecuencia de Pago' from CSV
    frecuencia_pago VARCHAR(50), -- Recommended to use 'frecuencia_pago_enum'

    -- Column 'Forma de Pago' from CSV
    forma_pago VARCHAR(50), -- Recommended to use 'forma_pago_enum'

    -- Column 'Cuenta Corriente' from CSV
    cuenta_bancaria VARCHAR(34), -- Standard length for IBAN

    -- Column 'Régimen' from CSV
    regimen VARCHAR(50), -- Recommended to use 'regimen_enum'

    -- Column 'Estado' from CSV
    estado VARCHAR(50) NOT NULL, -- Recommended to use 'estado_afiliado_enum'

    -- Columns 'API', 'Propiedad', 'Entramado' from CSV
    api TEXT,
    propiedad TEXT,
    entramado TEXT,

    -- Standard audit timestamps
    fecha_alta TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE,
    fecha_baja TIMESTAMP WITH TIME ZONE
);


--------------------------------------------------------------------


-- =====================================================================
-- ESQUEMA COMPLETO DEL SINDICATO DE INQUILINAS
-- =====================================================================
-- Este script define la estructura de datos completa, incluyendo
-- las correcciones para los campos faltantes (CIF, Forma de Pago)
-- y una mejora en la integridad referencial (entramado_id).
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
    -- Corregido: Se usa INTEGER y FOREIGN KEY para integridad de datos
    entramado_id INTEGER REFERENCES sindicato_inq.entramado_empresas(id) ON DELETE SET NULL,
    nombre TEXT,
    cif_nif_nie TEXT,
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

CREATE TABLE sindicato_inq.pisos (
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
    alias TEXT,
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
    -- Añadido: Campo CIF, crítico para la identificación
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
    periodicidad SMALLINT NOT NULL, -- Ej: 1 (Mensual), 3 (Trimestral), 12 (Anual)
    -- Añadido: Campo para la forma de pago
    forma_pago TEXT,
    iban TEXT,
    afiliada_id INTEGER REFERENCES sindicato_inq.afiliadas (id) ON DELETE SET NULL
);

-- =====================================================================
-- 3. TABLAS DE ACTIVIDAD Y CONFLICTOS
-- =====================================================================

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

CREATE TABLE sindicato_inq.diario_conflictos (
    id SERIAL PRIMARY KEY,
    estado TEXT DEFAULT NULL,
    ambito TEXT,
    afectada TEXT,
    causa TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conflicto_id INTEGER REFERENCES sindicato_inq.conflictos (id) ON DELETE SET NULL
);

CREATE TABLE sindicato_inq.solicitudes (
    id SERIAL PRIMARY KEY
    -- Esta tabla se puede desarrollar más adelante
);


-- =====================================================================
-- VISTA MATERIALIZADA v_afiliadas
-- =====================================================================
-- Esta vista une toda la información relevante para replicar la
-- estructura del CSV original, facilitando consultas y reportes.
-- Para actualizarla, se debe ejecutar: REFRESH MATERIALIZED VIEW sindicato_inq.v_afiliadas;
-- =====================================================================

CREATE MATERIALIZED VIEW sindicato_inq.v_afiliadas AS
SELECT
    a.num_afiliada AS "Núm.Afiliada",
    a.nombre AS "Nombre",
    a.apellidos AS "Apellidos",
    a.cif AS "CIF",
    a.genero AS "Género",
    -- Se reconstruye la dirección completa a partir de la tabla 'pisos'
    TRIM(CONCAT_WS(', ', p.direccion, p.municipio, p.cp::text)) AS "Dirección",
    f.cuota AS "Cuota",
    -- Se traduce el código numérico de periodicidad a texto
    CASE f.periodicidad
        WHEN 1 THEN 'Mensual'
        WHEN 3 THEN 'Trimestral'
        WHEN 6 THEN 'Semestral'
        WHEN 12 THEN 'Anual'
        ELSE 'Otra'
    END AS "Frecuencia de Pago",
    f.forma_pago AS "Forma de Pago",
    f.iban AS "Cuenta Corriente",
    a.regimen AS "Régimen",
    a.estado AS "Estado",
    e.api AS "API",
    e.nombre AS "Propiedad",
    ee.nombre AS "Entramado"
FROM
    sindicato_inq.afiliadas a
LEFT JOIN
    sindicato_inq.facturacion f ON a.id = f.afiliada_id
LEFT JOIN
    sindicato_inq.pisos p ON a.piso_id = p.id
LEFT JOIN
    sindicato_inq.bloques b ON p.bloque_id = b.id
LEFT JOIN
    sindicato_inq.empresas e ON b.empresa_id = e.id
LEFT JOIN
    sindicato_inq.entramado_empresas ee ON e.entramado_id = ee.id;