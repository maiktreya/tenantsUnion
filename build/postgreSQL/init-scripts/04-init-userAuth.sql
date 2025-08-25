-- Create the dedicated schema for authentication
CREATE SCHEMA IF NOT EXISTS auth;
SET search_path TO auth, sindicato_inq, public;

-- Move the tables into the 'auth' schema
CREATE TABLE auth.usuario_credenciales (
    -- This foreign key now needs to explicitly reference the main schema
    usuario_id INTEGER PRIMARY KEY REFERENCES sindicato_inq.usuarios(id) ON DELETE CASCADE,
    -- Default hashed password for "12345678" using bcrypt with cost factor 12
    password_hash TEXT DEFAULT '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXfs2E4Y0Q5W'
);

CREATE TABLE auth.roles (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE auth.usuario_roles (
    -- Also references the main schema
    usuario_id INTEGER REFERENCES sindicato_inq.usuarios(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES auth.roles(id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, role_id)
);

-- Índices para optimizar las uniones.
CREATE INDEX idx_usuario_roles_usuario_id ON auth.usuario_roles (usuario_id);
CREATE INDEX idx_usuario_roles_role_id ON auth.usuario_roles (role_id);



-- If you want to populate credentials for existing users with the default password:
INSERT INTO auth.usuario_credenciales (usuario_id)
SELECT id FROM sindicato_inq.usuarios
WHERE id NOT IN (SELECT usuario_id FROM auth.usuario_credenciales);

-- Ejemplo de inserción de datos (a modo de demostración)
INSERT INTO auth.roles (nombre, descripcion) VALUES ('admin', 'Administrador con todos los permisos');
INSERT INTO auth.roles (nombre, descripcion) VALUES ('gestor', 'Gestor de conflictos y afiliadas');

-- Para asignar el rol 'admin' al usuario con id 1:
-- INSERT INTO auth.usuario_roles (usuario_id, role_id) VALUES (1, 1);