


-- PostgreSQL Database Schema for Spanish Tenant Union
-- To be used as Docker init script

-- Database: tenant_union_db
DROP DATABASE IF EXISTS tenant_union_db;
CREATE DATABASE tenant_union_db
    WITH
    OWNER = app_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'es_ES.utf8'
    LC_CTYPE = 'es_ES.utf8'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

-- Connect to the newly created database
\c tenant_union_db;

-- Set up extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema
CREATE SCHEMA IF NOT EXISTS tenant_union;
SET search_path TO tenant_union, public;

-- 1. EMPRESAS (Companies/Property Management Companies)
CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    cif_nif_nie TEXT,
    entramado TEXT,
    directivos TEXT,
    api TEXT,
    direccion TEXT,
    num_afiliadas TEXT,
    num_inq_colaboradoras TEXT,
    num_afiliadas_adm TEXT,
    num_inq_colaboradoras_adm TEXT,
    viviendas_informadas TEXT,
    superficie_informada TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. BLOQUES (Building Blocks/Properties)
CREATE TABLE bloques (
    id SERIAL PRIMARY KEY,
    direccion TEXT,
    estado TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    num_afiliadas TEXT,
    num_preafiliadas TEXT,
    num_inq_colaboradoras TEXT,
    empresa_id INTEGER REFERENCES empresas(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. USUARIOS (System Users - Union Staff/Volunteers)
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    codigo TEXT,
    nombre TEXT,
    apellidos TEXT,
    correo_electronico TEXT,
    telefono TEXT,
    grupo_por_defecto TEXT,
    grupos TEXT,
    roles TEXT,
    activo TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. AFILIADAS (Union Members/Tenants)
CREATE TABLE afiliadas (
    id SERIAL PRIMARY KEY,
    num_afiliada TEXT,
    nombre TEXT,
    apellidos TEXT,
    genero TEXT,
    email TEXT,
    direccion TEXT,
    municipio TEXT,
    codigo_postal TEXT,
    regimen TEXT,
    estado TEXT DEFAULT NULL,
    fecha_alta TEXT,
    fecha_baja TEXT,
    prop_vertical TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    bloque_id INTEGER REFERENCES bloques(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. CONFLICTOS (Conflicts/Disputes)
CREATE TABLE conflictos (
    id SERIAL PRIMARY KEY,
    estado TEXT DEFAULT NULL,
    ambito TEXT,
    afectada TEXT,
    causa TEXT,
    fecha_apertura TEXT,
    fecha_cierre TEXT,
    descripcion TEXT,
    resolucion TEXT,
    afiliada_id INTEGER REFERENCES afiliadas(id) ON DELETE SET NULL,
    usuario_responsable_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. ASESORIAS (Advisory Services)
CREATE TABLE asesorias (
    id SERIAL PRIMARY KEY,
    estado TEXT DEFAULT NULL,
    fecha_asesoria TEXT,
    fecha_contacto TEXT,
    fecha_finalizacion TEXT,
    tipo_beneficiaria TEXT,
    beneficiaria TEXT,
    tipo TEXT,
    tecnica TEXT,
    resultado TEXT,
    observaciones TEXT,
    afiliada_id INTEGER REFERENCES afiliadas(id) ON DELETE SET NULL,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create basic indexes for IDs and foreign keys
CREATE INDEX idx_empresas_id ON empresas(id);
CREATE INDEX idx_bloques_id ON bloques(id);
CREATE INDEX idx_bloques_empresa ON bloques(empresa_id);
CREATE INDEX idx_usuarios_id ON usuarios(id);
CREATE INDEX idx_afiliadas_id ON afiliadas(id);
CREATE INDEX idx_afiliadas_bloque ON afiliadas(bloque_id);
CREATE INDEX idx_conflictos_id ON conflictos(id);
CREATE INDEX idx_conflictos_afiliada ON conflictos(afiliada_id);
CREATE INDEX idx_asesorias_id ON asesorias(id);
CREATE INDEX idx_asesorias_afiliada ON asesorias(afiliada_id);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_empresas_updated_at BEFORE UPDATE ON empresas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bloques_updated_at BEFORE UPDATE ON bloques FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_usuarios_updated_at BEFORE UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_afiliadas_updated_at BEFORE UPDATE ON afiliadas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conflictos_updated_at BEFORE UPDATE ON conflictos FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_asesorias_updated_at BEFORE UPDATE ON asesorias FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data based on your CSV files (all as TEXT to avoid type conflicts)
INSERT INTO empresas (nombre, cif_nif_nie, entramado, directivos, api, direccion, num_afiliadas, num_inq_colaboradoras, num_afiliadas_adm, num_inq_colaboradoras_adm, viviendas_informadas, superficie_informada) VALUES
('FIDERE VIVIENDA SL', 'B86657590', 'Blackstone', '', 'No', 'Paseo Castellana, 257, Madrid, España', '184', '0', '24', '0', '', ''),
('NESTAR RESIDENCIAL SII SA.', 'A83787382', '', '', 'No', 'Calle de Villanueva, 2, Madrid, España', '181', '0', '161', '0', '2208', ''),
('TESTA RESIDENCIAL, SOCIMI, S.A.', 'B82865890', 'Blackstone', '', 'No', 'P.º de la Castellana, 257, 28046 Madrid, España', '31', '0', '13', '0', '47', '2473'),
('SAREB', '', '', '', 'No', '', '20', '0', '0', '0', '', '');

INSERT INTO bloques (direccion, estado, api, propiedad, entramado, num_afiliadas, num_preafiliadas, num_inq_colaboradoras, empresa_id) VALUES
('Calle Juan Gris, 4, 28850, Torrejón de Ardoz, Espanya', '', '', 'FIDERE VIVIENDA SL', 'Blackstone', '47', '0', '0', 1),
('Calle Martín Muñoz de las Posadas, 7, 28031, Madrid, Espanya', '', '', 'NESTAR RESIDENCIAL SII SA.', 'NESTAR RESIDENCIAL SII SA.', '21', '0', '0', 2);

INSERT INTO usuarios (codigo, nombre, apellidos, correo_electronico, telefono, grupo_por_defecto, grupos, roles) VALUES
('sumate', 'Sumate', '(sistemas)', 'sumate@inquilinato.org', '', 'Sindicato de Inquilinas', 'Sección Sindical Madrid', 'Sistemas'),
('ana.sanchez', 'Ana', 'Sánchez', 'snchz.rojo@gmail.com', '', 'Sindicato de Inquilinas', 'Sección Sindical Madrid', 'Sistemas'),
('paula', 'Paula', 'Villega', 'paulavmartin@gmail.com', '', 'Sindicato de Inquilinas', 'Sindicato de Inquilinas, Sección Sindical Madrid', 'Delegada'),
('ptoapoyo', 'Punto', 'Apoyo', 'albertt_1998@hotmail.com', '', 'Sindicato de Inquilinas', 'Sindicato de Inquilinas, Sección Sindical Zona Sur', 'Coordinadora de Delegadas'),
('Organizacion', 'Remunerada', 'Organización', 'racu.valeria@gmail.com', '', 'Sindicato de Inquilinas', 'Sindicato de Inquilinas, Sección Sindical Madrid', 'Sistemas'),
('Daniel David', 'Daniel David', 'Abellan', 'inquilinodaniel@gmail.com', '', 'Sindicato de Inquilinas', 'Sindicato de Inquilinas, Sección Sindical Madrid', 'Delegada'),
('Pablo Alberto', 'Pablo P.', 'y Alberto', 'pablopruiz@gmail.com', '', 'Sindicato de Inquilinas', 'Sindicato de Inquilinas, Sección Sindical Madrid', 'Sistemas'),
('Alba MC', 'Alba', 'Moliner', 'albamolinercros@gmail.com', '', 'Sindicato de Inquilinas', '', 'Sistemas'),
('DaniMR', 'Daniel', 'Martinez Ruiz', 'martinez.ruiz.daniel@gmail.com', '', 'Sindicato de Inquilinas', '', 'Coordinadora de Delegadas'),
('Alex CL', 'Alex', 'CL', 'alesterzabala@gmail.com', '', 'Sindicato de Inquilinas', '', 'Coordinadora de Delegadas'),
('Elisa', 'Elisa', 'Organización', 'elisamu15@gmail.com', '', 'Sindicato de Inquilinas', '', 'Sistemas'),
('Blanca', 'Blanca', 'Comu', 'blcmartinezlopez@gmail.com', '', 'Sindicato de Inquilinas', '', 'Coordinadora de Delegadas'),
('Adri ', 'Adri', 'AS Sur', 'sherpa.rt28@gmail.com', '', 'Sección Sindical Zona Sur', '', 'Coordinadora de Delegadas');

INSERT INTO conflictos (estado, ambito, afectada, causa, fecha_apertura) VALUES
('Abierto', 'Afiliada', 'Robert Both', 'No renovación', '17/01/2025'),
('Abierto', 'Afiliada', 'Elena Quintero Roldán', 'No renovación', '17/01/2025');

INSERT INTO asesorias (estado, fecha_asesoria, fecha_contacto, fecha_finalizacion, tipo_beneficiaria, beneficiaria, tipo, tecnica, resultado) VALUES
('Resuelto', '23/05/2024', '', '23/05/2024', 'Afiliada', 'Alberto Martínez Casado', 'Asesoría Gratuita', 'Carlos Castillo', 'duda resuelta');

-- Create basic views for common queries
CREATE VIEW vista_conflictos_activos AS
SELECT 
    c.*,
    a.nombre || ' ' || a.apellidos as nombre_completo_afiliada,
    u.nombre || ' ' || u.apellidos as responsable
FROM conflictos c
LEFT JOIN afiliadas a ON c.afiliada_id = a.id
LEFT JOIN usuarios u ON c.usuario_responsable_id = u.id
WHERE c.estado = 'Abierto';

CREATE VIEW vista_empresas_estadisticas AS
SELECT 
    e.nombre,
    e.entramado,
    e.num_afiliadas,
    e.num_inq_colaboradoras,
    COUNT(b.id) as num_bloques_registrados,
    e.viviendas_informadas,
    e.superficie_informada
FROM empresas e
LEFT JOIN bloques b ON e.id = b.empresa_id
GROUP BY e.id, e.nombre, e.entramado, e.num_afiliadas, e.num_inq_colaboradoras, e.viviendas_informadas, e.superficie_informada;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tenant_union TO app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA tenant_union TO app_user;

COMMIT;









-- PostgreSQL COPY Commands for CSV Import
-- Make sure to use the correct CSV file for each table!

-- 1. EMPRESAS table from Empresas.csv
\copy tenant_union.empresas(nombre, cif_nif_nie, entramado, directivos, api, direccion, num_afiliadas, num_inq_colaboradoras, num_afiliadas_adm, num_inq_colaboradoras_adm, viviendas_informadas, superficie_informada) FROM 'C:/Users/70254057/DOWNLO~1/revisar/db_fork/Empresas.csv' WITH(FORMAT csv, DELIMITER ';', HEADER, ENCODING 'UTF8', QUOTE '"', NULL '', ESCAPE '"');

-- 2. BLOQUES table from Bloques.csv
\copy tenant_union.bloques(direccion, estado, api, propiedad, entramado, num_afiliadas, num_preafiliadas, num_inq_colaboradoras) FROM 'C:/Users/70254057/DOWNLO~1/revisar/db_fork/Bloques.csv' WITH(FORMAT csv, DELIMITER ';', HEADER, ENCODING 'UTF8', QUOTE '"', NULL '', ESCAPE '"');

-- 3. USUARIOS table from Usuarios.csv
\copy tenant_union.usuarios(codigo, nombre, apellidos, correo_electronico, telefono, grupo_por_defecto, grupos, roles) FROM 'C:/Users/70254057/DOWNLO~1/revisar/db_fork/Usuarios.csv' WITH(FORMAT csv, DELIMITER ';', HEADER, ENCODING 'UTF8', QUOTE '"', NULL '', ESCAPE '"');

-- 4. AFILIADAS table from Afiliadas_empty.csv (this file appears to be empty with only headers)
-- Since Afiliadas_empty.csv only has headers, you might want to skip this or create a proper Afiliadas.csv file
-- \copy tenant_union.afiliadas(num_afiliada, nombre, apellidos, genero, email, direccion, municipio, codigo_postal, regimen, estado, fecha_alta, fecha_baja, prop_vertical, api, propiedad, entramado) FROM 'C:/Users/70254057/DOWNLO~1/revisar/db_fork/Afiliadas_empty.csv' WITH(FORMAT csv, DELIMITER ';', HEADER, ENCODING 'UTF8', QUOTE '"', NULL '', ESCAPE '"');

-- 5. CONFLICTOS table from Conflictos.csv
\copy tenant_union.conflictos(estado, ambito, afectada, causa, fecha_apertura) FROM 'C:/Users/70254057/DOWNLO~1/revisar/db_fork/Conflictos.csv' WITH(FORMAT csv, DELIMITER ';', HEADER, ENCODING 'UTF8', QUOTE '"', NULL '', ESCAPE '"');

-- 6. ASESORIAS table from Asesorías.csv
\copy tenant_union.asesorias(estado, fecha_asesoria, fecha_contacto, fecha_finalizacion, tipo_beneficiaria, beneficiaria, tipo, tecnica, resultado) FROM 'C:/Users/70254057/DOWNLO~1/revisar/db_fork/Asesorias.csv' WITH(FORMAT csv, DELIMITER ';', HEADER, ENCODING 'UTF8', QUOTE '"', NULL '', ESCAPE '"');



