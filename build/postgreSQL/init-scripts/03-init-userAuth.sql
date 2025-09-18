--- PostgreSQL script to create user authentication and authorization tables

SET search_path TO sindicato_inq;

-- Move the tables into the 'sindicato_inq' schema
CREATE TABLE sindicato_inq.usuario_credenciales (
    -- This foreign key now needs to explicitly reference the main schema
    usuario_id INTEGER PRIMARY KEY REFERENCES sindicato_inq.usuarios (id) ON DELETE CASCADE,
    -- Default hashed password for "12345678" using bcrypt with cost factor 12
    password_hash TEXT DEFAULT ''
);

CREATE TABLE sindicato_inq.roles (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE sindicato_inq.usuario_roles (
    -- Also references the main schema
    usuario_id INTEGER REFERENCES sindicato_inq.usuarios (id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES sindicato_inq.roles (id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, role_id)
);

-- Índices para optimizar las uniones.
CREATE INDEX idx_usuario_roles_usuario_id ON sindicato_inq.usuario_roles (usuario_id);

CREATE INDEX idx_usuario_roles_role_id ON sindicato_inq.usuario_roles (role_id);

-- populate credentials for existing users with the default password:
INSERT INTO
    sindicato_inq.usuario_credenciales (usuario_id)
SELECT id
FROM sindicato_inq.usuarios
WHERE
    id NOT IN (
        SELECT usuario_id
        FROM sindicato_inq.usuario_credenciales
    );

-- initial setup of roles
INSERT INTO
    sindicato_inq.roles (nombre, descripcion)
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
        'Perfil básico para gestionar actas y documentos'
    );

INSERT INTO
    usuarios (
        alias,
        nombre,
        apellidos,
        email,
        is_active
    )
VALUES (
        'gestor',
        'test',
        'test',
        'gestor@inquilinato.org',
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
    sindicato_inq.usuario_roles (usuario_id, role_id)
VALUES (1, 1),
    (14, 2),
    (15, 3);

-- Assign the 'admin' role to the first user (assumed to be the superuser) & the two additional roles created
-- and reset their password to "12345678" (hashed).

UPDATE sindicato_inq.usuario_credenciales
SET
    password_hash = '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
WHERE
    usuario_id = 1;

-- create credentials with same default password for new test users for the two additional roles created
INSERT INTO
    usuario_credenciales (usuario_id, password_hash)
VALUES (
        14,
        '$2 b$12$J23QHdoGZ434MQIZH7FwEew.VMDftluCBEugd8LKLIE3B8NCuGKy6'
    ),
    (
        15,
        '$2b$12$.2k0jdsNjg6J/lcZL1WBkej85pFdSTq2NWdFBjPgfZ7EXjAbjoSei'
    );