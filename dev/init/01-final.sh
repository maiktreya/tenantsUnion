#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Execute the SQL commands using the psql client
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

-- ===================================================================
-- PART 1: CREATE STAGING TABLES
-- Description: These tables are temporary and match the CSV columns.
-- ===================================================================
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
    num_afiliadas INT -- This column will be ignored on import
);

CREATE TABLE staging_bloques (
    direccion TEXT,
    estado TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    num_afiliadas INT -- Ignored
);

CREATE TABLE staging_asesorias (
    estado TEXT,
    fecha_asesoria TEXT,
    fecha_contacto TEXT,
    fecha_finalizacion TEXT,
    tipo_beneficiaria TEXT,
    beneficiaria_nombre TEXT,
    tipo TEXT,
    resultado TEXT,
    afiliada_id TEXT, -- Will match num_afiliada
    tecnica_alias TEXT -- Will match alias in 'usuarios'
);

CREATE TABLE staging_conflictos (
    estado TEXT,
    ambito TEXT,
    afectada TEXT,
    causa TEXT,
    fecha_apertura TEXT,
    fecha_cierre TEXT,
    descripcion TEXT,
    resolucion TEXT,
    afiliada_id TEXT, -- num_afiliada
    usuario_responsable_alias TEXT -- alias
);

CREATE TABLE staging_usuarios (
    alias TEXT,
    nombre TEXT,
    apellidos TEXT,
    email TEXT,
    telefono TEXT,
    grupo_por_defecto TEXT,
    grupos TEXT,
    roles TEXT,
    activo TEXT
);


-- ===================================================================
-- PART 2: COPY DATA FROM CSVs INTO STAGING TABLES
-- Description: Uses the efficient COPY command. Assumes CSVs are in /data/
-- ===================================================================
COPY staging_afiliadas FROM '/data/Afiliadas .csv' DELIMITER ';' CSV HEADER;
COPY staging_empresas(nombre, cif_nif_nie, entramado, directivos, api, direccion_fiscal) FROM '/data/Empresas.csv' DELIMITER ';' CSV HEADER;
COPY staging_bloques(direccion, estado, api, propiedad, entramado) FROM '/data/Bloques.csv' DELIMITER ';' CSV HEADER;
COPY staging_asesorias FROM '/data/Asesorias.csv' DELIMITER ';' CSV HEADER;
COPY staging_conflictos FROM '/data/Conflictos.csv' DELIMITER ';' CSV HEADER;
COPY staging_usuarios FROM '/data/Usuarios.csv' DELIMITER ';' CSV HEADER;


-- ===================================================================
-- PART 3: MIGRATE DATA FROM STAGING TO FINAL TABLES
-- Description: Uses INSERT...SELECT to populate the normalized schema.
-- The order is critical to respect foreign key constraints.
-- ON CONFLICT DO NOTHING handles duplicates gracefully.
-- ===================================================================

-- 1. Populate lookup tables first (Entramado, Empresas, Usuarios)
INSERT INTO sindicato_inq.entramado_empresas (nombre)
SELECT DISTINCT entramado FROM staging_afiliadas WHERE entramado IS NOT NULL
UNION
SELECT DISTINCT entramado FROM staging_empresas WHERE entramado IS NOT NULL
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO sindicato_inq.empresas (nombre, cif_nif_nie, directivos, api, direccion_fiscal, entramado_id)
SELECT DISTINCT
    s.propiedad,
    s.cif_nif_nie,
    s.directivos,
    s.api,
    s.direccion_fiscal,
    ee.id
FROM (
    SELECT propiedad, NULL as cif_nif_nie, NULL as directivos, api, NULL as direccion_fiscal, entramado FROM staging_afiliadas
    UNION ALL
    SELECT nombre, cif_nif_nie, directivos, api, direccion_fiscal, entramado FROM staging_empresas
) s
JOIN sindicato_inq.entramado_empresas ee ON s.entramado = ee.nombre
WHERE s.propiedad IS NOT NULL
ON CONFLICT (cif_nif_nie) DO NOTHING;

INSERT INTO sindicato_inq.usuarios (alias, nombre, apellidos, email, telefono, grupo_por_defecto, grupos, roles, activo)
SELECT alias, nombre, apellidos, email, telefono, grupo_por_defecto, grupos, roles, activo FROM staging_usuarios
ON CONFLICT (alias) DO NOTHING;

