-- =====================================================================
-- SCRIPT DE DATOS ARTIFICIALES PARA PRUEBAS (VERSIÓN COMPLETA Y AUTÓNOMA)
-- =====================================================================
-- Este script crea el esquema completo, define las tablas, crea índices,
-- configura la autenticación, genera las vistas y puebla la base de
-- datos con un conjunto de datos amplio y artificial.
-- =====================================================================

-- =====================================================================
-- PASO 0: CREACIÓN DEL ESQUEMA
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS sindicato_inq;

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- PASO 1: DEFINICIÓN DE TABLAS E ÍNDICES (de 01-init-schema-and-data.sql)
-- =====================================================================

CREATE TABLE IF NOT EXISTS entramado_empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    entramado_id INTEGER REFERENCES entramado_empresas (id) ON DELETE SET NULL,
    nombre TEXT,
    cif_nif_nie TEXT UNIQUE,
    directivos TEXT,
    api TEXT,
    direccion_fiscal TEXT
);

CREATE TABLE IF NOT EXISTS bloques (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas (id) ON DELETE SET NULL,
    direccion TEXT UNIQUE,
    estado TEXT,
    api TEXT
);

CREATE TABLE IF NOT EXISTS pisos (
    id SERIAL PRIMARY KEY,
    bloque_id INTEGER REFERENCES bloques (id) ON DELETE SET NULL,
    direccion TEXT NOT NULL UNIQUE,
    municipio TEXT,
    cp INTEGER,
    api TEXT,
    prop_vertical BOOLEAN,
    por_habitaciones BOOLEAN
);

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    alias TEXT UNIQUE,
    nombre TEXT,
    apellidos TEXT,
    email TEXT,
    roles TEXT
);

CREATE TABLE IF NOT EXISTS afiliadas (
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
    usuario_responsable_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    estado TEXT DEFAULT NULL,
    ambito TEXT,
    causa TEXT,
    fecha_apertura DATE,
    fecha_cierre DATE,
    descripcion TEXT,
    resolucion TEXT
);

