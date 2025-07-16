-- 4. AFILIADAS (Union Members/Tenants)
CREATE TABLE afiliadas (
    id SERIAL PRIMARY KEY,
    num_afiliada TEXT,
    nombre TEXT,
    apellidos TEXT,
    genero TEXT,
    email TEXT,
    regimen TEXT,
    estado TEXT DEFAULT NULL,
    fecha_alta TEXT,
    fecha_baja TEXT DEFAULT NULL piso_id INTEGER REFERENCES pisos (id) ON DELETE SET NULL
);

CREATE TABLE pisos (
    id INT NOT NULL,
    direccion TEXT NOT NULL,
    municipio,
    cp INTEGER NOT NULL,
    api TEXT,
    prop_vertical BOOLEAN NOT NULL,
    por_habitaciones BOOLEAN NOT NULL,
    bloque_id INTEGER REFERENCES bloques (id) ON DELETE SET NULL
);

-- 2. BLOQUES (Building Blocks/Properties)
CREATE TABLE bloques (
    id SERIAL PRIMARY KEY,
    direccion TEXT,
    estado TEXT,
    api TEXT,
    empresa_id INTEGER REFERENCES empresas (id) ON DELETE SET NULL
);

-- 5. CONFLICTOS (Conflicts/Disputes)
CREATE TABLE conflictos (
    id SERIAL PRIMARY KEY,
    estado TEXT DEFAULT NULL,
    ambito TEXT,
    afectada TEXT,
    causa TEXT,
    fecha_apertura TEXT,
    fecha_cierre TEXT,
    descripcion TEXT,
    resolucion TEXT,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE SET NULL,
    usuario_responsable_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL
);

CREATE TABLE diario_conflictos (
    id SERIAL PRIMARY KEY,
    estado TEXT DEFAULT NULL,
    ambito TEXT,
    afectada TEXT,
    causa TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conflicto_id INTEGER REFERENCES conflictos (id) ON DELETE SET NULL
);

-- 1. EMPRESAS (Companies/Property Management Companies)
CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    entramado_id TEXT,
    nombre TEXT,
    cif_nif_nie TEXT,
    directivos TEXT,
    api TEXT,
    direccion_fiscal TEXT
);

CREATE TABLE entramado_empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    descripcion TEXT,
);

CREATE TABLE facturacion (
    id INT NOT NULL,
    Cuota DECIMAL(8, 2) NOT NULL,
    Periodicidad SMALLINT NOT NULL,
    IBAN TEXT NOT NULL,
    afiliada_id INTEGER REFERENCES afiliadas (id) ON DELETE SET NULL
);

CREATE TABLE solicitudes (id INT NOT NULL);

-- 3. USUARIOS (System Users - Union Staff/Volunteers)
CREATE TABLE usuarios (
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