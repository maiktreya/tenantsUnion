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
    regimen TEXT,
    estado TEXT,
    fecha_alta DATE
);

-- ✅ MEJORA: La facturación se elimina si se elimina la afiliada.
CREATE TABLE facturacion (
    id SERIAL PRIMARY KEY,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE CASCADE,
    cuota DECIMAL(8, 2),
    periodicidad SMALLINT,
    forma_pago TEXT,
    iban TEXT
);

-- ✅ MEJORA: Se elimina la columna redundante `beneficiaria_nombre`.
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

-- ✅ MEJORA: Se elimina la columna redundante `afectada`.
CREATE TABLE conflictos (
    id SERIAL PRIMARY KEY,
    estado TEXT DEFAULT NULL,
    ambito TEXT,
    causa TEXT,
    fecha_apertura DATE,
    fecha_cierre DATE,
    descripcion TEXT,
    resolucion TEXT,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE SET NULL,
    usuario_responsable_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL
);

-- Create the new table to store the types of actions.
CREATE TABLE acciones (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT -- An optional field for more details if needed in the future.
);
---- ✅ MEJORA: Las entradas del diario se eliminan si se elimina el conflicto.
--CREATE TABLE diario_conflictos (
--    id SERIAL PRIMARY KEY,
--    estado TEXT DEFAULT NULL,
--    ambito TEXT,
--    afectada TEXT,
--    causa TEXT,
--    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--    conflicto_id INTEGER REFERENCES conflictos (id) ON DELETE CASCADE
--);
-- =====================================================================
-- SUGGESTED UPDATE FOR: diario_conflictos
-- =====================================================================
-- This version corrects the data types, adds foreign key constraints for
-- data integrity, and includes a field to track the author of the note.

-- The final, complete definition for the conflict diary table.
CREATE TABLE diario_conflictos (
    id SERIAL PRIMARY KEY,

    -- Foreign key to the main conflict entry.
    conflicto_id INTEGER NOT NULL REFERENCES conflictos(id) ON DELETE CASCADE,

    -- Foreign key to the new 'acciones' table to categorize the entry.
    accion_id INTEGER REFERENCES acciones(id) ON DELETE SET NULL,

    -- Fields to track the state of the conflict at the time of this entry.
    estado TEXT,
    ambito TEXT,

    -- The main content of the note or update.
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_diario_conflictos_conflicto_id ON diario_conflictos(conflicto_id);
CREATE INDEX idx_diario_conflictos_accion_id ON diario_conflictos(accion_id);
CREATE INDEX idx_diario_conflictos_usuario_id ON diario_conflictos(usuario_id);

-- Add indexes for faster lookups on foreign keys.

-- =====================================================================
-- PARTE 1.5: CREACIÓN DE ÍNDICES PARA MEJORAR EL RENDIMIENTO
-- =====================================================================
-- ✅ MEJORA: Se añaden índices a todas las claves foráneas.

CREATE INDEX idx_empresas_entramado_id ON empresas (entramado_id);
CREATE INDEX idx_bloques_empresa_id ON bloques (empresa_id);
CREATE INDEX idx_pisos_bloque_id ON pisos (bloque_id);
CREATE INDEX idx_afiliadas_piso_id ON afiliadas (piso_id);
CREATE INDEX idx_facturacion_afiliada_id ON facturacion (afiliada_id);
CREATE INDEX idx_asesorias_afiliada_id ON asesorias (afiliada_id);
CREATE INDEX idx_asesorias_tecnica_id ON asesorias (tecnica_id);
CREATE INDEX idx_conflictos_afiliada_id ON conflictos (afiliada_id);
CREATE INDEX idx_conflictos_usuario_responsable_id ON conflictos (usuario_responsable_id);
CREATE INDEX idx_diario_conflictos_conflicto_id ON diario_conflictos(conflicto_id);
CREATE INDEX idx_diario_conflictos_accion_id ON diario_conflictos(accion_id);
CREATE INDEX idx_diario_conflictos_usuario_id ON diario_conflictos(usuario_id);
-- =====================================================================
-- PARTE 2: LÓGICA DE IMPORTACIÓN CON TABLAS STAGING
-- (El proceso de staging no se modifica para no romper la importación)
-- =====================================================================

-- 2.1. Crear tablas Staging
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
    entramado TEXT
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

-- ✅ NUEVO: Tabla staging para los pisos
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
-- Se añaden campos para el estado del usuario.
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

-- ✅ NUEVO: Carga de datos de pisos al área de staging
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
    JOIN entramado_empresas ee ON s.entramado = ee.nombre ON CONFLICT (cif_nif_nie) DO NOTHING;

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

-- ✅ CORREGIDO: Migración de datos para la tabla de pisos
WITH BloqueCandidatos AS (
    -- Para cada piso, se buscan todos los bloques cuya dirección sea un prefijo de la dirección del piso.
    -- Se asigna un número de fila, dando prioridad (rn=1) al bloque con la dirección más larga (la más específica).
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
    -- Se selecciona solo la mejor coincidencia para cada piso (la más larga).
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
    -- Extrae el municipio de la última parte del string de dirección, separada por comas.
    TRIM((string_to_array(s.direccion, ','))[array_upper(string_to_array(s.direccion, ','), 1)]),
    -- Extrae el código postal de la penúltima parte, lo limpia de caracteres no numéricos y lo convierte a entero.
    CAST(NULLIF(regexp_replace((string_to_array(s.direccion, ','))[array_upper(string_to_array(s.direccion, ','), 1) - 1], '\D', '', 'g'), '') AS INTEGER),
    NULLIF(s.api, ''),
    mcb.bloque_id,
    FALSE, -- Valor por defecto, no disponible en el CSV
    FALSE  -- Valor por defecto, no disponible en el CSV
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

INSERT INTO
    afiliadas (
        num_afiliada,
        nombre,
        apellidos,
        cif,
        genero,
        regimen,
        estado,
        fecha_alta,
        piso_id
    )
SELECT s.num_afiliada, s.nombre, s.apellidos, s.cif, s.genero, s.regimen, s.estado, CURRENT_DATE, p.id
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
        WHEN 'Mensual' THEN 1
        ELSE 0
    END,
    s.forma_pago,
    s.cuenta_corriente,
    a.id
FROM
    staging_afiliadas s
    JOIN afiliadas a ON s.num_afiliada = a.num_afiliada ON CONFLICT (id) DO NOTHING;

-- ✅ MEJORA: El INSERT ya no incluye la columna redundante `afectada`.
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

-- ✅ MEJORA: El INSERT ya no incluye la columna redundante `beneficiaria_nombre`.
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