CREATE TABLE IF NOT EXISTS acciones (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS diario_conflictos (
    id SERIAL PRIMARY KEY,
    conflicto_id INTEGER NOT NULL REFERENCES conflictos (id) ON DELETE CASCADE,
    usuario_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    accion_id INTEGER REFERENCES acciones (id) ON DELETE SET NULL,
    estado TEXT,
    ambito TEXT,
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
WITH
    TIME ZONE DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_empresas_entramado_id ON empresas (entramado_id);

CREATE INDEX IF NOT EXISTS idx_bloques_empresa_id ON bloques (empresa_id);

CREATE INDEX IF NOT EXISTS idx_pisos_bloque_id ON pisos (bloque_id);

CREATE INDEX IF NOT EXISTS idx_afiliadas_piso_id ON afiliadas (piso_id);

CREATE INDEX IF NOT EXISTS idx_facturacion_afiliada_id ON facturacion (afiliada_id);

CREATE INDEX IF NOT EXISTS idx_asesorias_afiliada_id ON asesorias (afiliada_id);

CREATE INDEX IF NOT EXISTS idx_asesorias_tecnica_id ON asesorias (tecnica_id);

CREATE INDEX IF NOT EXISTS idx_conflictos_afiliada_id ON conflictos (afiliada_id);

CREATE INDEX IF NOT EXISTS idx_conflictos_usuario_responsable_id ON conflictos (usuario_responsable_id);

CREATE INDEX IF NOT EXISTS idx_diario_conflictos_conflicto_id ON diario_conflictos (conflicto_id);

CREATE INDEX IF NOT EXISTS idx_diario_conflictos_accion_id ON diario_conflictos (accion_id);

CREATE INDEX IF NOT EXISTS idx_diario_conflictos_usuario_id ON diario_conflictos (usuario_id);

-- =====================================================================
-- PASO 2: INTEGRACIÓN DE NODOS (de 02-init-nodos.sql)
-- =====================================================================

CREATE TABLE IF NOT EXISTS sindicato_inq.nodos (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS sindicato_inq.nodos_cp_mapping (
    cp INTEGER PRIMARY KEY,
    nodo_id INTEGER REFERENCES nodos (id) ON DELETE CASCADE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_nodos_cp_mapping_nodo_id ON sindicato_inq.nodos_cp_mapping (nodo_id);

ALTER TABLE sindicato_inq.bloques
ADD COLUMN IF NOT EXISTS nodo_id INTEGER REFERENCES sindicato_inq.nodos (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_bloques_nodo_id ON sindicato_inq.bloques (nodo_id);

CREATE OR REPLACE FUNCTION sync_bloque_nodo()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sindicato_inq.bloques
    SET nodo_id = (SELECT nodo_id FROM sindicato_inq.nodos_cp_mapping WHERE cp = NEW.cp)
    WHERE id = NEW.bloque_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_sync_bloque_nodo ON sindicato_inq.pisos;

CREATE TRIGGER trigger_sync_bloque_nodo
AFTER INSERT OR UPDATE OF cp ON sindicato_inq.pisos
FOR EACH ROW EXECUTE FUNCTION sync_bloque_nodo();

-- =====================================================================
-- PASO 3: AUTENTICACIÓN Y AUTORIZACIÓN (de 03-init-userAuth.sql)
-- =====================================================================

CREATE TABLE IF NOT EXISTS sindicato_inq.usuario_credenciales (
    usuario_id INTEGER PRIMARY KEY REFERENCES sindicato_inq.usuarios (id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sindicato_inq.roles (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS sindicato_inq.usuario_roles (
    usuario_id INTEGER REFERENCES sindicato_inq.usuarios (id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES sindicato_inq.roles (id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_usuario_roles_usuario_id ON sindicato_inq.usuario_roles (usuario_id);

CREATE INDEX IF NOT EXISTS idx_usuario_roles_role_id ON sindicato_inq.usuario_roles (role_id);

-- =====================================================================
-- PASO 4: VISTAS PARA PRESENTACIÓN DE DATOS (de 04-init-views.sql)
-- =====================================================================

CREATE OR REPLACE VIEW v_afiliadas AS
SELECT a.num_afiliada, a.nombre, a.apellidos, a.cif, a.genero,
    TRIM(CONCAT_WS(', ', p.direccion, p.municipio, p.cp::text)) AS "Dirección",
    f.cuota,
    CASE f.periodicidad WHEN 1 THEN 'Mensual' WHEN 3 THEN 'Trimestral' WHEN 6 THEN 'Semestral' WHEN 12 THEN 'Anual' ELSE 'Otra' END AS "Frecuencia de Pago",
    f.forma_pago, f.iban, a.regimen, a.estado, e.api, e.nombre AS "Propiedad", ee.nombre AS "Entramado"
FROM afiliadas a
LEFT JOIN facturacion f ON a.id = f.afiliada_id
LEFT JOIN pisos p ON a.piso_id = p.id
LEFT JOIN bloques b ON p.bloque_id = b.id
LEFT JOIN empresas e ON b.empresa_id = e.id
LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id;

CREATE OR REPLACE VIEW v_empresas AS
SELECT e.nombre, e.cif_nif_nie, ee.nombre AS "Entramado", e.directivos, e.api, e.direccion_fiscal, COUNT(DISTINCT a.id) AS "Núm.Afiliadas"
FROM
    empresas e
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
    LEFT JOIN bloques b ON e.id = b.empresa_id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY
    e.id,
    ee.nombre;

CREATE OR REPLACE VIEW v_bloques AS
SELECT b.direccion, b.estado, b.api, e.nombre AS "Propiedad", ee.nombre AS "Entramado", COUNT(DISTINCT a.id) AS "Núm.Afiliadas"
FROM
    bloques b
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY
    b.id,
    e.nombre,
    ee.nombre;

CREATE OR REPLACE VIEW v_conflictos_con_afiliada AS
SELECT
    c.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo
FROM conflictos c
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id;

CREATE OR REPLACE VIEW v_diario_conflictos_con_afiliada AS
SELECT
    d.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo,
    u.alias AS autor_nota_alias,
    ac.nombre AS accion_nombre
FROM
    diario_conflictos d
    LEFT JOIN conflictos c ON d.conflicto_id = c.id
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN usuarios u ON d.usuario_id = u.id
    LEFT JOIN acciones ac ON d.accion_id = ac.id;

CREATE OR REPLACE VIEW v_conflictos_con_nodo AS
SELECT
    c.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo,
    u.alias AS usuario_responsable_alias,
    n.nombre AS nodo_nombre,
    p.direccion AS direccion_piso
FROM
    conflictos c
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN pisos p ON a.piso_id = p.id
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN nodos n ON b.nodo_id = n.id
    LEFT JOIN usuarios u ON c.usuario_responsable_id = u.id;

CREATE OR REPLACE VIEW v_conflictos_enhanced AS
SELECT
    c.id,
    c.estado,
    c.ambito,
    c.causa,
    c.fecha_apertura,
    c.fecha_cierre,
    c.descripcion,
    c.resolucion,
    c.afiliada_id,
    c.usuario_responsable_id,
    a.nombre AS afiliada_nombre,
    a.apellidos AS afiliada_apellidos,
    CONCAT(a.nombre, ' ', a.apellidos) AS afiliada_nombre_completo,
    a.num_afiliada,
    p.id AS piso_id,
    p.direccion AS piso_direccion,
    p.municipio AS piso_municipio,
    p.cp AS piso_cp,
    b.id AS bloque_id,
    b.direccion AS bloque_direccion,
    COALESCE(n1.id, n2.id) AS nodo_id,
    COALESCE(n1.nombre, n2.nombre) AS nodo_nombre,
    u.alias AS usuario_responsable_alias,
    CONCAT(
        'ID ',
        c.id,
        ' - ',
        COALESCE(
            p.direccion,
            b.direccion,
            'Sin dirección'
        ),
        ' | ',
        COALESCE(
            a.nombre || ' ' || a.apellidos,
            'Sin afiliada'
        ),
        CASE
            WHEN c.estado IS NOT NULL THEN ' [' || c.estado || ']'
            ELSE ''
        END
    ) AS conflict_label
FROM
    conflictos c
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN pisos p ON a.piso_id = p.id
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN nodos n1 ON b.nodo_id = n1.id
    LEFT JOIN nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN nodos n2 ON ncm.nodo_id = n2.id
    LEFT JOIN usuarios u ON c.usuario_responsable_id = u.id;

-- =====================================================================
-- PASO 5: POBLACIÓN DE DATOS ESTÁTICOS Y ARTIFICIALES (de 05 y artificial)
-- =====================================================================

-- Limpiar datos existentes para evitar conflictos de claves primarias
TRUNCATE TABLE diario_conflictos,
conflictos,
asesorias,
facturacion,
afiliadas,
usuarios,
pisos,
bloques,
empresas,
entramado_empresas,
acciones,
nodos,
nodos_cp_mapping,
roles,
usuario_credenciales,
usuario_roles
RESTART IDENTITY;

-- Datos Estáticos (necesarios para la aplicación)
INSERT INTO
    acciones (nombre)
VALUES ('nota simple'),
    (
        'nota localización propiedades'
    ),
    ('deposito fianza'),
    ('puerta a puerta'),
    ('comunicación enviada'),
    ('llamada'),
    ('acción'),
    ('reunión de negociación'),
    ('informe vulnerabilidad'),
    ('MASC'),
    ('justicia gratuita'),
    ('demanda'),
    ('sentencia') ON CONFLICT (nombre) DO NOTHING;

INSERT INTO
    roles (nombre, descripcion)
VALUES (
        'admin',
        'Administrador con todos los permisos'
    ),
    (
        'gestor',
        'Gestor de conflictos y afiliadas'
    ),
    (
        'sistemas',
        'Acceso de superusuario para mantenimiento'
    ) ON CONFLICT (nombre) DO NOTHING;

INSERT INTO
    nodos (nombre, descripcion)
VALUES (
        'Centro-Arganzuela-Retiro',
        'Agrupa los distritos de Centro, Arganzuela, Retiro, Moncloa y Chamberí.'
    ),
    (
        'Latina',
        'Nodo del distrito de Latina.'
    ),
    (
        'Este',
        'Agrupa los distritos del este de Madrid.'
    );

INSERT INTO
    nodos_cp_mapping (cp, nodo_id)
VALUES (
        28080,
        (
            SELECT id
            FROM nodos
            WHERE
                nombre = 'Centro-Arganzuela-Retiro'
        )
    ),
    (
        28081,
        (
            SELECT id
            FROM nodos
            WHERE
                nombre = 'Latina'
        )
    ),
    (
        28082,
        (
            SELECT id
            FROM nodos
            WHERE
                nombre = 'Este'
        )
    );

-- Población de Datos Artificiales
INSERT INTO
    entramado_empresas (nombre, descripcion)
VALUES (
        'Inversiones Inmobiliarias Globales',
        'Un conglomerado internacional de inversión en bienes raíces.'
    ),
    (
        'Gestión de Activos Peninsulares',
        'Una empresa centrada en la gestión de propiedades residenciales en España y Portugal.'
    ),
    (
        'Viviendas del Futuro S.L.',
        'Una promotora especializada en la construcción y alquiler de viviendas sostenibles.'
    );

INSERT INTO
    empresas (
        entramado_id,
        nombre,
        cif_nif_nie,
        directivos,
        api,
        direccion_fiscal
    )
VALUES (
        (
            SELECT id
            FROM entramado_empresas
            WHERE
                nombre = 'Inversiones Inmobiliarias Globales'
        ),
        'Fidere Vivienda Ficticia SL',
        'B81234567',
        'Juan Pérez, Ana García',
        'No',
        'Paseo de la Castellana, 1, Madrid, España'
    ),
    (
        (
            SELECT id
            FROM entramado_empresas
            WHERE
                nombre = 'Gestión de Activos Peninsulares'
        ),
        'Nestar Residencial Ficticia SA',
        'A87654321',
        'Carlos Sánchez, Laura Martínez',
        'Sí',
        'Calle de Serrano, 10, Madrid, España'
    ),
    (
        (
            SELECT id
            FROM entramado_empresas
            WHERE
                nombre = 'Viviendas del Futuro S.L.'
        ),
        'Elix Housing Ficticia SOCIMI',
        'A12345678',
        'Sofía Gómez, David Fernández',
        'No',
        'Avenida de América, 5, Madrid, España'
    );

INSERT INTO
    bloques (
        empresa_id,
        direccion,
        estado,
        api
    )
VALUES (
        (
            SELECT id
            FROM empresas
            WHERE
                nombre = 'Fidere Vivienda Ficticia SL'
        ),
        'Calle de la Invención, 10, 28080, Madrid',
        'Activo',
        'No'
    ),
    (
        (
            SELECT id
            FROM empresas
            WHERE
                nombre = 'Nestar Residencial Ficticia SA'
        ),
        'Avenida de la Imaginación, 20, 28081, Madrid',
        'Activo',
        'Sí'
    ),
    (
        (
            SELECT id
            FROM empresas
            WHERE
                nombre = 'Elix Housing Ficticia SOCIMI'
        ),
        'Plaza de la Creatividad, 5, 28082, Madrid',
        'En renovación',
        'No'
    );

INSERT INTO
    pisos (
        bloque_id,
        direccion,
        municipio,
        cp,
        api,
        prop_vertical,
        por_habitaciones
    )
VALUES (
        (
            SELECT id
            FROM bloques
            WHERE
                direccion = 'Calle de la Invención, 10, 28080, Madrid'
        ),
        'Calle de la Invención, 10, 1ºA, 28080, Madrid',
        'Madrid',
        28080,
        'No',
        true,
        false
    ),
    (
        (
            SELECT id
            FROM bloques
            WHERE
                direccion = 'Calle de la Invención, 10, 28080, Madrid'
        ),
        'Calle de la Invención, 10, 2ºB, 28080, Madrid',
        'Madrid',
        28080,
        'No',
        true,
        false
    ),
    (
        (
            SELECT id
            FROM bloques
            WHERE
                direccion = 'Avenida de la Imaginación, 20, 28081, Madrid'
        ),
        'Avenida de la Imaginación, 20, Bajo C, 28081, Madrid',
        'Madrid',
        28081,
        'Sí',
        true,
        false
    );

-- Forzar la actualización del nodo_id en bloques a través del trigger
UPDATE pisos
SET
    cp = 28080
WHERE
    direccion = 'Calle de la Invención, 10, 1ºA, 28080, Madrid';

UPDATE pisos
SET
    cp = 28081
WHERE
    direccion = 'Avenida de la Imaginación, 20, Bajo C, 28081, Madrid';

INSERT INTO
    usuarios (
        alias,
        nombre,
        apellidos,
        email,
        roles
    )
VALUES (
        'sumate',
        'Admin',
        'de Sistemas',
        'admin@example.com',
        'sistemas'
    ),
    (
        'test_gestor',
        'Gestor',
        'de Casos',
        'gestor@example.com',
        'gestor'
    ),
    (
        'test_user',
        'Usuario',
        'de Prueba',
        'user@example.com',
        NULL
    );

-- Contraseña para todos los usuarios: "password"
-- Ejemplo de inserción de datos (a modo de demostración)
INSERT INTO
    sindicato_inq.roles (nombre, descripcion)
VALUES (
        'admin',
        'Administrador con todos los permisos'
    );

INSERT INTO
    sindicato_inq.roles (nombre, descripcion)
VALUES (
        'gestor',
        'Gestor de conflictos y afiliadas'
    );

-- Para asignar el rol 'admin' al usuario con id 1:
-- INSERT INTO sindicato_inq.usuario_roles (usuario_id, role_id) VALUES (1, 1);

UPDATE sindicato_inq.usuario_credenciales
SET
    password_hash = '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
WHERE
    usuario_id = 1;

INSERT INTO
    sindicato_inq.usuario_roles (usuario_id, role_id)
VALUES (1, 1);

INSERT INTO
    afiliadas (
        piso_id,
        num_afiliada,
        nombre,
        apellidos,
        cif,
        genero,
        regimen,
        estado,
        fecha_alta
    )
VALUES (
        (
            SELECT id
            FROM pisos
            WHERE
                direccion = 'Calle de la Invención, 10, 1ºA, 28080, Madrid'
        ),
        'A0001',
        'Lucía',
        'García Pérez',
        '12345678A',
        'Mujer',
        'Alquiler',
        'Alta',
        '2023-01-15'
    ),
    (
        (
            SELECT id
            FROM pisos
            WHERE
                direccion = 'Calle de la Invención, 10, 2ºB, 28080, Madrid'
        ),
        'A0002',
        'Javier',
        'Rodríguez López',
        '87654321B',
        'Hombre',
        'Alquiler',
        'Alta',
        '2023-02-20'
    ),
    (
        (
            SELECT id
            FROM pisos
            WHERE
                direccion = 'Avenida de la Imaginación, 20, Bajo C, 28081, Madrid'
        ),
        'A0003',
        'María',
        'Sánchez Martín',
        '11223344C',
        'Mujer',
        'Alquiler',
        'Baja',
        '2023-03-25'
    );

INSERT INTO
    facturacion (
        afiliada_id,
        cuota,
        periodicidad,
        forma_pago,
        iban
    )
VALUES (
        (
            SELECT id
            FROM afiliadas
            WHERE
                num_afiliada = 'A0001'
        ),
        10.00,
        1,
        'Domiciliación',
        'ES9121000418450200051332'
    ),
    (
        (
            SELECT id
            FROM afiliadas
            WHERE
                num_afiliada = 'A0002'
        ),
        100.00,
        12,
        'Domiciliación',
        'ES9021000418450200051333'
    );

INSERT INTO
    asesorias (
        afiliada_id,
        tecnica_id,
        estado,
        fecha_asesoria,
        tipo_beneficiaria,
        tipo,
        resultado
    )
VALUES (
        (
            SELECT id
            FROM afiliadas
            WHERE
                num_afiliada = 'A0001'
        ),
        (
            SELECT id
            FROM usuarios
            WHERE
                alias = 'test_gestor'
        ),
        'Resuelto',
        '2024-05-23',
        'Afiliada',
        'Asesoría Gratuita',
        'Duda resuelta'
    );

INSERT INTO
    conflictos (
        afiliada_id,
        usuario_responsable_id,
        estado,
        ambito,
        causa,
        fecha_apertura,
        descripcion,
        resolucion
    )
VALUES (
        (
            SELECT id
            FROM afiliadas
            WHERE
                num_afiliada = 'A0001'
        ),
        (
            SELECT id
            FROM usuarios
            WHERE
                alias = 'test_gestor'
        ),
        'Abierto',
        'Afiliada',
        'No renovación',
        '2025-01-17',
        'El propietario se niega a renovar el contrato sin justificación.',
        NULL
    ),
    (
        (
            SELECT id
            FROM afiliadas
            WHERE
                num_afiliada = 'A0002'
        ),
        (
            SELECT id
            FROM usuarios
            WHERE
                alias = 'test_gestor'
        ),
        'Cerrado',
        'Afiliada',
        'Fianza',
        '2024-11-19',
        'El propietario no devuelve la fianza alegando daños inexistentes.',
        'Se recuperó la fianza tras la mediación.'
    );

INSERT INTO
    diario_conflictos (
        conflicto_id,
        usuario_id,
        accion_id,
        estado,
        ambito,
        notas,
        created_at
    )
VALUES (
        (
            SELECT id
            FROM conflictos
            WHERE
                causa = 'No renovación'
        ),
        (
            SELECT id
            FROM usuarios
            WHERE
                alias = 'test_gestor'
        ),
        (
            SELECT id
            FROM acciones
            WHERE
                nombre = 'llamada'
        ),
        'Abierto',
        'Afiliada',
        'Primer contacto con la afiliada para recabar información.',
        '2025-01-17 10:00:00'
    ),
    (
        (
            SELECT id
            FROM conflictos
            WHERE
                causa = 'Fianza'
        ),
        (
            SELECT id
            FROM usuarios
            WHERE
                alias = 'test_gestor'
        ),
        (
            SELECT id
            FROM acciones
            WHERE
                nombre = 'comunicación enviada'
        ),
        'En proceso',
        'Afiliada',
        'Se envía burofax al propietario reclamando la devolución de la fianza.',
        '2024-11-20 12:30:00'
    );