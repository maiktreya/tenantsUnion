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
-- PASO 1: DEFINICIÓN DE TABLAS E ÍNDICES
-- =====================================================================

-- Tablas principales ordenadas por dependencias
CREATE TABLE IF NOT EXISTS entramado_empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS nodos (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT,
    usuario_responsable_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS nodos_cp_mapping (
    cp INTEGER PRIMARY KEY,
    nodo_id INTEGER REFERENCES nodos (id) ON DELETE CASCADE NOT NULL
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
    roles TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    direccion TEXT UNIQUE,
    estado TEXT,
    api TEXT,
    nodo_id INTEGER REFERENCES nodos (id) ON DELETE SET NULL
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

CREATE TABLE IF NOT EXISTS afiliadas (
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

CREATE INDEX IF NOT EXISTS idx_bloques_nodo_id ON bloques (nodo_id);

CREATE INDEX IF NOT EXISTS idx_pisos_bloque_id ON pisos (bloque_id);

CREATE INDEX IF NOT EXISTS idx_afiliadas_piso_id ON afiliadas (piso_id);

CREATE INDEX IF NOT EXISTS idx_facturacion_afiliada_id ON facturacion (afiliada_id);

CREATE INDEX IF NOT EXISTS idx_asesorias_afiliada_id ON asesorias (afiliada_id);

CREATE INDEX IF NOT EXISTS idx_asesorias_tecnica_id ON asesorias (tecnica_id);

CREATE INDEX IF NOT EXISTS idx_conflictos_afiliada_id ON conflictos (afiliada_id);

CREATE INDEX IF NOT EXISTS idx_conflictos_usuario_responsable_id ON conflictos (usuario_responsable_id);

CREATE INDEX IF NOT EXISTS idx_diario_conflictos_conflicto_id ON diario_conflictos (conflicto_id);

CREATE INDEX IF NOT EXISTS idx_diario_conflictos_usuario_id ON diario_conflictos (usuario_id);

-- =====================================================================
-- PASO 2: FUNCIÓN Y TRIGGER PARA SINCRONIZACIÓN DE NODOS
-- =====================================================================

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
-- PASO 3: VISTAS PARA PRESENTACIÓN DE DATOS
-- =====================================================================

CREATE OR REPLACE VIEW v_resumen_nodos AS
SELECT
    n.id,
    n.nombre,
    n.descripcion,
    COUNT(DISTINCT b.id) as num_bloques,
    COUNT(DISTINCT p.id) as num_pisos,
    COUNT(DISTINCT a.id) as num_afiliadas
FROM
    nodos n
    LEFT JOIN nodos_cp_mapping ncm ON n.id = ncm.nodo_id
    LEFT JOIN pisos p ON ncm.cp = p.cp
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY
    n.id,
    n.nombre,
    n.descripcion;

CREATE OR REPLACE VIEW v_resumen_entramados_empresas AS
SELECT
    ee.id,
    ee.nombre,
    ee.descripcion,
    COUNT(DISTINCT e.id) as num_empresas,
    COUNT(DISTINCT b.id) as num_bloques,
    COUNT(DISTINCT a.id) as num_afiliadas
FROM
    entramado_empresas ee
    LEFT JOIN empresas e ON ee.id = e.entramado_id
    LEFT JOIN bloques b ON e.id = b.empresa_id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
GROUP BY
    ee.id,
    ee.nombre,
    ee.descripcion;

CREATE OR REPLACE VIEW v_afiliadas_detalle AS
SELECT
    a.id,
    a.num_afiliada,
    a.nombre,
    a.apellidos,
    CONCAT(a.nombre, ' ', a.apellidos) as nombre_completo,
    a.cif,
    a.genero,
    a.email,
    a.telefono,
    a.regimen,
    a.estado,
    a.fecha_alta,
    a.fecha_baja,
    p.direccion as direccion_piso,
    p.municipio,
    p.cp,
    b.direccion as direccion_bloque,
    e.nombre as empresa_nombre,
    ee.nombre as entramado_nombre,
    n.nombre as nodo_nombre,
    f.cuota,
    f.periodicidad,
    f.forma_pago
FROM
    afiliadas a
    LEFT JOIN pisos p ON a.piso_id = p.id
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
    LEFT JOIN nodos n ON b.nodo_id = n.id
    LEFT JOIN facturacion f ON a.id = f.afiliada_id;

CREATE OR REPLACE VIEW v_conflictos_detalle AS
SELECT
    c.id,
    c.estado,
    c.ambito,
    c.causa,
    c.tarea_actual,
    c.fecha_apertura,
    c.fecha_cierre,
    c.descripcion,
    c.resolucion,
    a.nombre as afiliada_nombre,
    a.apellidos as afiliada_apellidos,
    CONCAT(a.nombre, ' ', a.apellidos) as afiliada_nombre_completo,
    a.num_afiliada,
    u.alias as usuario_responsable_alias,
    p.direccion as direccion_piso,
    b.direccion as direccion_bloque,
    n.nombre as nodo_nombre
FROM
    conflictos c
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN usuarios u ON c.usuario_responsable_id = u.id
    LEFT JOIN pisos p ON a.piso_id = p.id
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN nodos n ON b.nodo_id = n.id;

CREATE OR REPLACE VIEW v_diario_conflictos_con_afiliada AS
SELECT
    dc.id,
    dc.conflicto_id,
    dc.estado,
    dc.accion,
    dc.notas,
    dc.tarea_actual,
    dc.created_at,
    u.alias as usuario_alias,
    a.nombre as afiliada_nombre,
    a.apellidos as afiliada_apellidos,
    CONCAT(a.nombre, ' ', a.apellidos) as afiliada_nombre_completo
FROM
    diario_conflictos dc
    LEFT JOIN usuarios u ON dc.usuario_id = u.id
    LEFT JOIN conflictos c ON dc.conflicto_id = c.id
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id;

CREATE OR REPLACE VIEW comprobar_link_pisos_bloques AS
SELECT
    p.id as piso_id,
    p.direccion as piso_direccion,
    p.bloque_id,
    b.direccion as bloque_direccion,
    CASE
        WHEN p.bloque_id IS NULL THEN 'Sin bloque asignado'
        WHEN b.id IS NULL THEN 'Bloque referenciado no existe'
        ELSE 'Vinculación correcta'
    END as estado_vinculacion
FROM pisos p
    LEFT JOIN bloques b ON p.bloque_id = b.id;

CREATE OR REPLACE VIEW v_conflictos_enhanced AS
SELECT
    c.id,
    c.estado,
    c.ambito,
    c.causa,
    c.tarea_actual,
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
    sindicato_inq.conflictos c
    LEFT JOIN sindicato_inq.afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN sindicato_inq.pisos p ON a.piso_id = p.id
    LEFT JOIN sindicato_inq.bloques b ON p.bloque_id = b.id
    LEFT JOIN sindicato_inq.nodos n1 ON b.nodo_id = n1.id
    LEFT JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
    LEFT JOIN sindicato_inq.nodos n2 ON ncm.nodo_id = n2.id
    LEFT JOIN sindicato_inq.usuarios u ON c.usuario_responsable_id = u.id;

-- =====================================================================
-- PASO 4: LIMPIEZA Y POBLACIÓN DE DATOS ARTIFICIALES
-- =====================================================================

-- Limpiar datos existentes para evitar conflictos
TRUNCATE TABLE diario_conflictos,
conflictos,
asesorias,
facturacion,
afiliadas,
pisos,
bloques,
empresas,
entramado_empresas,
usuario_credenciales,
usuario_roles,
usuarios,
roles,
nodos_cp_mapping,
nodos
RESTART IDENTITY CASCADE;

-- Insertar roles
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
        'técnico',
        'Técnico para asesorías'
    ),
    (
        'usuario',
        'Usuario básico del sistema'
    ) ON CONFLICT (nombre) DO NOTHING;

-- Insertar nodos territoriales
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
    ),
    (
        'Norte',
        'Distritos del norte de Madrid'
    ),
    (
        'Sur',
        'Distritos del sur de Madrid'
    );

-- Mapeo códigos postales a nodos
INSERT INTO
    nodos_cp_mapping (cp, nodo_id)
VALUES (28080, 1), -- Centro-Arganzuela-Retiro
    (28013, 1), -- Centro-Arganzuela-Retiro
    (28014, 1), -- Centro-Arganzuela-Retiro
    (28081, 2), -- Latina
    (28024, 2), -- Latina
    (28082, 3), -- Este
    (28009, 3), -- Este
    (28028, 4), -- Norte
    (28034, 4), -- Norte
    (28025, 5), -- Sur
    (28041, 5);
-- Sur

-- Insertar entramados empresariales
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
    ),
    (
        'Grupo Inmobiliario Madrid',
        'Empresa local especializada en gestión de patrimonio inmobiliario urbano.'
    );

