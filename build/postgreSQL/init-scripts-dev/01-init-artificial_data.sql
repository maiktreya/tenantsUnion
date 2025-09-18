-- =====================================================================
-- SCRIPT DE DATOS ARTIFICIALES PARA PRUEBAS (ALINEADO CON ESQUEMA BASE)
-- =====================================================================
-- Este script crea el esquema completo, define las tablas (alineadas con
-- 01-init-schema-and-data), crea índices, configura la autenticación,
-- genera las vistas y puebla la base de datos con datos artificiales.
-- Mantiene extensiones "dev-only": nodos y mapping CP→nodo, roles
-- normalizados, credenciales, triggers y vistas de reporting.
-- =====================================================================

-- =====================================================================
-- PASO 0: CREACIÓN DEL ESQUEMA
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS sindicato_inq;

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- PASO 1: DEFINICIÓN DE TABLAS E ÍNDICES (ALINEADO CON PRODUCCIÓN)
-- Nota: Se incorporan campos presentes en 01-init-schema-and-data:
--   - empresas.url_notas TEXT
--   - pisos.prop_vertical TEXT (en lugar de BOOLEAN), vpo, vpo_date
--   - afiliadas.fecha_nac (en lugar de fecha_nacimiento)
-- Se preservan campos dev-only que ya usabas (seccion_sindical, comision).
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
    descripcion TEXT,
    usuario_responsable_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL
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
    url_notas TEXT -- añadido para alinear con esquema base
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
    nodo_id INTEGER REFERENCES nodos (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS pisos (
    id SERIAL PRIMARY KEY,
    bloque_id INTEGER REFERENCES bloques (id) ON DELETE SET NULL,
    direccion TEXT NOT NULL UNIQUE,
    municipio TEXT,
    cp INTEGER,
    inmobiliaria TEXT,
    -- prop_vertical ahora TEXT (en el script base es TEXT)
    prop_vertical TEXT,
    por_habitaciones BOOLEAN,
    n_personas INTEGER,
    fecha_firma DATE,
    -- añadidos del script base
    vpo BOOLEAN,
    vpo_date DATE
);

-- Tabla 'afiliadas' alineada con base:
-- - fecha_nac en lugar de fecha_nacimiento
-- - se mantienen seccion_sindical y comision (dev-only) para no romper vistas/dev
CREATE TABLE IF NOT EXISTS afiliadas (
    id SERIAL PRIMARY KEY,
    piso_id INTEGER REFERENCES pisos (id) ON DELETE SET NULL,
    -- Identificación
    num_afiliada TEXT UNIQUE,
    nombre TEXT,
    apellidos TEXT,
    cif TEXT UNIQUE,
    fecha_nac DATE,
    genero TEXT,
    email TEXT,
    telefono TEXT,
    -- Estado y Régimen
    estado TEXT,
    regimen TEXT,
    fecha_alta DATE,
    fecha_baja DATE,
    trato_propiedad BOOLEAN,
    -- Participación Interna (dev-only, no está en esquema base pero se preserva)
    seccion_sindical TEXT,
    nivel_participacion TEXT,
    comision TEXT
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

-- Crear índices (incluye los del base y extras dev)
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
-- PASO 2: FUNCIÓN, PROCEDIMIENTO Y TRIGGER PARA SINCRONIZACIÓN (dev)
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

-- PROCEDURE TO SYNC BLOQUES TO NODOS BASED ON PISOS' CPs
CREATE OR REPLACE PROCEDURE sync_all_bloques_to_nodos()
LANGUAGE plpgsql
AS $$
DECLARE
    bloque_record RECORD;
    most_common_nodo_id INTEGER;
BEGIN
    FOR bloque_record IN SELECT id FROM sindicato_inq.bloques WHERE nodo_id IS NULL LOOP
        SELECT ncm.nodo_id INTO most_common_nodo_id
        FROM sindicato_inq.pisos p
        JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
        WHERE p.bloque_id = bloque_record.id
        GROUP BY ncm.nodo_id
        ORDER BY COUNT(*) DESC
        LIMIT 1;

        IF FOUND AND most_common_nodo_id IS NOT NULL THEN
            UPDATE sindicato_inq.bloques
            SET nodo_id = most_common_nodo_id
            WHERE id = bloque_record.id;
        END IF;
    END LOOP;
END;
$$;

-- =====================================================================
-- PASO 3: VISTAS PARA PRESENTACIÓN DE DATOS (dev)
-- =====================================================================
CREATE OR REPLACE VIEW v_resumen_bloques AS
SELECT
    b.id,
    b.empresa_id,
    b.nodo_id,
    b.direccion AS "Dirección",
    e.nombre AS "Empresa Propietaria",
    n.nombre AS "Nodo Territorial",
    COUNT(DISTINCT p.id) AS "Pisos en el bloque",
    COUNT(DISTINCT a.id) AS "Afiliadas en el bloque"
FROM
    bloques b
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN nodos n ON b.nodo_id = n.id
GROUP BY
    b.id,
    e.nombre,
    n.nombre
ORDER BY "Afiliadas en el bloque" DESC;

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
nodos RESTART IDENTITY CASCADE;

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
        'actas',
        'Técnico para asesorías'
    )
ON CONFLICT (nombre) DO NOTHING;

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
VALUES (28080, 1),
    (28013, 1),
    (28014, 1),
    (28081, 2),
    (28024, 2),
    (28082, 3),
    (28009, 3),
    (28028, 4),
    (28034, 4),
    (28025, 5),
    (28041, 5);

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

-- Insertar empresas (añadimos url_notas como NULL por defecto)
INSERT INTO
    empresas (
        entramado_id,
        nombre,
        cif_nif_nie,
        directivos,
        direccion_fiscal,
        url_notas
    )
VALUES (
        1,
        'Fidere Vivienda Madrid SL',
        'B81234567',
        'Juan Pérez García, Ana García López',
        'Paseo de la Castellana, 1, Madrid, España',
        NULL
    ),
    (
        1,
        'Azora Gestión Inmobiliaria SA',
        'A81234568',
        'Carlos Sánchez Ruiz, María López Torres',
        'Calle de Serrano, 50, Madrid, España',
        NULL
    ),
    (
        2,
        'Nestar Residencial Madrid SA',
        'A87654321',
        'Laura Martínez Silva, David Fernández Vega',
        'Calle de Serrano, 10, Madrid, España',
        NULL
    ),
    (
        3,
        'Elix Housing SOCIMI',
        'A12345678',
        'Sofía Gómez Ruiz, David Fernández Castro',
        'Avenida de América, 5, Madrid, España',
        NULL
    ),
    (
        4,
        'Inmobiliaria Centro Madrid SL',
        'B98765432',
        'Roberto Díaz Moreno, Elena Jiménez Blanco',
        'Gran Vía, 25, Madrid, España',
        NULL
    );

-- Insertar bloques
INSERT INTO
    bloques (empresa_id, direccion)
VALUES (
        1,
        'Calle de la Invención, 10, Madrid'
    ),
    (1, 'Calle Falsa, 123, Madrid'),
    (
        2,
        'Avenida de la Imaginación, 20, Madrid'
    ),
    (
        3,
        'Plaza de la Creatividad, 5, Madrid'
    ),
    (
        4,
        'Calle Ejemplo, 15, Madrid'
    ),
    (5, 'Avenida Test, 30, Madrid');

-- Insertar pisos
-- Ajuste: prop_vertical como TEXT ('Si'/'No'); añadimos vpo y vpo_date como NULL
INSERT INTO
    pisos (
        bloque_id,
        direccion,
        municipio,
        cp,
        inmobiliaria,
        prop_vertical,
        por_habitaciones,
        n_personas,
        fecha_firma,
        vpo,
        vpo_date
    )
VALUES (
        1,
        'Calle de la Invención, 10, 1ºA, Madrid',
        'Madrid',
        28080,
        'No',
        'Si',
        false,
        2,
        NULL,
        NULL,
        NULL
    ),
    (
        1,
        'Calle de la Invención, 10, 2ºB, Madrid',
        'Madrid',
        28080,
        'No',
        'Si',
        false,
        3,
        NULL,
        NULL,
        NULL
    ),
    (
        1,
        'Calle de la Invención, 10, 3ºC, Madrid',
        'Madrid',
        28080,
        'No',
        'Si',
        false,
        1,
        NULL,
        NULL,
        NULL
    ),
    (
        2,
        'Calle Falsa, 123, Bajo, Madrid',
        'Madrid',
        28013,
        'No',
        'No',
        true,
        4,
        NULL,
        NULL,
        NULL
    ),
    (
        2,
        'Calle Falsa, 123, 1º, Madrid',
        'Madrid',
        28013,
        'No',
        'No',
        false,
        2,
        NULL,
        NULL,
        NULL
    ),
    (
        3,
        'Avenida de la Imaginación, 20, Bajo C, Madrid',
        'Madrid',
        28081,
        'Sí',
        'Si',
        false,
        3,
        NULL,
        NULL,
        NULL
    ),
    (
        3,
        'Avenida de la Imaginación, 20, 1ºD, Madrid',
        'Madrid',
        28081,
        'Sí',
        'Si',
        false,
        2,
        NULL,
        NULL,
        NULL
    ),
    (
        4,
        'Plaza de la Creatividad, 5, 2ºA, Madrid',
        'Madrid',
        28082,
        'No',
        'Si',
        false,
        1,
        NULL,
        NULL,
        NULL
    ),
    (
        5,
        'Calle Ejemplo, 15, Ático, Madrid',
        'Madrid',
        28028,
        'Sí',
        'Si',
        true,
        5,
        NULL,
        NULL,
        NULL
    ),
    (
        6,
        'Avenida Test, 30, 1ºB, Madrid',
        'Madrid',
        28025,
        'No',
        'Si',
        false,
        2,
        NULL,
        NULL,
        NULL
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
        is_active
    )
VALUES (
        'sumate',
        'Sumate',
        '(sistemas)',
        'sumate@inquilinato.org',
        TRUE
    ),
    (
        'gestor',
        'test',
        'test',
        'test@inquilinato.org',
        TRUE
    ),
    (
        'actas',
        'test',
        'test',
        'actas@inquilinato.org',
        TRUE
    );

-- Insertar credenciales para usuarios (Hash for password "12345678")
INSERT INTO
    usuario_credenciales (usuario_id, password_hash)
VALUES (
        1,
        '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
    ),
    (
        2,
        '$2 b$12$J23QHdoGZ434MQIZH7FwEew.VMDftluCBEugd8LKLIE3B8NCuGKy6'
    ),
    (
        3,
        '$2b$12$.2k0jdsNjg6J/lcZL1WBkej85pFdSTq2NWdFBjPgfZ7EXjAbjoSei'
    );

-- Asignar roles a usuarios
INSERT INTO
    usuario_roles (usuario_id, role_id)
VALUES (1, 1),
    (2, 2),
    (3, 3);

-- Crear afiliadas
-- Ajuste: usamos fecha_nac (en lugar de fecha_nacimiento) y mantenemos seccion_sindical/comision
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
        seccion_sindical,
        nivel_participacion,
        comision,
        regimen,
        estado,
        fecha_alta,
        trato_propiedad,
        fecha_nac,
        fecha_baja
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
        'Latina',
        'Activa',
        'No',
        'Alquiler',
        'Alta',
        '2023-01-15',
        false,
        '1985-03-15',
        NULL
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
        'Latina',
        'Colaboradora',
        'Si',
        'Alquiler',
        'Alta',
        '2023-02-20',
        true,
        '1978-11-22',
        NULL
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
        'Centro',
        'Referente',
        'No',
        'Alquiler',
        'Baja',
        '2023-03-25',
        false,
        '1992-07-08',
        NULL
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
        'Centro',
        'Activa',
        'No',
        'Alquiler',
        'Alta',
        '2023-04-10',
        true,
        '1980-12-03',
        NULL
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
        'Este',
        'Colaboradora',
        'No',
        'Propiedad',
        'Alta',
        '2023-05-18',
        false,
        '1975-09-17',
        NULL
    );

