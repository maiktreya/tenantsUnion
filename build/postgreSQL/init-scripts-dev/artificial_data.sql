-- =====================================================================
-- SCRIPT DE DATOS ARTIFICIALES PARA PRUEBAS (VERSIÓN COMPLETA Y AUTÓNOMA)
-- =====================================================================
-- Este script crea el esquema completo, define las tablas, crea índices
-- y puebla la base de datos con un conjunto de datos amplio y artificial
-- para permitir pruebas exhaustivas del sistema.
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

CREATE TABLE facturacion (
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
    fecha_apertura DATE,
    fecha_cierre DATE,
    descripcion TEXT,
    resolucion TEXT
);

CREATE TABLE acciones (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE diario_conflictos (
    id SERIAL PRIMARY KEY,
    conflicto_id INTEGER NOT NULL REFERENCES conflictos (id) ON DELETE CASCADE,
    usuario_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    accion_id INTEGER REFERENCES acciones (id) ON DELETE SET NULL,
    estado TEXT,
    ambito TEXT,
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MEJORA DE LA TABLA DE USUARIOS
ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
WITH
    TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- =====================================================================
-- PARTE 2: CREACIÓN DE ÍNDICES PARA MEJORAR EL RENDIMIENTO
-- =====================================================================

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
-- PARTE 3: POBLACIÓN DE DATOS ARTIFICIALES
-- =====================================================================

-- Limpiar datos existentes para evitar conflictos
DELETE FROM diario_conflictos;

DELETE FROM conflictos;

DELETE FROM asesorias;

DELETE FROM facturacion;

DELETE FROM afiliadas;

DELETE FROM usuarios;

DELETE FROM pisos;

DELETE FROM bloques;

DELETE FROM empresas;

DELETE FROM entramado_empresas;

DELETE FROM acciones;

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

-- Entramados Empresariales Ficticios
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
        'Patrimonio Urbano SOCIMI',
        'SOCIMI dedicada a la adquisición y gestión de edificios residenciales en centros urbanos.'
    ),
    (
        'Propiedades Familiares Castellanas',
        'Un grupo familiar con una cartera diversificada de inmuebles en alquiler.'
    );

-- Empresas Ficticias
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
    ),
    (
        (
            SELECT id
            FROM entramado_empresas
            WHERE
                nombre = 'Patrimonio Urbano SOCIMI'
        ),
        'Urbe Alquileres S.A.',
        'A88888888',
        'Miguel Torres',
        'Sí',
        'Calle Goya, 55, Madrid, España'
    ),
    (
        NULL,
        'Inmobiliaria Hermanos López',
        'B99999999',
        'Lucía López, Marcos López',
        'No',
        'Plaza Mayor, 2, Madrid, España'
    );

-- Bloques Ficticios
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
    ),
    (
        (
            SELECT id
            FROM empresas
            WHERE
                nombre = 'Urbe Alquileres S.A.'
        ),
        'Calle del Ejemplo, 15, 28083, Madrid',
        'Activo',
        'Sí'
    ),
    (
        (
            SELECT id
            FROM empresas
            WHERE
                nombre = 'Inmobiliaria Hermanos López'
        ),
        'Calle Ficticia, 1, 28084, Getafe',
        'Activo',
        'No'
    );

-- Pisos Ficticios
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
    ),
    (
        (
            SELECT id
            FROM bloques
            WHERE
                direccion = 'Plaza de la Creatividad, 5, 28082, Madrid'
        ),
        'Plaza de la Creatividad, 5, 3ºD, 28082, Madrid',
        'Madrid',
        28082,
        'No',
        false,
        true
    ),
    (
        (
            SELECT id
            FROM bloques
            WHERE
                direccion = 'Calle del Ejemplo, 15, 28083, Madrid'
        ),
        'Calle del Ejemplo, 15, 4º Izquierda, 28083, Madrid',
        'Madrid',
        28083,
        'Sí',
        true,
        false
    ),
    (
        NULL,
        'Calle Solitaria, 33, 1º, 28085, Móstoles',
        'Móstoles',
        28085,
        'No',
        false,
        false
    );