-- Insertar empresas
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
        1,
        'Fidere Vivienda Madrid SL',
        'B81234567',
        'Juan Pérez García, Ana García López',
        'No',
        'Paseo de la Castellana, 1, Madrid, España'
    ),
    (
        1,
        'Azora Gestión Inmobiliaria SA',
        'A81234568',
        'Carlos Sánchez Ruiz, María López Torres',
        'Sí',
        'Calle de Serrano, 50, Madrid, España'
    ),
    (
        2,
        'Nestar Residencial Madrid SA',
        'A87654321',
        'Laura Martínez Silva, David Fernández Vega',
        'Sí',
        'Calle de Serrano, 10, Madrid, España'
    ),
    (
        3,
        'Elix Housing SOCIMI',
        'A12345678',
        'Sofía Gómez Ruiz, David Fernández Castro',
        'No',
        'Avenida de América, 5, Madrid, España'
    ),
    (
        4,
        'Inmobiliaria Centro Madrid SL',
        'B98765432',
        'Roberto Díaz Moreno, Elena Jiménez Blanco',
        'No',
        'Gran Vía, 25, Madrid, España'
    );

-- Insertar bloques
INSERT INTO
    bloques (
        empresa_id,
        direccion,
        estado,
        api
    )
VALUES (
        1,
        'Calle de la Invención, 10, Madrid',
        'Activo',
        'No'
    ),
    (
        1,
        'Calle Falsa, 123, Madrid',
        'Activo',
        'No'
    ),
    (
        2,
        'Avenida de la Imaginación, 20, Madrid',
        'Activo',
        'Sí'
    ),
    (
        3,
        'Plaza de la Creatividad, 5, Madrid',
        'En renovación',
        'No'
    ),
    (
        4,
        'Calle Ejemplo, 15, Madrid',
        'Activo',
        'Sí'
    ),
    (
        5,
        'Avenida Test, 30, Madrid',
        'Activo',
        'No'
    );

