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
-- 04-populate: roles + usuarios semilla + datos de referencia (provincias)
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

-- =====================================================================
-- PROVINCIAS: poblado de la tabla de lookup `provincias`
-- =====================================================================
-- 52 provincias españolas (50 + Ceuta y Melilla) ORDENADAS por el código
-- oficial INE (01..52). Al insertarse en orden, el `id` SERIAL autogenerado
-- coincide con el `code` INE de la provincia.
--
-- `provincias.code` (UNIQUE) es la clave natural usada por el trigger
-- `trigger_b_set_provincia_from_cp` (ver 02-init-plpgsql_functions.sql)
-- para resolver `pisos.provincia_id` a partir del CP.
--
-- Idempotente: ON CONFLICT (code) DO NOTHING (re-ejecuciones seguras).
-- El TRUNCATE inicial de este script NO toca `provincias` (es tabla de
-- referencia, no está en su lista de TRUNCATE ni es hija en cascade de
-- ninguno de los tablas listadas), así que el insert es seguro aquí.
-- Debe poblarse ANTES de 05-init-artificial_data.sql, que inserta pisos
-- cuyo trigger_b_set_provincia_from_cp resolverá la provincia por lookup.
INSERT INTO provincias (code, nombre)
VALUES
    (1,  'Araba/Álava'),
    (2,  'Albacete'),
    (3,  'Alicante/Alacant'),
    (4,  'Almería'),
    (5,  'Ávila'),
    (6,  'Badajoz'),
    (7,  'Illes Balears'),
    (8,  'Barcelona'),
    (9,  'Burgos'),
    (10, 'Cáceres'),
    (11, 'Cádiz'),
    (12, 'Castellón/Castelló'),
    (13, 'Ciudad Real'),
    (14, 'Córdoba'),
    (15, 'A Coruña'),
    (16, 'Cuenca'),
    (17, 'Girona'),
    (18, 'Granada'),
    (19, 'Guadalajara'),
    (20, 'Gipuzkoa/Guipúzcoa'),
    (21, 'Huelva'),
    (22, 'Huesca'),
    (23, 'Jaén'),
    (24, 'León'),
    (25, 'Lleida'),
    (26, 'La Rioja'),
    (27, 'Lugo'),
    (28, 'Madrid'),
    (29, 'Málaga'),
    (30, 'Murcia'),
    (31, 'Navarra/Nafarroa'),
    (32, 'Ourense'),
    (33, 'Asturias'),
    (34, 'Palencia'),
    (35, 'Las Palmas'),
    (36, 'Pontevedra'),
    (37, 'Salamanca'),
    (38, 'Santa Cruz de Tenerife'),
    (39, 'Cantabria'),
    (40, 'Segovia'),
    (41, 'Sevilla'),
    (42, 'Soria'),
    (43, 'Tarragona'),
    (44, 'Teruel'),
    (45, 'Toledo'),
    (46, 'Valencia/València'),
    (47, 'Valladolid'),
    (48, 'Bizkaia/Vizcaya'),
    (49, 'Zamora'),
    (50, 'Zaragoza'),
    (51, 'Ceuta'),
    (52, 'Melilla')
ON CONFLICT (code) DO NOTHING;