-- 2. Populate Bloques and Pisos
INSERT INTO sindicato_inq.bloques (direccion, estado, api, empresa_id)
SELECT
    s.direccion,
    s.estado,
    s.api,
    e.id
FROM staging_bloques s
JOIN sindicato_inq.empresas e ON s.propiedad = e.nombre
ON CONFLICT (id) DO NOTHING; -- Assuming you'll add a unique constraint on address

INSERT INTO sindicato_inq.pisos (direccion, municipio, cp, bloque_id)
SELECT DISTINCT
    split_part(s.direccion, ',', 1), -- Calle Fresno de Cantespino, 3, 1 B
    split_part(s.direccion, ',', 4), -- Madrid
    CAST(TRIM(split_part(s.direccion, ',', 3)) AS INTEGER), -- 28051
    b.id
FROM staging_afiliadas s
LEFT JOIN sindicato_inq.bloques b ON b.direccion LIKE split_part(s.direccion, ',', 1) || '%' -- Basic matching
ON CONFLICT (id) DO NOTHING; -- Assuming unique constraint on full address

-- 3. Populate Afiliadas and Facturacion
INSERT INTO sindicato_inq.afiliadas (num_afiliada, nombre, apellidos, cif, genero, email, regimen, estado, fecha_alta, piso_id)
SELECT
    s.num_afiliada,
    s.nombre,
    s.apellidos,
    s.cif,
    s.genero,
    NULL, -- No email in this CSV
    s.regimen,
    s.estado,
    CURRENT_DATE, -- Or parse from another field if available
    p.id
FROM staging_afiliadas s
LEFT JOIN sindicato_inq.pisos p ON p.direccion LIKE split_part(s.direccion, ',', 1) || '%'
ON CONFLICT (num_afiliada) DO NOTHING;

INSERT INTO sindicato_inq.facturacion (cuota, periodicidad, forma_pago, iban, afiliada_id)
SELECT
    CAST(REPLACE(s.cuota, ',', '.') AS DECIMAL(8, 2)),
    CASE s.frecuencia_pago
        WHEN 'Mensual' THEN 1
        WHEN 'Trimestral' THEN 3
        WHEN 'Anual' THEN 12
        ELSE 0
    END,
    s.forma_pago,
    s.cuenta_corriente,
    a.id
FROM staging_afiliadas s
JOIN sindicato_inq.afiliadas a ON s.num_afiliada = a.num_afiliada
ON CONFLICT (id) DO NOTHING;

-- 4. Populate Asesorias and Conflictos
INSERT INTO sindicato_inq.asesorias (estado, fecha_asesoria, tipo_beneficiaria, beneficiaria_nombre, tipo, resultado, afiliada_id, tecnica_id)
SELECT
    s.estado,
    s.fecha_asesoria::DATE,
    s.tipo_beneficiaria,
    s.beneficiaria_nombre,
    s.tipo,
    s.resultado,
    a.id,
    u.id
FROM staging_asesorias s
LEFT JOIN sindicato_inq.afiliadas a ON s.afiliada_id = a.num_afiliada
LEFT JOIN sindicato_inq.usuarios u ON s.tecnica_alias = u.alias
ON CONFLICT (id) DO NOTHING;

INSERT INTO sindicato_inq.conflictos(estado, ambito, afectada, causa, fecha_apertura, afiliada_id, usuario_responsable_id)
SELECT
    s.estado, s.ambito, s.afectada, s.causa, s.fecha_apertura::DATE,
    a.id,
    u.id
FROM staging_conflictos s
LEFT JOIN sindicato_inq.afiliadas a ON s.afiliada_id = a.num_afiliada
LEFT JOIN sindicato_inq.usuarios u ON s.usuario_responsable_alias = u.alias
ON CONFLICT (id) DO NOTHING;


-- ===================================================================
-- PART 4: CLEANUP
-- Description: Drop the temporary staging tables.
-- ===================================================================
DROP TABLE staging_afiliadas;
DROP TABLE staging_empresas;
DROP TABLE staging_bloques;
DROP TABLE staging_asesorias;
DROP TABLE staging_conflictos;
DROP TABLE staging_usuarios;

EOSQL