-- Insertar pisos
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
        1,
        'Calle de la Invención, 10, 1ºA, Madrid',
        'Madrid',
        28080,
        'No',
        true,
        false
    ),
    (
        1,
        'Calle de la Invención, 10, 2ºB, Madrid',
        'Madrid',
        28080,
        'No',
        true,
        false
    ),
    (
        1,
        'Calle de la Invención, 10, 3ºC, Madrid',
        'Madrid',
        28080,
        'No',
        true,
        false
    ),
    (
        2,
        'Calle Falsa, 123, Bajo, Madrid',
        'Madrid',
        28013,
        'No',
        false,
        true
    ),
    (
        2,
        'Calle Falsa, 123, 1º, Madrid',
        'Madrid',
        28013,
        'No',
        false,
        false
    ),
    (
        3,
        'Avenida de la Imaginación, 20, Bajo C, Madrid',
        'Madrid',
        28081,
        'Sí',
        true,
        false
    ),
    (
        3,
        'Avenida de la Imaginación, 20, 1ºD, Madrid',
        'Madrid',
        28081,
        'Sí',
        true,
        false
    ),
    (
        4,
        'Plaza de la Creatividad, 5, 2ºA, Madrid',
        'Madrid',
        28082,
        'No',
        true,
        false
    ),
    (
        5,
        'Calle Ejemplo, 15, Ático, Madrid',
        'Madrid',
        28028,
        'Sí',
        true,
        true
    ),
    (
        6,
        'Avenida Test, 30, 1ºB, Madrid',
        'Madrid',
        28025,
        'No',
        true,
        false
    );

-- =====================================================================
-- PASO 5: INSERTAR USUARIOS Y CONFIGURAR ADMIN
-- =====================================================================

-- Insertar usuarios (incluyendo el admin)
INSERT INTO
    usuarios (
        alias,
        nombre,
        apellidos,
        email,
        roles,
        is_active
    )
VALUES (
        'sumate',
        'Sumate',
        '(sistemas)',
        'sumate@inquilinato.org',
        'admin',
        TRUE
    ),
    (
        'admin',
        'Administrador',
        'Sistema',
        'admin@inquilinato.org',
        'admin',
        TRUE
    ),
    (
        'gestor1',
        'Laura',
        'Gómez',
        'laura.gomez@inquilinato.org',
        'gestor',
        TRUE
    ),
    (
        'tecnico1',
        'Miguel',
        'López',
        'miguel.lopez@inquilinato.org',
        'técnico',
        TRUE
    ),
    (
        'usuario1',
        'Ana',
        'Martínez',
        'ana.martinez@inquilinato.org',
        'usuario',
        TRUE
    ),
    (
        'usuario2',
        'Carlos',
        'Sánchez',
        'carlos.sanchez@inquilinato.org',
        'usuario',
        TRUE
    );

