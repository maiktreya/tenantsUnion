-- =====================================================================
-- SCRIPT DE DATOS ARTIFICIALES PARA PRUEBAS (VERSIÓN REVISADA Y CORREGIDA)
-- =====================================================================
-- Este script crea el esquema completo, define las tablas, crea índices,
-- configura la autenticación, y puebla la base de datos con datos
-- artificiales.
--
-- REVISIÓN: El esquema de las tablas comunes ha sido sincronizado con
-- el script de producción '01-init-schema-and-data.sql'.
-- Las vistas han sido revisadas para garantizar que cada una
-- exponga una clave primaria consistente como 'id', alineándose con
-- las mejores prácticas para el consumo por parte de la API y el frontend.
-- =====================================================================

-- =====================================================================
-- PASO 0: CREACIÓN DEL ESQUEMA
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS sindicato_inq;

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- PASO 1: DEFINICIÓN DE TABLAS E ÍNDICES
-- =====================================================================

CREATE TABLE IF NOT EXISTS entramado_empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    alias TEXT UNIQUE,
    nombre TEXT,
    apellidos TEXT,
    email TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nodos (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS nodos_cp_mapping (
    cp INTEGER PRIMARY KEY,
    nodo_id INTEGER REFERENCES nodos (id) ON DELETE CASCADE NOT NULL
);

CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    entramado_id INTEGER REFERENCES entramado_empresas (id) ON DELETE SET NULL,
    nombre TEXT,
    cif_nif_nie TEXT UNIQUE,
    directivos TEXT,
    direccion_fiscal TEXT,
    url_notas TEXT
);

CREATE TABLE IF NOT EXISTS usuario_credenciales (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuarios (id) ON DELETE CASCADE,
    password_hash TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS usuario_roles (
    usuario_id INTEGER REFERENCES usuarios (id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles (id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, role_id)
);

CREATE TABLE IF NOT EXISTS bloques (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas (id) ON DELETE SET NULL,
    direccion TEXT UNIQUE
);

-- CORREGIDO: Añadido el campo 'propiedad' para alinear con el esquema final.
CREATE TABLE IF NOT EXISTS pisos (
    id SERIAL PRIMARY KEY,
    bloque_id INTEGER REFERENCES bloques (id) ON DELETE SET NULL,
    direccion TEXT NOT NULL UNIQUE,
    municipio TEXT,
    cp INTEGER,
    inmobiliaria TEXT, -- Agencia Inmobiliaria (atributo del piso)
    propiedad TEXT,
    prop_vertical TEXT, -- Propiedad Vertical (atributo del piso)
    por_habitaciones BOOLEAN,
    n_personas INTEGER,
    fecha_firma DATE,
    vpo BOOLEAN,
    vpo_date DATE
);

-- CORREGIDO: Eliminados campos 'trato_propiedad', 'seccion_sindical', 'comision'.
CREATE TABLE IF NOT EXISTS afiliadas (
    id SERIAL PRIMARY KEY,
    piso_id INTEGER REFERENCES pisos (id) ON DELETE SET NULL,
    num_afiliada TEXT UNIQUE,
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
    nivel_participacion TEXT
);

CREATE TABLE IF NOT EXISTS facturacion (
    id SERIAL PRIMARY KEY,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE CASCADE,
    cuota DECIMAL(8, 2),
    periodicidad SMALLINT,
    forma_pago TEXT,
    iban TEXT
);

CREATE TABLE IF NOT EXISTS asesorias (
    id SERIAL PRIMARY KEY,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE SET NULL,
    tecnica_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    estado TEXT,
    fecha_asesoria DATE,
    tipo_beneficiaria TEXT,
    tipo TEXT,
    resultado TEXT
);

CREATE TABLE IF NOT EXISTS conflictos (
    id SERIAL PRIMARY KEY,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE SET NULL,
    estado TEXT,
    ambito TEXT,
    causa TEXT,
    tarea_actual TEXT,
    fecha_apertura DATE,
    fecha_cierre DATE,
    descripcion TEXT,
    resolucion TEXT
);

CREATE TABLE IF NOT EXISTS diario_conflictos (
    id SERIAL PRIMARY KEY,
    conflicto_id INTEGER NOT NULL REFERENCES conflictos (id) ON DELETE CASCADE,
    usuario_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    estado TEXT,
    accion TEXT,
    notas TEXT,
    tarea_actual TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_nodos_cp_mapping_nodo_id ON nodos_cp_mapping (nodo_id);

CREATE INDEX IF NOT EXISTS idx_empresas_entramado_id ON empresas (entramado_id);

CREATE INDEX IF NOT EXISTS idx_usuario_roles_usuario_id ON usuario_roles (usuario_id);

CREATE INDEX IF NOT EXISTS idx_usuario_roles_role_id ON usuario_roles (role_id);

CREATE INDEX IF NOT EXISTS idx_bloques_empresa_id ON bloques (empresa_id);


CREATE INDEX IF NOT EXISTS idx_pisos_bloque_id ON pisos (bloque_id);

CREATE INDEX IF NOT EXISTS idx_afiliadas_piso_id ON afiliadas (piso_id);

CREATE INDEX IF NOT EXISTS idx_facturacion_afiliada_id ON facturacion (afiliada_id);

CREATE INDEX IF NOT EXISTS idx_asesorias_afiliada_id ON asesorias (afiliada_id);

CREATE INDEX IF NOT EXISTS idx_asesorias_tecnica_id ON asesorias (tecnica_id);

CREATE INDEX IF NOT EXISTS idx_conflictos_afiliada_id ON conflictos (afiliada_id);

CREATE INDEX IF NOT EXISTS idx_diario_conflictos_conflicto_id ON diario_conflictos (conflicto_id);

CREATE INDEX IF NOT EXISTS idx_diario_conflictos_usuario_id ON diario_conflictos (usuario_id);