-- Insertar facturación (valida con constraint de IBAN)
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
        2,
        'Completada',
        '2024-11-15',
        'Inquilina',
        'Legal',
        'Resuelto favorablemente'
    ),
    (
        2,
        2,
        'En proceso',
        '2024-12-01',
        'Inquilina',
        'Técnica',
        'Pendiente de documentación'
    ),
    (
        4,
        3,
        'Completada',
        '2024-10-20',
        'Inquilina',
        'Legal',
        'Derivado a conflicto'
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
        descripcion
    )
VALUES (
        1,
        3,
        'En proceso',
        'Afiliada',
        'No renovación',
        'Comunicación con propietario',
        '2025-01-17',
        'El propietario se niega a renovar el contrato sin justificación válida.'
    ),
    (
        2,
        3,
        'Cerrado',
        'Afiliada',
        'Fianza',
        NULL,
        '2024-11-19',
        'El propietario no devuelve la fianza alegando daños inexistentes.'
    ),
    (
        4,
        3,
        'Abierto',
        'Afiliada',
        'Subida de alquiler',
        'Revisión de contrato',
        '2024-12-10',
        'Incremento abusivo del alquiler superior al IPC.'
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
    );

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- VISTA 1: ENTRAMADO_EMPRESAS (CORREGIDA CON 'id' EXPLÍCITO)
-- NOTA: Esta es una vista de resumen. Al hacer clic en una fila, se mostrarán las empresas hijas (child records).
CREATE OR REPLACE VIEW v_resumen_entramados_empresas AS
SELECT
    ee.id, -- FIX: Se asegura que el ID primario del entramado esté presente como 'id'.
    ee.nombre AS "Entramado",
    ee.descripcion AS "Descripción",
    COUNT(DISTINCT e.id) AS "Núm. Empresas",
    COUNT(DISTINCT b.id) AS "Núm. Bloques",
    COUNT(DISTINCT p.id) AS "Núm. Pisos",
    COUNT(DISTINCT a.id) AS "Núm. Afiliadas"
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

