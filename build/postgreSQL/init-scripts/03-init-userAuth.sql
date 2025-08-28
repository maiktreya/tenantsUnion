-- Create the dedicated schema for sindicato_inqentication
CREATE SCHEMA IF NOT EXISTS sindicato_inq;

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

-- If you want to populate credentials for existing users with the default password:
INSERT INTO
    sindicato_inq.usuario_credenciales (usuario_id)
SELECT id
FROM sindicato_inq.usuarios
WHERE
    id NOT IN(
        SELECT usuario_id
        FROM sindicato_inq.usuario_credenciales
    );

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

UPDATE sindicato_inq.usuario_credenciales
SET
    password_hash = '$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6'
WHERE
    usuario_id = 1;

INSERT INTO
    sindicato_inq.usuario_roles (usuario_id, role_id)
VALUES (1, 1);