-- Insertar credenciales para usuarios
-- Hash para password "12345678" usando bcrypt con cost 12: $2b$12$Dz8E7dJgKF5BV8.6RQGJlu0TgmN4WZKcK8VzQwYqP5fF1wBJNsOui
INSERT INTO
    usuario_credenciales (usuario_id, password_hash)
VALUES (
        1,
        '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
    ), -- admin
    (
        2,
        '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
    ), -- sumate
    (
        3,
        '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
    ), -- gestor1
    (
        4,
        '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
    ), -- tecnico1
    (
        5,
        '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
    ), -- usuario1
    (
        6,
        '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
    );
-- usuario2

-- Asignar roles a usuarios
INSERT INTO
    usuario_roles (usuario_id, role_id)
VALUES (1, 1), -- admin -> admin role
    (2, 1), -- sumate -> admin role
    (3, 2), -- gestor1 -> gestor role
    (4, 3), -- tecnico1 -> técnico role
    (5, 4), -- usuario1 -> usuario role
    (6, 4);
-- usuario2 -> usuario role

-- Insertar afiliadas
INSERT INTO
    afiliadas (
        piso_id,
        num_afiliada,
        nombre,
        apellidos,
        cif,
        genero,
        email,
        telefono,
        regimen,
        estado,
        fecha_alta
    )
VALUES (
        1,
        'A0001',
        'Lucía',
        'García Pérez',
        '12345678A',
        'Mujer',
        'lucia.garcia@email.com',
        '600123456',
        'Alquiler',
        'Alta',
        '2023-01-15'
    ),
    (
        2,
        'A0002',
        'Javier',
        'Rodríguez López',
        '87654321B',
        'Hombre',
        'javier.rodriguez@email.com',
        '600234567',
        'Alquiler',
        'Alta',
        '2023-02-20'
    ),
    (
        3,
        'A0003',
        'María',
        'Sánchez Martín',
        '11223344C',
        'Mujer',
        'maria.sanchez@email.com',
        '600345678',
        'Alquiler',
        'Baja',
        '2023-03-25'
    ),
    (
        4,
        'A0004',
        'Carlos',
        'López Torres',
        '55667788D',
        'Hombre',
        'carlos.lopez@email.com',
        '600456789',
        'Alquiler',
        'Alta',
        '2023-04-10'
    ),
    (
        5,
        'A0005',
        'Ana',
        'Fernández Ruiz',
        '99887766E',
        'Mujer',
        'ana.fernandez@email.com',
        '600567890',
        'Propiedad',
        'Alta',
        '2023-05-18'
    ),
    (
        6,
        'A0006',
        'Miguel',
        'Gómez Silva',
        '44556677F',
        'Hombre',
        'miguel.gomez@email.com',
        '600678901',
        'Alquiler',
        'Alta',
        '2023-06-22'
    ),
    (
        7,
        'A0007',
        'Elena',
        'Díaz Castro',
        '33445566G',
        'Mujer',
        'elena.diaz@email.com',
        '600789012',
        'Alquiler',
        'Alta',
        '2023-07-30'
    ),
    (
        8,
        'A0008',
        'Pedro',
        'Moreno Vega',
        '22334455H',
        'Hombre',
        'pedro.moreno@email.com',
        '600890123',
        'Alquiler',
        'Suspendida',
        '2023-08-15'
    ),
    (
        9,
        'A0009',
        'Laura',
        'Jiménez Blanco',
        '66778899I',
        'Mujer',
        'laura.jimenez@email.com',
        '600901234',
        'Propiedad',
        'Alta',
        '2023-09-10'
    ),
    (
        10,
        'A0010',
        'Roberto',
        'Herrera Campos',
        '77889900J',
        'Hombre',
        'roberto.herrera@email.com',
        '601012345',
        'Alquiler',
        'Alta',
        '2023-10-05'
    );

-- Insertar facturación
INSERT INTO
    facturacion (
        afiliada_id,
        cuota,
        periodicidad,
        forma_pago,
        iban
    )
