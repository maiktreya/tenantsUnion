-- 1. ENTRAMADO_EMPRESAS
-- Create the schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS sindicato_inq;

CREATE TABLE sindicato_inq.entramado_empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    descripcion TEXT
);

-- 2. EMPRESAS (Companies)
CREATE TABLE sindicato_inq.empresas (
    id SERIAL PRIMARY KEY,
    entramado_id TEXT,
    nombre TEXT,
    cif_nif_nie TEXT,
    directivos TEXT,
    api TEXT,
    direccion_fiscal TEXT
);

-- 3. BLOQUES (Building Blocks / Properties)
CREATE TABLE sindicato_inq.bloques (
    id SERIAL PRIMARY KEY,
    direccion TEXT,
    estado TEXT,
    api TEXT,
    empresa_id INTEGER REFERENCES empresas (id) ON DELETE SET NULL
);

-- 4. PISOS (Apartments / Units)
CREATE TABLE sindicato_inq.pisos (
    id SERIAL PRIMARY KEY,
    direccion TEXT NOT NULL,
    municipio TEXT,
    cp INTEGER NOT NULL,
    api TEXT,
    prop_vertical BOOLEAN NOT NULL,
    por_habitaciones BOOLEAN NOT NULL,
    bloque_id INTEGER REFERENCES bloques (id) ON DELETE SET NULL
);

-- 5. USUARIOS (System Users)
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

-- 6. AFILIADAS (Union Members / Tenants)
CREATE TABLE sindicato_inq.afiliadas (
    id SERIAL PRIMARY KEY,
    num_afiliada TEXT,
    nombre TEXT,
    apellidos TEXT,
    genero TEXT,
    email TEXT,
    regimen TEXT,
    estado TEXT DEFAULT NULL,
    fecha_alta DATE,
    fecha_baja DATE DEFAULT NULL,
    piso_id INTEGER REFERENCES pisos (id) ON DELETE SET NULL
);

-- 7. CONFLICTOS (Conflicts / Disputes)
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
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE SET NULL,
    usuario_responsable_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL
);

-- 8. DIARIO_CONFLICTOS (Conflict Logs)
CREATE TABLE sindicato_inq.diario_conflictos (
    id SERIAL PRIMARY KEY,
    estado TEXT DEFAULT NULL,
    ambito TEXT,
    afectada TEXT,
    causa TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conflicto_id INTEGER REFERENCES conflictos (id) ON DELETE SET NULL
);

-- 9. FACTURACION (Billing)
CREATE TABLE sindicato_inq.facturacion (
    id SERIAL PRIMARY KEY,
    cuota DECIMAL(8, 2) NOT NULL,
    periodicidad SMALLINT NOT NULL,
    iban TEXT NOT NULL,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE SET NULL
);

-- 10. SOLICITUDES (Applications / Requests)
CREATE TABLE sindicato_inq.solicitudes (id SERIAL PRIMARY KEY);