-- =====================================================================
-- ARCHIVO 01: CREACIÓN DE ESQUEMA E IMPORTACIÓN (VERSIÓN FINAL)
-- =====================================================================
-- Este script crea el esquema, importa los datos, y aplica mejoras
-- en la integridad referencial y la indexación para un diseño robusto.
-- =====================================================================

-- CREACIÓN DEL ESQUEMA
CREATE SCHEMA IF NOT EXISTS sindicato_inq;

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- PARTE 1: DEFINICIÓN DE LAS TABLAS FINALES Y NORMALIZADAS
-- =====================================================================

CREATE TABLE entramado_empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE,
    descripcion TEXT
);

CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    entramado_id INTEGER REFERENCES entramado_empresas (id) ON DELETE SET NULL,
    nombre TEXT,
    cif_nif_nie TEXT UNIQUE,
    directivos TEXT,
    api TEXT,
    direccion_fiscal TEXT
);

CREATE TABLE bloques (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas (id) ON DELETE SET NULL,
    direccion TEXT UNIQUE,
    estado TEXT,
    api TEXT
);

CREATE TABLE pisos (
    id SERIAL PRIMARY KEY,
    bloque_id INTEGER REFERENCES bloques (id) ON DELETE SET NULL,
    direccion TEXT NOT NULL UNIQUE,
    municipio TEXT,
    cp INTEGER,
    api TEXT,
    prop_vertical BOOLEAN,
    por_habitaciones BOOLEAN
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    alias TEXT UNIQUE,
    nombre TEXT,
    apellidos TEXT,
    email TEXT,
    roles TEXT
);

CREATE TABLE afiliadas (
    id SERIAL PRIMARY KEY,
    piso_id INTEGER REFERENCES pisos (id) ON DELETE SET NULL,
    num_afiliada TEXT UNIQUE,
    nombre TEXT,
    apellidos TEXT,
    cif TEXT UNIQUE,
    genero TEXT,
    email TEXT,
    telefono TEXT,
    regimen TEXT,
    estado TEXT,
    fecha_alta DATE,
    fecha_baja DATE
);

CREATE TABLE facturacion (
    id SERIAL PRIMARY KEY,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE CASCADE,
    cuota DECIMAL(8, 2),
    periodicidad SMALLINT,
    forma_pago TEXT,
    iban TEXT
);

CREATE TABLE asesorias (
    id SERIAL PRIMARY KEY,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE SET NULL,
    tecnica_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    estado TEXT,
    fecha_asesoria DATE,
    tipo_beneficiaria TEXT,
    tipo TEXT,
    resultado TEXT
);

CREATE TABLE conflictos (
    id SERIAL PRIMARY KEY,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE SET NULL,
    usuario_responsable_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    estado TEXT DEFAULT NULL,
    ambito TEXT,
    causa TEXT,
    fecha_apertura DATE,
    fecha_cierre DATE,
    descripcion TEXT,
    resolucion TEXT
);

