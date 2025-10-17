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

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- 04-init: POBLACIÓN DE DATOS ARTIFICIALES (final init script)
-- =====================================================================

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
    );

-- Insertar nodos territoriales
INSERT INTO nodos (nombre, descripcion) VALUES
    ('Centro-Arganzuela-Retiro', 'Agrupa los distritos de Centro, Arganzuela, Retiro, Moncloa y Chamberí.'),
    ('Latina', 'Nodo del distrito de Latina.'),
    ('Carabanchel', 'Nodo del distrito de Carabanchel.'),
    ('Usera-Villaverde', 'Agrupa los distritos de Usera y Villaverde.'),
    ('Este', 'Agrupa los distritos del este de Madrid: Salamanca, Chamartín, Ciudad Lineal, Hortaleza, San Blas-Canillejas, Moratalaz, Vicálvaro y Barajas.'),
    ('Sur', 'Agrupa los municipios de la zona sur de la Comunidad de Madrid.'),
    ('Corredor', 'Agrupa los municipios del Corredor del Henares.'),
    ('Sierra Norte', 'Agrupa los municipios de la Sierra Norte.')
ON CONFLICT (nombre) DO NOTHING;

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

-- Insertar empresas
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

-- CORREGIDO: Añadidos valores para el nuevo campo 'propiedad'.
INSERT INTO
    pisos (
        bloque_id,
        direccion,
        municipio,
        cp,
        inmobiliaria,
        propiedad,
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
        'Fidere Vivienda Madrid SL',
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
        'Fidere Vivienda Madrid SL',
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
        'Fidere Vivienda Madrid SL',
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
        'Fidere Vivienda Madrid SL',
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
        'Fidere Vivienda Madrid SL',
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
        'Azora Gestión Inmobiliaria SA',
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
        'Azora Gestión Inmobiliaria SA',
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
        'Elix Housing SOCIMI',
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
        'Inmobiliaria Centro Madrid SL',
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
        'Inmobiliaria Centro Madrid SL',
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

INSERT INTO
    usuario_credenciales (usuario_id, password_hash)
VALUES (
        1,
        '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
    ),
    (
        2,
        '$2b$12$J23QHdoGZ434MQIZH7FwEew.VMDftluCBEugd8LKLIE3B8NCuGKy6'
    ),
    (
        3,
        '$2b$12$.2k0jdsNjg6J/lcZL1WBkej85pFdSTq2NWdFBjPgfZ7EXjAbjoSei'
    );

INSERT INTO
    usuario_roles (usuario_id, role_id)
VALUES (1, 1),
    (2, 2),
    (3, 3);

-- CORREGIDO: Eliminados valores para 'seccion_sindical', 'comision', 'trato_propiedad'.
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
        nivel_participacion,
        regimen,
        estado,
        fecha_alta,
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
        'Activa',
        'Alquiler',
        'Alta',
        '2023-01-15',
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
        'Colaboradora',
        'Alquiler',
        'Alta',
        '2023-02-20',
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
        'Referente',
        'Alquiler',
        'Baja',
        '2023-03-25',
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
        'Activa',
        'Alquiler',
        'Alta',
        '2023-04-10',
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
        'Colaboradora',
        'Propiedad',
        'Alta',
        '2023-05-18',
        '1975-09-17',
        NULL
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
        'Victoria',
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
        estado,
        ambito,
        causa,
        tarea_actual,
        fecha_apertura,
        descripcion
    )
