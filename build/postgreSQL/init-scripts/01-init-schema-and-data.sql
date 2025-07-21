-- =====================================================================
-- ARCHIVO 01: CREACIÓN DE ESQUEMA E IMPORTACIÓN DE DATOS (VERSIÓN FINAL)
-- =====================================================================
-- Este script crea el esquema, todas las tablas finales y temporales,
-- importa los datos desde los CSV y finalmente migra los datos
-- a las tablas normalizadas antes de limpiar las temporales.
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
    entramado_id INTEGER REFERENCES entramado_empresas(id) ON DELETE SET NULL,
    nombre TEXT,
    cif_nif_nie TEXT UNIQUE,
    directivos TEXT,
    api TEXT,
    direccion_fiscal TEXT
);

CREATE TABLE bloques (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id) ON DELETE SET NULL,
    direccion TEXT UNIQUE,
    estado TEXT,
    api TEXT
);

-- ✅ Definición de la tabla 'pisos' (añadida)
CREATE TABLE pisos (
    id SERIAL PRIMARY KEY,
    bloque_id INTEGER REFERENCES bloques(id) ON DELETE SET NULL,
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
    piso_id INTEGER REFERENCES pisos(id) ON DELETE SET NULL,
    num_afiliada TEXT UNIQUE,
    nombre TEXT,
    apellidos TEXT,
    cif TEXT UNIQUE,
    genero TEXT,
    regimen TEXT,
    estado TEXT,
    fecha_alta DATE
);

CREATE TABLE facturacion (
    id SERIAL PRIMARY KEY,
    afiliada_id INTEGER REFERENCES afiliadas(id) ON DELETE SET NULL,
    cuota DECIMAL(8, 2),
    periodicidad SMALLINT,
    forma_pago TEXT,
    iban TEXT
);

CREATE TABLE asesorias (
    id SERIAL PRIMARY KEY,
    afiliada_id INTEGER REFERENCES afiliadas(id) ON DELETE SET NULL,
    tecnica_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    estado TEXT,
    fecha_asesoria DATE,
    tipo_beneficiaria TEXT,
    beneficiaria_nombre TEXT,
    tipo TEXT,
    resultado TEXT
);

CREATE TABLE conflictos (
    id SERIAL PRIMARY KEY,
    afiliada_id INTEGER REFERENCES afiliadas(id) ON DELETE SET NULL,
    usuario_responsable_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    estado TEXT,
    ambito TEXT,
    causa TEXT,
    fecha_apertura DATE
);

-- =====================================================================
-- PARTE 2: LÓGICA DE IMPORTACIÓN CON TABLAS STAGING
-- =====================================================================

-- 2.1. Crear tablas Staging
CREATE TABLE staging_afiliadas ( num_afiliada TEXT, nombre TEXT, apellidos TEXT, cif TEXT, genero TEXT, direccion TEXT, cuota TEXT, frecuencia_pago TEXT, forma_pago TEXT, cuenta_corriente TEXT, regimen TEXT, estado TEXT, api TEXT, propiedad TEXT, entramado TEXT );
CREATE TABLE staging_empresas ( nombre TEXT, cif_nif_nie TEXT, entramado TEXT, directivos TEXT, api TEXT, direccion_fiscal TEXT, num_afiliadas INT );
CREATE TABLE staging_bloques ( direccion TEXT, estado TEXT, api TEXT, propiedad TEXT, entramado TEXT, num_afiliadas INT );
CREATE TABLE staging_pisos ( direccion TEXT, municipio TEXT, cp TEXT, api TEXT, prop_vertical TEXT, por_habitaciones TEXT, bloque_direccion TEXT ); -- ✅ Staging para pisos.csv
CREATE TABLE staging_asesorias ( estado TEXT, fecha_asesoria TEXT, fecha_contacto TEXT, fecha_finalizacion TEXT, tipo_beneficiaria TEXT, beneficiaria_nombre TEXT, tipo TEXT, resultado TEXT, afiliada_id TEXT, tecnica_alias TEXT );
CREATE TABLE staging_conflictos ( estado TEXT, ambito TEXT, afectada TEXT, causa TEXT, fecha_apertura TEXT, fecha_cierre TEXT, descripcion TEXT, resolucion TEXT, afiliada_id TEXT, usuario_responsable_alias TEXT );
CREATE TABLE staging_usuarios ( alias TEXT, nombre TEXT, apellidos TEXT, email TEXT, telefono TEXT, grupo_por_defecto TEXT, grupos TEXT, roles TEXT, activo TEXT );