VALUES (
        1,
        15.00,
        1,
        'Domiciliación',
        'ES9121000418450200051332'
    ),
    (
        2,
        150.00,
        12,
        'Domiciliación',
        'ES9021000418450200051333'
    ),
    (
        4,
        15.00,
        1,
        'Transferencia',
        'ES7620770024003102575766'
    ),
    (
        5,
        45.00,
        3,
        'Domiciliación',
        'ES1000492352082414205416'
    ),
    (
        6,
        15.00,
        1,
        'Domiciliación',
        'ES0182380025120300951501'
    ),
    (7, 30.00, 6, 'Efectivo', NULL),
    (
        9,
        180.00,
        12,
        'Domiciliación',
        'ES9000246912501640045014'
    ),
    (
        10,
        15.00,
        1,
        'Transferencia',
        'ES5520809476543210987654'
    );

-- Insertar asesorías
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
        1,
        4,
        'Completada',
        '2024-11-15',
        'Inquilina',
        'Legal',
        'Resuelto favorablemente'
    ),
    (
        2,
        4,
        'En proceso',
        '2024-12-01',
        'Inquilina',
        'Técnica',
        'Pendiente de documentación'
    ),
    (
        4,
        4,
        'Completada',
        '2024-10-20',
        'Inquilina',
        'Legal',
        'Derivado a conflicto'
    ),
    (
        6,
        4,
        'Programada',
        '2025-01-25',
        'Inquilina',
        'Técnica',
        NULL
    ),
    (
        9,
        4,
        'Completada',
        '2024-09-10',
        'Propietaria',
        'Legal',
        'Información proporcionada'
    );

-- Insertar conflictos
INSERT INTO
    conflictos (
        afiliada_id,
        usuario_responsable_id,
        estado,
        ambito,
        causa,
        tarea_actual,
        fecha_apertura,
        descripcion,
        resolucion
    )
VALUES (
        1,
        3,
        'En proceso',
        'Afiliada',
        'No renovación',
        'Comunicación con propietario',
        '2025-01-17',
        'El propietario se niega a renovar el contrato sin justificación válida.',
        NULL
    ),
    (
        2,
        3,
        'Cerrado',
        'Afiliada',
        'Fianza',
        NULL,
        '2024-11-19',
        'El propietario no devuelve la fianza alegando daños inexistentes.',
        'Se recuperó la fianza tras la mediación legal.'
    ),
    (
        4,
        3,
        'Abierto',
        'Afiliada',
        'Subida de alquiler',
        'Revisión de contrato',
        '2024-12-10',
        'Incremento abusivo del alquiler superior al IPC.',
        NULL
    ),
    (
        6,
        3,
        'En proceso',
        'Bloque',
        'Reparaciones / Habitabilidad',
        'Inspección técnica',
        '2024-11-05',
        'Problemas de humedades y calefacción en el edificio.',
        NULL
    ),
    (
        8,
        3,
        'Abierto',
        'Afiliada',
        'Acoso inmobiliario',
        'Recopilación de pruebas',
        '2024-12-20',
        'Presiones constantes para abandonar la vivienda.',
        NULL
    );

-- Insertar diario de conflictos
INSERT INTO
    diario_conflictos (
        conflicto_id,
        usuario_id,
        estado,
        accion,
        notas,
        tarea_actual,
        created_at
    )
VALUES (
        1,
        3,
        'En proceso',
        'comunicación enviada',
        'Se envió burofax al propietario solicitando renovación del contrato.',
        'Esperar respuesta',
        '2025-01-17 10:00:00'
    ),
    (
        1,
        3,
        'En proceso',
        'llamada',
        'Contacto telefónico con la afiliada para informar del estado.',
        'Comunicación con propietario',
        '2025-01-20 15:30:00'
    ),
    (
        2,
        3,
        'En proceso',
        'nota localización propiedades',
        'Investigación de bienes del propietario para posible ejecución.',
        'Preparar demanda',
        '2024-11-20 12:30:00'
    ),
    (
        2,
        3,
        'Cerrado',
        'MASC',
        'Mediación exitosa. El propietario acepta devolver la fianza.',
        NULL,
        '2024-12-01 16:45:00'
    ),
    (
        3,
        3,
        'Abierto',
        'nota simple',
        'Análisis del contrato de alquiler y comparación con índices oficiales.',
        'Revisión de contrato',
        '2024-12-10 09:15:00'
    ),
    (
        4,
        3,
        'En proceso',
        'informe vulnerabilidad',
        'Elaborado informe de vulnerabilidad social de las afiliadas afectadas.',
        'Inspección técnica',
        '2024-11-05 14:20:00'
    ),
    (
        4,
        3,
        'En proceso',
        'acción',
        'Reunión con la comunidad de propietarios para abordar las reparaciones.',
        'Inspección técnica',
        '2024-11-15 11:00:00'
    ),
    (
        5,
        3,
        'Abierto',
        'nota simple',
        'Primera entrevista con la afiliada. Documentación de incidentes.',
        'Recopilación de pruebas',
        '2024-12-20 10:30:00'
    );