-- VISTA 2: RESUMEN POR NODO TERRITORIAL (CORREGIDA CON 'id' EXPLÍCITO)
CREATE OR REPLACE VIEW v_resumen_nodos AS
SELECT
    n.id, -- FIX: Se asegura que el ID primario del nodo esté presente como 'id'.
    n.nombre AS "Nodo Territorial",
    n.descripcion AS "Descripción",
    COUNT(DISTINCT b.id) AS "Núm. Bloques",
    COUNT(DISTINCT e.id) AS "Núm. Empresas Activas",
    COUNT(DISTINCT a.id) AS "Núm. Afiliadas",
    COUNT(DISTINCT c.id) AS "Total Conflictos",
    COUNT(DISTINCT c.id) FILTER (
        WHERE
            c.estado = 'Abierto'
    ) AS "Conflictos Abiertos"
FROM
    nodos n
    LEFT JOIN bloques b ON n.id = b.nodo_id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
    LEFT JOIN conflictos c ON a.id = c.afiliada_id
GROUP BY
    n.id,
    n.nombre,
    n.descripcion
ORDER BY "Núm. Afiliadas" DESC;

-- VISTA 3: VISTA DE DETALLE DE CONFLICTOS (UNIFICADA)
-- Esta vista ya incluye 'c.id' a través de 'c.*', por lo que es correcta.
CREATE OR REPLACE VIEW v_conflictos_detalle AS
SELECT
    c.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo,
    u.alias AS usuario_responsable_alias,
    n.nombre AS nodo_nombre,
    p.direccion AS direccion_piso