CREATE TABLE acciones (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE diario_conflictos (
    id SERIAL PRIMARY KEY,
    conflicto_id INTEGER NOT NULL REFERENCES conflictos (id) ON DELETE CASCADE,
    usuario_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    accion_id INTEGER REFERENCES acciones (id) ON DELETE SET NULL,
    estado TEXT,
    ambito TEXT,
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- PARTE 1.5: CREACIÓN DE ÍNDICES PARA MEJORAR EL RENDIMIENTO
-- =====================================================================
CREATE INDEX idx_empresas_entramado_id ON empresas (entramado_id);

CREATE INDEX idx_bloques_empresa_id ON bloques (empresa_id);

CREATE INDEX idx_pisos_bloque_id ON pisos (bloque_id);

CREATE INDEX idx_afiliadas_piso_id ON afiliadas (piso_id);

CREATE INDEX idx_facturacion_afiliada_id ON facturacion (afiliada_id);

CREATE INDEX idx_asesorias_afiliada_id ON asesorias (afiliada_id);

CREATE INDEX idx_asesorias_tecnica_id ON asesorias (tecnica_id);

CREATE INDEX idx_conflictos_afiliada_id ON conflictos (afiliada_id);

CREATE INDEX idx_conflictos_usuario_responsable_id ON conflictos (usuario_responsable_id);

CREATE INDEX idx_diario_conflictos_conflicto_id ON diario_conflictos (conflicto_id);

CREATE INDEX idx_diario_conflictos_accion_id ON diario_conflictos (accion_id);

CREATE INDEX idx_diario_conflictos_usuario_id ON diario_conflictos (usuario_id);

-- =====================================================================
-- PARTE 2: LÓGICA DE IMPORTACIÓN CON TABLAS STAGING
-- =====================================================================

-- 2.1. Crear tablas Staging

-- FINAL VERSION: This table structure now exactly matches the final CSV file header.
CREATE TABLE staging_afiliadas (
    num_afiliada TEXT,
    nombre TEXT,
    apellidos TEXT,
    cif TEXT,
    genero TEXT,
    direccion TEXT,
    cuota TEXT,
    frecuencia_pago TEXT,
    forma_pago TEXT,
    cuenta_corriente TEXT,
    regimen TEXT,
    estado TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    email TEXT,
    telefono TEXT,
    fecha_alta TEXT,
    fecha_baja TEXT
);

CREATE TABLE staging_empresas (
    nombre TEXT,
    cif_nif_nie TEXT,
    entramado TEXT,
    directivos TEXT,
    api TEXT,
    direccion_fiscal TEXT,
    col_extra_1 TEXT,
    col_extra_2 TEXT,
    col_extra_3 TEXT,
    col_extra_4 TEXT,
    col_extra_5 TEXT,
    col_extra_6 TEXT
);

CREATE TABLE staging_bloques (
    direccion TEXT,
    estado TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    col_extra_1 TEXT,
    col_extra_2 TEXT,
    col_extra_3 TEXT
);

CREATE TABLE staging_pisos (
    direccion TEXT,
    estado TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    num_afiliadas TEXT,
    num_preafiliadas TEXT,
    num_inq_colaboradoras TEXT
);

CREATE TABLE staging_asesorias (
    estado TEXT,
    fecha_asesoria TEXT,
    fecha_contacto TEXT,
    fecha_finalizacion TEXT,
    tipo_beneficiaria TEXT,
    beneficiaria_nombre TEXT,
    tipo TEXT,
    tecnica_alias TEXT,
    resultado TEXT
);

CREATE TABLE staging_conflictos (
    estado TEXT,
    ambito TEXT,
    afectada TEXT,
    causa TEXT,
    fecha_apertura TEXT
);

CREATE TABLE staging_usuarios (
    codigo TEXT,
    nombre TEXT,
    apellidos TEXT,
    correo_electronico TEXT,
    telefono TEXT,
    grupo_por_defecto TEXT,
    grupos TEXT,
    roles TEXT
);

-- =====================================================================
-- PARTE B.1: MEJORA DE LA TABLA DE USUARIOS
-- =====================================================================
ALTER TABLE usuarios
ADD COLUMN is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN created_at TIMESTAMP
WITH
    TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- 2.2. Copiar datos desde CSV
COPY staging_afiliadas
FROM '/csv-data/Afiliadas.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

COPY staging_empresas
FROM '/csv-data/Empresas.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

COPY staging_bloques
FROM '/csv-data/Bloques.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

COPY staging_pisos
FROM '/csv-data/Pisos.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

COPY staging_asesorias
FROM '/csv-data/Asesorias.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

COPY staging_conflictos
FROM '/csv-data/Conflictos.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

COPY staging_usuarios
FROM '/csv-data/Usuarios.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

-- 2.3. Migrar datos de Staging a tablas finales

-- RE-ENABLED: This logic is valid as the 'entramado' column is present.
INSERT INTO
    entramado_empresas (nombre)
SELECT DISTINCT
    entramado
FROM staging_afiliadas
WHERE
    entramado IS NOT NULL
    AND entramado != '' ON CONFLICT (nombre) DO NOTHING;

INSERT INTO
    empresas (
        nombre,
        cif_nif_nie,
        directivos,
        api,
        direccion_fiscal,
        entramado_id
    )
SELECT s.nombre, s.cif_nif_nie, s.directivos, s.api, s.direccion_fiscal, ee.id
FROM
    staging_empresas s
    LEFT JOIN entramado_empresas ee ON s.entramado = ee.nombre ON CONFLICT (cif_nif_nie) DO NOTHING;

INSERT INTO
    bloques (
        direccion,
        empresa_id,
        estado,
        api
    )
SELECT s.direccion, e.id, s.estado, s.api
FROM
    staging_bloques s
    JOIN empresas e ON s.propiedad = e.nombre ON CONFLICT (direccion) DO NOTHING;

WITH BloqueCandidatos AS (
    SELECT
        p.direccion AS piso_direccion,
        b.id AS bloque_id,
        ROW_NUMBER() OVER(PARTITION BY p.direccion ORDER BY LENGTH(b.direccion) DESC) as rn
    FROM
        staging_pisos p
    JOIN
        bloques b ON p.direccion LIKE b.direccion || '%'
    WHERE
        p.direccion IS NOT NULL AND p.direccion != ''
),
MejorCoincidenciaBloque AS (
    SELECT piso_direccion, bloque_id FROM BloqueCandidatos WHERE rn = 1
)
INSERT INTO
    pisos (
        direccion,
        municipio,
        cp,
        api,
        bloque_id,
        prop_vertical,
        por_habitaciones
    )
SELECT
    s.direccion,
    TRIM((string_to_array(s.direccion, ','))[array_upper(string_to_array(s.direccion, ','), 1)]),
    CAST(NULLIF(regexp_replace((string_to_array(s.direccion, ','))[array_upper(string_to_array(s.direccion, ','), 1) - 1], '\D', '', 'g'), '') AS INTEGER),
    NULLIF(s.api, ''),
    mcb.bloque_id,
    FALSE,
    FALSE
FROM
    staging_pisos s
LEFT JOIN
    MejorCoincidenciaBloque mcb ON s.direccion = mcb.piso_direccion
WHERE
    s.direccion IS NOT NULL AND s.direccion != ''
ON CONFLICT (direccion) DO NOTHING;

INSERT INTO
    usuarios (
        alias,
        nombre,
        apellidos,
        email,
        roles
    )
SELECT
    codigo,
    nombre,
    apellidos,
    NULLIF(correo_electronico, ''),
    roles
FROM
    staging_usuarios ON CONFLICT (alias) DO NOTHING;

-- FINAL VERSION: This INSERT statement now correctly uses all available columns from the definitive CSV file.
INSERT INTO
    afiliadas (
        num_afiliada,
        nombre,
        apellidos,
        cif,
        genero,
        email,
        telefono,
        regimen,
        estado,
        fecha_alta,
        fecha_baja,
        piso_id
    )
SELECT
    s.num_afiliada,
    s.nombre,
    s.apellidos,
    s.cif,
    s.genero,
    s.email,
    s.telefono,
    s.regimen,
    s.estado,
    to_date (
        NULLIF(s.fecha_alta, ''),
        'DD/MM/YYYY'
    ),
    to_date (
        NULLIF(s.fecha_baja, ''),
        'DD/MM/YYYY'
    ),
    p.id
FROM
    staging_afiliadas s
    LEFT JOIN pisos p ON s.direccion = p.direccion ON CONFLICT (num_afiliada) DO NOTHING;

INSERT INTO
    facturacion (
        cuota,
        periodicidad,
        forma_pago,
        iban,
        afiliada_id
    )
SELECT
    CAST(
        REPLACE (s.cuota, ',', '.') AS DECIMAL(8, 2)
    ),
    CASE s.frecuencia_pago
        WHEN 'Anual' THEN 12
        WHEN 'Mensual' THEN 1
        ELSE 0
    END,
    s.forma_pago,
    s.cuenta_corriente,
    a.id
FROM
    staging_afiliadas s
    JOIN afiliadas a ON s.num_afiliada = a.num_afiliada ON CONFLICT (id) DO NOTHING;

INSERT INTO
    conflictos (
        afiliada_id,
        estado,
        ambito,
        causa,
        fecha_apertura
    )
SELECT a.id, s.estado, s.ambito, s.causa, to_date (
        NULLIF(s.fecha_apertura, ''), 'DD/MM/YYYY'
    )
FROM
    staging_conflictos s
    LEFT JOIN afiliadas a ON (
        a.nombre || ' ' || a.apellidos
    ) = s.afectada ON CONFLICT (id) DO NOTHING;

INSERT INTO
    asesorias (
        afiliada_id,
        tecnica_id,
        estado,
        tipo,
        fecha_asesoria,
        resultado,
        tipo_beneficiaria
    )
SELECT a.id, u.id, s.estado, s.tipo, to_date (
        NULLIF(s.fecha_asesoria, ''), 'DD/MM/YYYY'
    ), s.resultado, s.tipo_beneficiaria
FROM
    staging_asesorias s
    LEFT JOIN afiliadas a ON (
        a.nombre || ' ' || a.apellidos
    ) = s.beneficiaria_nombre
    LEFT JOIN usuarios u ON s.tecnica_alias = u.alias ON CONFLICT (id) DO NOTHING;

-- 2.4. Limpiar tablas Staging
DROP TABLE staging_afiliadas;

DROP TABLE staging_empresas;

DROP TABLE staging_bloques;

DROP TABLE staging_pisos;

DROP TABLE staging_asesorias;

DROP TABLE staging_conflictos;

DROP TABLE staging_usuarios;