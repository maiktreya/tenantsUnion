-- =====================================================================
-- ARCHIVO 01: CREACIÓN DE ESQUEMA E IMPORTACIÓN (VERSIÓN FINAL MEJORADA)
-- =====================================================================
-- Este script crea el esquema, importa los datos, y aplica mejoras
-- en la integridad referencial y la indexación para un diseño robusto.
-- Se han refactorizado las tablas para eliminar datos duplicados y
-- asegurar que cada dato resida en su tabla lógica correspondiente.
-- =====================================================================

-- CREACIÓN DEL ESQUEMA
CREATE SCHEMA IF NOT EXISTS sindicato_inq;

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- PARTE 1: DEFINICIÓN DE LAS TABLAS FINALES Y NORMALIZADAS (REFINADO)
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
    direccion_fiscal TEXT,
    url_notas TEXT
);

CREATE TABLE bloques (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas (id) ON DELETE SET NULL,
    direccion TEXT UNIQUE
);

CREATE TABLE pisos (
    id SERIAL PRIMARY KEY,
    bloque_id INTEGER REFERENCES bloques (id) ON DELETE SET NULL,
    direccion TEXT NOT NULL UNIQUE,
    municipio TEXT,
    cp INTEGER,
    inmobiliaria TEXT, -- Agencia Inmobiliaria (atributo del piso)
    prop_vertical TEXT, -- Propiedad Vertical (atributo del piso)
    por_habitaciones BOOLEAN,
    n_personas INTEGER,
    fecha_firma DATE,
    vpo BOOLEAN,
    vpo_date DATE
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    alias TEXT UNIQUE,
    nombre TEXT,
    apellidos TEXT,
    email TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS sindicato_inq.afiliadas_num_afiliada_seq;

CREATE TABLE sindicato_inq.afiliadas (
    id SERIAL PRIMARY KEY,
    piso_id INTEGER REFERENCES sindicato_inq.pisos (id) ON DELETE SET NULL,
    num_afiliada TEXT UNIQUE, -- Notice: NO DEFAULT value here yet!
    nombre TEXT,
    apellidos TEXT,
    cif TEXT UNIQUE,
    fecha_nac DATE,
    genero TEXT,
    email TEXT,
    telefono TEXT,
    estado TEXT,
    regimen TEXT,
    fecha_alta DATE,
    fecha_baja DATE,
    trato_propiedad BOOLEAN,
    nivel_participacion TEXT
);

CREATE TABLE sindicato_inq.facturacion (
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
    tarea_actual TEXT,
    fecha_apertura DATE,
    fecha_cierre DATE,
    descripcion TEXT,
    resolucion TEXT
);

CREATE TABLE diario_conflictos (
    id SERIAL PRIMARY KEY,
    conflicto_id INTEGER NOT NULL REFERENCES conflictos (id) ON DELETE CASCADE,
    usuario_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    estado TEXT,
    accion TEXT,
    notas TEXT,
    tarea_actual TEXT,
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

CREATE INDEX idx_diario_conflictos_usuario_id ON diario_conflictos (usuario_id);

-- =====================================================================
-- PARTE 2: LÓGICA DE IMPORTACIÓN CON TABLAS STAGING
-- =====================================================================

-- 2.1. Crear tablas Staging
CREATE TABLE staging_afiliadas (
    num_afiliada TEXT,
    nombre TEXT,
    apellidos TEXT,
    cif TEXT,
    genero TEXT,
    email TEXT,
    telefono TEXT,
    seccion_sindical TEXT,
    nivel_participacion TEXT,
    comision TEXT,
    direccion TEXT,
    municipio TEXT,
    codigo_postal TEXT,
    cuota TEXT,
    frecuencia_pago TEXT,
    forma_pago TEXT,
    cuenta_corriente TEXT,
    regimen TEXT,
    estado TEXT,
    fecha_alta TEXT,
    fecha_baja TEXT,
    prop_vertical TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    fecha_nac TEXT
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
    num_inq_colaboradoras TEXT,
    prop_vertical TEXT
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
    grupos TEXT
);

-- =====================================================================
-- PARTE 2.2: IMPORTACIÓN DE DATOS DESDE CSV
-- =====================================================================
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

-- =====================================================================
-- PARTE 2.3: MIGRACIÓN DE DATOS (REFACTORIZADA Y CORREGIDA)
-- =====================================================================

INSERT INTO
    entramado_empresas (nombre)
SELECT DISTINCT
    entramado
FROM staging_afiliadas
WHERE
    entramado IS NOT NULL
    AND entramado != ''
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO
    empresas (
        nombre,
        cif_nif_nie,
        directivos,
        direccion_fiscal,
        entramado_id
    )
SELECT s.nombre, s.cif_nif_nie, s.directivos, s.direccion_fiscal, ee.id
FROM
    staging_empresas s
    LEFT JOIN entramado_empresas ee ON s.entramado = ee.nombre
ON CONFLICT (cif_nif_nie) DO NOTHING;

-- Corregido: Ahora se vincula la empresa por su nombre desde staging_bloques
INSERT INTO
    bloques (direccion, empresa_id)
SELECT s.direccion, e.id
FROM staging_bloques s
    LEFT JOIN empresas e ON s.propiedad = e.nombre
ON CONFLICT (direccion) DO NOTHING;

-- Se crean los pisos a partir de las direcciones únicas en staging_afiliadas.
-- Este es el primer paso para asegurar que cada piso exista antes de ser referenciado.
INSERT INTO
    pisos (direccion, municipio, cp)
SELECT DISTINCT
    s.direccion,
    s.municipio,
    CAST(
        NULLIF(s.codigo_postal, '') AS INTEGER
    )
FROM staging_afiliadas s
WHERE
    s.direccion IS NOT NULL
    AND s.direccion != ''
ON CONFLICT (direccion) DO NOTHING;

-- *** NUEVO PASO: Actualizar 'pisos' con la información de propiedad de 'staging_afiliadas' ***
-- Se enriquece la tabla de pisos con los datos que le pertenecen.
UPDATE pisos p

SET
    inmobiliaria = s.api,
    prop_vertical = CASE
        WHEN s.prop_vertical = 'Si' THEN TRUE
        ELSE FALSE
    END
FROM (
        -- Usamos una subconsulta para obtener una única fila por dirección
        SELECT DISTINCT
            ON (sa.direccion) sa.direccion, sa.api, sp.prop_vertical
        FROM
            staging_afiliadas sa
            LEFT JOIN staging_pisos sp ON sa.direccion = sp.direccion
        WHERE
            sa.direccion IS NOT NULL
            AND sa.direccion != ''
    ) AS s
WHERE
    p.direccion = s.direccion;

-- *** PASO REFACTORIZADO: Insertar en 'afiliadas' con una estructura limpia ***
INSERT INTO
    afiliadas (
        piso_id,
        num_afiliada,
        nombre,
        apellidos,
        cif,
        fecha_nac,
        genero,
        email,
        telefono,
        estado,
        regimen,
        fecha_alta,
        fecha_baja,
        trato_propiedad,
        nivel_participacion
    )
SELECT p.id, s.num_afiliada, s.nombre, s.apellidos, s.cif, to_date(
        NULLIF(s.fecha_nac, ''), 'YYYY-MM-DD'
    ), s.genero, s.email, s.telefono, s.estado, s.regimen, to_date(
        NULLIF(s.fecha_alta, ''), 'DD/MM/YYYY'
    ), to_date(
        NULLIF(s.fecha_baja, ''), 'DD/MM/YYYY'
    ), FALSE, s.nivel_participacion
FROM staging_afiliadas s
    JOIN pisos p ON s.direccion = p.direccion -- Se usa JOIN para asegurar la vinculación
ON CONFLICT (num_afiliada) DO NOTHING;

-- (El resto de las inserciones para usuarios, facturacion, conflictos, etc., permanecen igual)
INSERT INTO
    usuarios (
        alias,
        nombre,
        apellidos,
        email
    )
SELECT codigo, nombre, apellidos, NULLIF(correo_electronico, ''),
FROM staging_usuarios
ON CONFLICT (alias) DO NOTHING;

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
        REPLACE(s.cuota, ',', '.') AS DECIMAL(8, 2)
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
    JOIN afiliadas a ON s.num_afiliada = a.num_afiliada
ON CONFLICT (id) DO NOTHING;

INSERT INTO
    conflictos (
        afiliada_id,
        estado,
        ambito,
        causa,
        fecha_apertura
    )
SELECT a.id, s.estado, s.ambito, s.causa, to_date(
        NULLIF(s.fecha_apertura, ''), 'DD/MM/YYYY'
    )
FROM
    staging_conflictos s
    LEFT JOIN afiliadas a ON (
        a.nombre || ' ' || a.apellidos
    ) = s.afectada
ON CONFLICT (id) DO NOTHING;

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
SELECT a.id, u.id, s.estado, s.tipo, to_date(
        NULLIF(s.fecha_asesoria, ''), 'DD/MM/YYYY'
    ), s.resultado, s.tipo_beneficiaria
FROM
    staging_asesorias s
    LEFT JOIN afiliadas a ON (
        a.nombre || ' ' || a.apellidos
    ) = s.beneficiaria_nombre
    LEFT JOIN usuarios u ON s.tecnica_alias = u.alias
ON CONFLICT (id) DO NOTHING;

-- Añade la restricción pero no la valida en los datos existentes
ALTER TABLE sindicato_inq.facturacion
ADD CONSTRAINT chk_iban_format CHECK (
    iban IS NULL
    OR iban ~ '^ES[0-9]{22}$'
) NOT VALID;

-- 2.4. Limpiar tablas Staging
DROP TABLE staging_afiliadas;

DROP TABLE staging_empresas;

DROP TABLE staging_bloques;

DROP TABLE staging_pisos;

DROP TABLE staging_asesorias;

DROP TABLE staging_conflictos;

DROP TABLE staging_usuarios;