FROM
    sindicato_inq.conflictos c
    LEFT JOIN sindicato_inq.afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN sindicato_inq.pisos p ON a.piso_id = p.id
    LEFT JOIN sindicato_inq.bloques b ON p.bloque_id = b.id
    LEFT JOIN sindicato_inq.nodos n ON b.nodo_id = n.id
    LEFT JOIN sindicato_inq.usuarios u ON c.usuario_responsable_id = u.id;

-- VISTA 4: AFILIADAS (ESTA VISTA YA ERA CORRECTA)
CREATE OR REPLACE VIEW v_afiliadas_detalle AS
SELECT
    a.id, -- ID primario de la afiliada (para buscar hijos)
    a.piso_id, -- ID foráneo del piso (para buscar padres)
    a.num_afiliada AS "Núm.Afiliada",
    a.nombre AS "Nombre",
    a.apellidos AS "Apellidos",
    a.cif AS "CIF",
    a.genero AS "Género",
    TRIM(
        CONCAT_WS(
            ', ',
            p.direccion,
            p.municipio,
            p.cp::text
        )
    ) AS "Dirección",
    a.regimen AS "Régimen",
    a.estado AS "Estado",
    p.inmobiliaria AS "Inmobiliaria",
    e.nombre AS "Propiedad",
    COALESCE(ee.nombre, 'Sin Entramado') AS "Entramado",
    COALESCE(n.nombre, 'Sin Nodo Asignado') AS "Nodo"
