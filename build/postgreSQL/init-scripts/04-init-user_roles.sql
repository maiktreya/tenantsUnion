-- =====================================================================
-- SCRIPT DE DATOS ARTIFICIALES PARA PRUEBAS (VERSIÓN REVISADA Y CORREGIDA)
-- =====================================================================
-- Este script puebla la base de datos con datos artificiales. Para funcionar
-- desde 01-init hasta 03-init files deben haberse corrido con anterioridad.
--
-- REVISIÓN: El esquema de las tablas comunes ha sido sincronizado con
-- el script de producción '01-init-schema-and-data.sql'.
-- Las vistas han sido revisadas para garantizar que cada una
-- exponga una clave primaria consistente como 'id', alineándose con
-- las mejores prácticas para el consumo por parte de la API y el frontend.
-- =====================================================================

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- 04-init user-roles:
-- =====================================================================

TRUNCATE TABLE diario_conflictos,
conflictos,
asesorias,
facturacion,
afiliadas,
pisos,
agrupacion_bloques,
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
        '$2b$12$gVMWfDAGD3K7cG0IgaAmxOLsa9hBDN2FK3iFU96R7JZ7d6t.tzrBC'
    ),
    (
        2,
        '$2b$12$Vr5p/mTdYLOxjSzCj0bdV.YpJCQAz5mkYZBS/8wSX5HAwf8etbzUe'
    ),
    (
        3,
        '$2b$12$fUC/WbD0gQMAyAvpPveD5.AZSh9uTQWmHScILf8jl00L5lH7uSTAK'
    );

INSERT INTO
    usuario_roles (usuario_id, role_id)
VALUES (1, 1),
    (2, 2),
    (3, 3);