-- PROCEDURE TO SYNC BLOQUES TO NODOS BASED ON PISOS' CPs
-- This procedure assigns nodo_id to bloques based on the most common nodo_id among their pisos' CPs
CREATE OR REPLACE PROCEDURE sync_all_bloques_to_nodos()
LANGUAGE plpgsql
AS $$
DECLARE
    bloque_record RECORD;
    most_common_nodo_id INTEGER;
BEGIN
    -- Itera sobre cada bloque que no tiene un nodo asignado
    FOR bloque_record IN SELECT id FROM sindicato_inq.bloques WHERE nodo_id IS NULL LOOP
        -- Encuentra el nodo_id más común entre los pisos de este bloque
        SELECT ncm.nodo_id INTO most_common_nodo_id
        FROM sindicato_inq.pisos p
        JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
        WHERE p.bloque_id = bloque_record.id
        GROUP BY ncm.nodo_id
        ORDER BY COUNT(*) DESC
        LIMIT 1;

        -- Si se encontró un nodo común, actualiza el bloque
        IF FOUND AND most_common_nodo_id IS NOT NULL THEN
            UPDATE sindicato_inq.bloques
            SET nodo_id = most_common_nodo_id
            WHERE id = bloque_record.id;
        END IF;
    END LOOP;
END;
$;

-- =====================================================================
-- PASO 6: SINCRONIZACIÓN Y FINALIZACIÓN
-- =====================================================================

-- La sincronización ya se ejecutó arriba con el bloque DO

-- =====================================================================
-- CONFIRMACIÓN Y ESTADÍSTICAS
-- =====================================================================

SELECT 'Base de datos poblada correctamente con datos artificiales' as mensaje;

-- Verificar que el usuario admin se creó correctamente
SELECT
    u.id,
    u.alias,
    u.nombre,
    u.apellidos,
    u.email,
    r.nombre as rol,
    CASE
        WHEN uc.password_hash IS NOT NULL THEN 'Hash configurado'
        ELSE 'Sin hash'
    END as estado_password
FROM usuarios u
LEFT JOIN usuario_roles ur ON u.id = ur.usuario_id
LEFT JOIN roles r ON ur.role_id = r.id
LEFT JOIN usuario_credenciales uc ON u.id = uc.usuario_id
WHERE u.alias = 'admin';

-- Mostrar estadísticas generales
SELECT
    'Nodos' as tabla, COUNT(*) as registros FROM nodos
UNION ALL SELECT 'Entramados', COUNT(*) FROM entramado_empresas
UNION ALL SELECT 'Empresas', COUNT(*) FROM empresas
UNION ALL SELECT 'Bloques', COUNT(*) FROM bloques
UNION ALL SELECT 'Pisos', COUNT(*) FROM pisos
UNION ALL SELECT 'Usuarios', COUNT(*) FROM usuarios
UNION ALL SELECT 'Afiliadas', COUNT(*) FROM afiliadas
UNION ALL SELECT 'Conflictos', COUNT(*) FROM conflictos
UNION ALL SELECT 'Diario Conflictos', COUNT(*) FROM diario_conflictos
UNION ALL SELECT 'Asesorías', COUNT(*) FROM asesorias
UNION ALL SELECT 'Facturación', COUNT(*) FROM facturacion
ORDER BY tabla;

-- Verificar integridad de relaciones críticas
SELECT 'Verificaciones de integridad:' as mensaje;

SELECT
    COUNT(*) as bloques_sin_nodo,
    'bloques sin nodo asignado' as descripcion
FROM bloques WHERE nodo_id IS NULL;

SELECT
    COUNT(*) as usuarios_sin_credenciales,
    'usuarios sin credenciales' as descripcion
FROM usuarios u
LEFT JOIN usuario_credenciales uc ON u.id = uc.usuario_id
WHERE uc.usuario_id IS NULL;

SELECT
    COUNT(*) as usuarios_sin_roles,
    'usuarios sin roles asignados' as descripcion
FROM usuarios u
LEFT JOIN usuario_roles ur ON u.id = ur.usuario_id
WHERE ur.usuario_id IS NULL;