-- 2.2. Copiar datos desde CSV
COPY staging_afiliadas FROM '/csv-data/Afiliadas .csv' DELIMITER ';' CSV HEADER;
COPY staging_empresas(nombre, cif_nif_nie, entramado, directivos, api, direccion_fiscal) FROM '/csv-data/Empresas.csv' DELIMITER ';' CSV HEADER;
COPY staging_bloques(direccion, estado, api, propiedad, entramado) FROM '/csv-data/Bloques.csv' DELIMITER ';' CSV HEADER;
COPY staging_pisos FROM '/csv-data/pisos.csv' DELIMITER ';' CSV HEADER; -- ✅ Copiar datos de pisos.csv
COPY staging_asesorias FROM '/csv-data/Asesorias.csv' DELIMITER ';' CSV HEADER;
COPY staging_conflictos FROM '/csv-data/Conflictos.csv' DELIMITER ';' CSV HEADER;
COPY staging_usuarios FROM '/csv-data/Usuarios.csv' DELIMITER ';' CSV HEADER;

-- 2.3. Migrar datos de Staging a tablas finales (en orden de dependencia)
INSERT INTO entramado_empresas (nombre) SELECT DISTINCT entramado FROM staging_afiliadas WHERE entramado IS NOT NULL ON CONFLICT (nombre) DO NOTHING;
INSERT INTO empresas (nombre, entramado_id) SELECT DISTINCT s.propiedad, ee.id FROM staging_afiliadas s JOIN entramado_empresas ee ON s.entramado = ee.nombre WHERE s.propiedad IS NOT NULL ON CONFLICT (nombre) DO NOTHING;
INSERT INTO bloques (direccion, empresa_id) SELECT s.direccion, e.id FROM staging_bloques s JOIN empresas e ON s.propiedad = e.nombre ON CONFLICT (direccion) DO NOTHING;
INSERT INTO usuarios (alias, nombre, apellidos, email, roles) SELECT alias, nombre, apellidos, email, roles FROM staging_usuarios ON CONFLICT (alias) DO NOTHING;

-- ✅ Lógica de inserción para 'pisos' usando su propio CSV
INSERT INTO pisos (direccion, municipio, cp, api, prop_vertical, por_habitaciones, bloque_id)
SELECT s.direccion, s.municipio, s.cp::INTEGER, s.api, s.prop_vertical::BOOLEAN, s.por_habitaciones::BOOLEAN, b.id
FROM staging_pisos s
LEFT JOIN bloques b ON s.bloque_direccion = b.direccion
ON CONFLICT (direccion) DO NOTHING;

INSERT INTO afiliadas (num_afiliada, nombre, apellidos, cif, genero, regimen, estado, fecha_alta, piso_id)
SELECT s.num_afiliada, s.nombre, s.apellidos, s.cif, s.genero, s.regimen, s.estado, CURRENT_DATE, p.id
FROM staging_afiliadas s
LEFT JOIN pisos p ON s.direccion = p.direccion -- Unir por la dirección completa
ON CONFLICT (num_afiliada) DO NOTHING;

INSERT INTO facturacion (cuota, periodicidad, forma_pago, iban, afiliada_id) SELECT CAST(REPLACE(s.cuota, ',', '.') AS DECIMAL(8, 2)), CASE s.frecuencia_pago WHEN 'Mensual' THEN 1 ELSE 0 END, s.forma_pago, s.cuenta_corriente, a.id FROM staging_afiliadas s JOIN afiliadas a ON s.num_afiliada = a.num_afiliada ON CONFLICT (id) DO NOTHING;
INSERT INTO conflictos (afiliada_id, usuario_responsable_id, estado, causa, fecha_apertura) SELECT a.id, u.id, s.estado, s.causa, s.fecha_apertura::DATE FROM staging_conflictos s LEFT JOIN afiliadas a ON s.afiliada_id = a.num_afiliada LEFT JOIN usuarios u ON s.usuario_responsable_alias = u.alias ON CONFLICT (id) DO NOTHING;
INSERT INTO asesorias (afiliada_id, tecnica_id, estado, tipo, fecha_asesoria) SELECT a.id, u.id, s.estado, s.tipo, s.fecha_asesoria::DATE FROM staging_asesorias s LEFT JOIN afiliadas a ON s.afiliada_id = a.num_afiliada LEFT JOIN usuarios u ON s.tecnica_alias = u.alias ON CONFLICT (id) DO NOTHING;

-- 2.4. Limpiar tablas Staging
DROP TABLE staging_afiliadas;
DROP TABLE staging_empresas;
DROP TABLE staging_bloques;
DROP TABLE staging_pisos; -- ✅ Limpiar staging de pisos
DROP TABLE staging_asesorias;
DROP TABLE staging_conflictos;
DROP TABLE staging_usuarios;