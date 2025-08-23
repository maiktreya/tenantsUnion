-- =====================================================================
-- PARTE B.1: MEJORA DE LA TABLA DE USUARIOS
-- =====================================================================
-- Se añaden campos para el estado del usuario.
ALTER TABLE usuarios
ADD COLUMN is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN created_at TIMESTAMP
WITH
    TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- =====================================================================
-- PARTE B.2: TABLA DE CREDENCIALES
-- =====================================================================
-- Almacena de forma segura los hashes de las contraseñas, separada de
-- la información personal del usuario.
CREATE TABLE usuario_credenciales (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuarios (id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL
);

-- =====================================================================
-- PARTE B.3: GESTIÓN DE ROLES Y PERMISOS
-- =====================================================================
-- La tabla 'roles' define los niveles de permiso en la aplicación.
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

-- La tabla 'usuario_roles' asigna roles a los usuarios (relación N:M).
CREATE TABLE usuario_roles (
    usuario_id INTEGER REFERENCES usuarios (id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles (id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, role_id)
);

-- Índices para optimizar las uniones.
CREATE INDEX idx_usuario_roles_usuario_id ON usuario_roles (usuario_id);

CREATE INDEX idx_usuario_roles_role_id ON usuario_roles (role_id);

-- Ejemplo de inserción de datos (a modo de demostración)
-- INSERT INTO roles (nombre, descripcion) VALUES ('admin', 'Administrador con todos los permisos');
-- INSERT INTO roles (nombre, descripcion) VALUES ('gestor', 'Gestor de conflictos y afiliadas');

-- Para asignar el rol 'admin' al usuario con id 1:
-- INSERT INTO usuario_roles (usuario_id, role_id) VALUES (1, 1);