-- Usuarios Ficticios
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
        'Sistemas'
    ),
    (
        'test_gestor',
        'Gestor',
        'de Casos',
        'gestor@example.com',
        'Gestor'
    ),
    (
        'test_user',
        'Usuario',
        'de Prueba',
        'user@example.com',
        'Usuario'
    ),
    (
        'ana_tecnica',
        'Ana',
        'Fernández',
        'ana.f@example.com',
        'Gestor'
    );

-- Afiliadas Ficticias
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
    ),
    (
        (
            SELECT id
            FROM pisos
            WHERE
                direccion = 'Plaza de la Creatividad, 5, 3ºD, 28082, Madrid'
        ),
        'A0004',
        'David',
        'Gómez Ruiz',
        '22334455D',
        'Hombre',
        'Alquiler por habitaciones',
        'Alta',
        '2023-04-10'
    ),
    (
        (
            SELECT id
            FROM pisos
            WHERE
                direccion = 'Calle del Ejemplo, 15, 4º Izquierda, 28083, Madrid'
        ),
        'A0005',
        'Elena',
        'Jiménez Moreno',
        '33445566E',
        'Mujer',
        'Alquiler',
        'Alta',
        '2023-05-12'
    );

-- Facturación Ficticia
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
    ),
    (
        (
            SELECT id
            FROM afiliadas
            WHERE
                num_afiliada = 'A0003'
        ),
        10.00,
        1,
        'Transferencia',
        'ES8921000418450200051334'
    ),
    (
        (
            SELECT id
            FROM afiliadas
            WHERE
                num_afiliada = 'A0004'
        ),
        30.00,
        3,
        'Domiciliación',
        'ES8821000418450200051335'
    ),
    (
        (
            SELECT id
            FROM afiliadas
            WHERE
                num_afiliada = 'A0005'
        ),
        10.00,
        1,
        'Efectivo',
        NULL
    );

-- Asesorías Ficticias
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
        'En proceso',
        '2024-06-15',
        'Afiliada',
        'Asesoría Jurídica',
        'Pendiente de documentación'
    ),
    (
        (
            SELECT id
            FROM afiliadas
            WHERE
                num_afiliada = 'A0004'
        ),
        (
            SELECT id
            FROM usuarios
            WHERE
                alias = 'ana_tecnica'
        ),
        'Resuelto',
        '2024-07-01',
        'Afiliada',
        'Asesoría Gratuita',
        'Información proporcionada sobre derechos en alquiler por habitaciones.'
    );

-- Conflictos Ficticios
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
    ),
    (
        (
            SELECT id
            FROM afiliadas
            WHERE
                num_afiliada = 'A0005'
        ),
        (
            SELECT id
            FROM usuarios
            WHERE
                alias = 'ana_tecnica'
        ),
        'En proceso',
        'Colectivo',
        'Subida abusiva de alquiler',
        '2025-02-01',
        'La propiedad ha comunicado una subida del 30% a todos los inquilinos del bloque.',
        NULL
    );

-- Diario de Conflictos Ficticio
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
                nombre = 'comunicación enviada'
        ),
        'Abierto',
        'Afiliada',
        'Se envía burofax a la propiedad solicitando la motivación de la no renovación.',
        '2025-01-20 13:00:00'
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
                nombre = 'reunión de negociación'
        ),
        'Resuelto',
        'Afiliada',
        'Acuerdo con el propietario para la devolución del 90% de la fianza.',
        '2024-12-05 16:00:00'
    ),
    (
        (
            SELECT id
            FROM conflictos
            WHERE
                causa = 'Subida abusiva de alquiler'
        ),
        (
            SELECT id
            FROM usuarios
            WHERE
                alias = 'ana_tecnica'
        ),
        (
            SELECT id
            FROM acciones
            WHERE
                nombre = 'puerta a puerta'
        ),
        'En proceso',
        'Colectivo',
        'Se realiza un puerta a puerta en el bloque para informar a los vecinos y organizar una asamblea.',
        '2025-02-03 18:00:00'
    );