VALUES (
        1,
        'Victoria',
        'Afiliada',
        'No renovación',
        'Comunicación con propietario',
        '2025-01-17',
        'El propietario se niega a renovar el contrato sin justificación válida.'
    ),
    (
        2,
        'Cerrado',
        'Afiliada',
        'Fianza',
        NULL,
        '2024-11-19',
        'El propietario no devuelve la fianza alegando daños inexistentes.'
    ),
    (
        4,
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
        1,
        'Victoria',
        'comunicación enviada',
        'Se envió burofax al propietario solicitando renovación del contrato.',
        'Esperar respuesta',
        '2025-01-17 10:00:00'
    ),
    (
        1,
        2,
        'Victoria',
        'llamada',
        'Contacto telefónico con la afiliada para informar del estado.',
        'Comunicación con propietario',
        '2025-01-20 15:30:00'
    ),
    (
        2,
        3,
        'Victoria',
        'nota localización propiedades',
        'Investigación de bienes del propietario para posible ejecución.',
        'Preparar demanda',
        '2024-11-20 12:30:00'
    ),
    (
        2,
        2,
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

-- =====================================================================
-- PASO 6: SINCRONIZACIÓN Y FINALIZACIÓN
-- =====================================================================

-- =====================================================================
-- CONFIRMACIÓN
-- =====================================================================
SELECT 'Base de datos poblada correctamente con datos artificiales' as mensaje;

-- =====================================================================
-- PARTE 2: MAPEADO DE CÓDIGOS POSTALES A NODOS
-- =====================================================================
-- Se asocia cada código postal con su nodo correspondiente.

-- Nodo: Centro-Arganzuela-Retiro
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Centro-Arganzuela-Retiro')
FROM (VALUES
    (28004), (28005), (28007), (28008), (28009), (28010),
    (28012), (28013), (28014), (28015), (28045)
) AS data(cp) ON CONFLICT (cp) DO NOTHING;

-- Nodo: Latina
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Latina')
FROM (VALUES (28011), (28024), (28044)) AS data(cp)
ON CONFLICT (cp) DO NOTHING;

-- Nodo: Carabanchel
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Carabanchel')
FROM (VALUES (28047), (28019), (28025)) AS data(cp)
ON CONFLICT (cp) DO NOTHING;

-- Nodo: Usera-Villaverde
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Usera-Villaverde')
FROM (VALUES (28021), (28026), (28041)) AS data(cp)
ON CONFLICT (cp) DO NOTHING;

-- Nodo: Este
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Este')
FROM (VALUES
    (28017), (28022), (28027), (28030), (28032), (28033),
    (28037), (28043), (28052)
) AS data(cp) ON CONFLICT (cp) DO NOTHING;

-- Nodo: Sur
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Sur')
FROM (VALUES
    (28054), (28300), (28312), (28320), (28340), (28341), (28342),
    (28343), (28600), (28609), (28911), (28912), (28913), (28914),
    (28915), (28916), (28917), (28918), (28919), (28921), (28922),
    (28923), (28924), (28925), (28931), (28932), (28933), (28934),
    (28935), (28936), (28937), (28938), (28939), (28941), (28942),
    (28943), (28944), (28945), (28946), (28947), (28950), (28970),
    (28971), (28976), (28977), (28978), (28979), (28980), (28981),
    (28982), (28983), (28984), (28990), (28991), (28901), (28902),
    (28903), (28904), (28905), (28906), (28907)
) AS data(cp) ON CONFLICT (cp) DO NOTHING;
-- Nodo: Corredor
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Corredor')
FROM (VALUES
    (28801), (28802), (28803), (28804), (28805), (28806), (28807),
    (28811), (28812), (28814), (28815), (28816), (28817), (28818),
    (28821), (28822), (28823), (28830), (28850), (28863), (28864),
    (28880), (28890)
) AS data(cp) ON CONFLICT (cp) DO NOTHING;

-- Nodo: Sierra Norte
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Sierra Norte')
FROM (VALUES
    (28180), (28189), (28190), (28191), (28192), (28193), (28194),
    (28195), (28196), (28720), (28721), (28722), (28729), (28730),
    (28737), (28739), (28740), (28742), (28743), (28749), (28751),
    (28752), (28754), (28755), (28756), (28792)
) AS data(cp) ON CONFLICT (cp) DO NOTHING;