FROM
    afiliadas a
    LEFT JOIN pisos p ON a.piso_id = p.id
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN entramado_empresas ee ON e.entramado_id = ee.id
    LEFT JOIN nodos n ON b.nodo_id = n.id;

-- VISTA 5: RESUMEN DE BLOQUES (ESTA VISTA YA ERA CORRECTA)
CREATE OR REPLACE VIEW v_resumen_bloques AS
SELECT
    b.id, -- Primary key for the block
    b.empresa_id, -- Foreign key to empresas
    b.nodo_id, -- Foreign key to nodos
    b.direccion AS "Dirección",
    e.nombre AS "Empresa Propietaria",
    n.nombre AS "Nodo Territorial",
    COUNT(DISTINCT p.id) AS "Pisos en el bloque",
    COUNT(DISTINCT a.id) AS "Afiliadas en el bloque"
FROM
    bloques b
    LEFT JOIN pisos p ON b.id = p.bloque_id
    LEFT JOIN afiliadas a ON p.id = a.piso_id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    LEFT JOIN nodos n ON b.nodo_id = n.id
GROUP BY
    b.id,
    e.nombre,
    n.nombre
ORDER BY "Afiliadas en el bloque" DESC;
-- =====================================================================
-- VISTAS INTERNAS VISTA CONFLICTOS (NO DISPONIBLE EN LA INTERFAZ NI EN CONFIG.PY)
-- =====================================================================
CREATE OR REPLACE VIEW v_diario_conflictos_con_afiliada AS
SELECT
    d.*,
    a.nombre || ' ' || a.apellidos AS afiliada_nombre_completo,
    u.alias AS autor_nota_alias
FROM
    diario_conflictos d
    LEFT JOIN conflictos c ON d.conflicto_id = c.id
    LEFT JOIN afiliadas a ON c.afiliada_id = a.id
    LEFT JOIN usuarios u ON d.usuario_id = u.id;

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
-- PROCEDIMIENTO: SINCRONIZACIÓN MASIVA DE NODOS PARA BLOQUES
-- =====================================================================
CREATE OR REPLACE VIEW comprobar_link_pisos_bloques AS

SELECT
    p.id,
    p.direccion AS direccion1_piso,
    p.bloque_id,
    b.direccion AS direccion2_bloque,
    (p.bloque_id IS NOT NULL) AS linked,
    similarity (
        trim(
            split_part(b.direccion, ',', 1)
        ) || ', ' || trim(
            split_part(b.direccion, ',', 2)
        ),
        trim(
            split_part(p.direccion, ',', 1)
        ) || ', ' || trim(
            split_part(p.direccion, ',', 2)
        )
    ) AS score
FROM pisos p
    LEFT JOIN bloques b ON p.bloque_id = b.id
ORDER BY linked DESC, score DESC;

-- =====================================================================
-- PASO 6: SINCRONIZACIÓN Y FINALIZACIÓN
-- =====================================================================
CALL sync_all_bloques_to_nodos ();

-- =====================================================================
-- CONFIRMACIÓN Y ESTADÍSTICAS
-- =====================================================================
SELECT 'Base de datos poblada correctamente con datos artificiales (alineado con esquema base)' as mensaje;

ALTER TABLE sindicato_inq.facturacion
ADD CONSTRAINT chk_iban_format CHECK (
    iban IS NULL
    OR iban ~ '^ES[0-9]{22}$'
) NOT VALID;