-- Entramado Empresarial
INSERT INTO
    entramado_empresas (nombre, descripcion)
VALUES (
        'Grupo Inmobiliario Sur',
        'Holding de empresas de gestión inmobiliaria'
    );

-- Empresas
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
        '1',
        'Gestión Propietaria SL',
        'B12345678',
        'Juan Pérez',
        'https://api.empresa1.com',
        'Calle Mayor 1, Madrid'
    );

-- Bloques
INSERT INTO
    bloques (
        direccion,
        estado,
        api,
        empresa_id
    )
VALUES (
        'Calle Falsa 123',
        'activo',
        'https://api.bloque1.com',
        1
    );

-- Pisos
INSERT INTO
    pisos (
        direccion,
        municipio,
        cp,
        api,
        prop_vertical,
        por_habitaciones,
        bloque_id
    )
VALUES (
        'Calle Falsa 123, 1A',
        'Madrid',
        28080,
        'https://api.piso1.com',
        true,
        false,
        1
    );

-- Usuarios
INSERT INTO
    usuarios (
        alias,
        nombre,
        apellidos,
        email,
        telefono,
        grupo_por_defecto,
        grupos,
        roles,
        activo
    )
VALUES (
        'jlopez',
        'Julia',
        'López García',
        'julia.lopez@example.com',
        '612345678',
        'Atención',
        'Atención,Intervención',
        'admin',
        'sí'
    );

-- Afiliadas
INSERT INTO
    afiliadas (
        num_afiliada,
        nombre,
        apellidos,
        genero,
        email,
        regimen,
        estado,
        fecha_alta,
        piso_id
    )
VALUES (
        'AF-001',
        'Ana',
        'Martínez Ruiz',
        'F',
        'ana.martinez@example.com',
        'autónomo',
        'activa',
        '2023-01-15',
        1
    );

-- Conflictos
INSERT INTO
    conflictos (
        estado,
        ambito,
        afectada,
        causa,
        fecha_apertura,
        fecha_cierre,
        descripcion,
        resolucion,
        afiliada_id,
        usuario_responsable_id
    )
VALUES (
        'abierto',
        'laboral',
        'Ana Martínez Ruiz',
        'despido improcedente',
        '2023-02-01',
        NULL,
        'Reclamación de despido sin justificación.',
        NULL,
        1,
        1
    );

-- Diario de Conflictos
INSERT INTO
    diario_conflictos (
        estado,
        ambito,
        afectada,
        causa,
        conflicto_id
    )
VALUES (
        'abierto',
        'laboral',
        'Ana Martínez Ruiz',
        'despido improcedente',
        1
    );

-- Facturación
INSERT INTO
    facturacion (
        cuota,
        periodicidad,
        iban,
        afiliada_id
    )
VALUES (
        35.50,
        1,
        'ES9820385778983000760236',
        1
    );

-- Solicitudes
INSERT INTO solicitudes DEFAULT VALUES;