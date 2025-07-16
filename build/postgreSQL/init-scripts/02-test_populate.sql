-- Entramado Empresarial
INSERT INTO sindicato_inq.entramado_empresas (nombre, descripcion) VALUES
    ('Grupo Inmobiliario Sur', 'Holding de empresas de gestión inmobiliaria'),
    ('Consorcio Norte', 'Empresas de servicios y alquileres del norte'),
    ('Red Urbana', 'Plataforma de gestión urbanística');

-- Empresas
INSERT INTO sindicato_inq.empresas (entramado_id, nombre, cif_nif_nie, directivos, api, direccion_fiscal) VALUES
    ('1', 'Gestión Propietaria SL', 'B12345678', 'Juan Pérez', 'https://api.empresa1.com', 'Calle Mayor 1, Madrid'),
    ('2', 'Alquileres del Norte SA', 'A87654321', 'María González', 'https://api.empresa2.com', 'Avenida Norte 50, Bilbao'),
    ('3', 'Urbana Gestión SL', 'B24681357', 'Pedro López', 'https://api.empresa3.com', 'Calle Central 22, Valencia');

-- Bloques
INSERT INTO sindicato_inq.bloques (direccion, estado, api, empresa_id) VALUES
    ('Calle Falsa 123', 'activo', 'https://api.bloque1.com', 1),
    ('Avenida Norte 51', 'activo', 'https://api.bloque2.com', 2),
    ('Calle Central 23', 'inactivo', 'https://api.bloque3.com', 3),
    ('Plaza Mayor 10', 'activo', 'https://api.bloque4.com', 1);

-- Pisos
INSERT INTO sindicato_inq.pisos (direccion, municipio, cp, api, prop_vertical, por_habitaciones, bloque_id) VALUES
    ('Calle Falsa 123, 1A', 'Madrid', 28080, 'https://api.piso1.com', true, false, 1),
    ('Calle Falsa 123, 2B', 'Madrid', 28080, 'https://api.piso2.com', false, true, 1),
    ('Avenida Norte 51, 3C', 'Bilbao', 48001, 'https://api.piso3.com', true, false, 2),
    ('Plaza Mayor 10, 1D', 'Madrid', 28012, 'https://api.piso4.com', false, false, 4);

-- Usuarios
INSERT INTO sindicato_inq.usuarios (alias, nombre, apellidos, email, telefono, grupo_por_defecto, grupos, roles, activo) VALUES
    ('jlopez', 'Julia', 'López García', 'julia.lopez@example.com', '612345678', 'Atención', 'Atención,Intervención', 'admin', 'sí'),
    ('pfernandez', 'Pablo', 'Fernández Ruiz', 'pablo.fernandez@example.com', '623456789', 'Intervención', 'Intervención,Soporte', 'gestor', 'sí'),
    ('mmartin', 'Marta', 'Martín Sáez', 'marta.martin@example.com', '634567890', 'Soporte', 'Soporte', 'usuario', 'sí'),
    ('rdominguez', 'Raúl', 'Domínguez Gil', 'raul.dominguez@example.com', '645678901', 'Atención', 'Atención', 'usuario', 'no');

-- Afiliadas
INSERT INTO sindicato_inq.afiliadas (num_afiliada, nombre, apellidos, genero, email, regimen, estado, fecha_alta, piso_id) VALUES
    ('AF-001', 'Ana', 'Martínez Ruiz', 'F', 'ana.martinez@example.com', 'autónomo', 'activa', '2023-01-15', 1),
    ('AF-002', 'Beatriz', 'Sánchez López', 'F', 'beatriz.sanchez@example.com', 'asalariado', 'activa', '2023-03-10', 2),
    ('AF-003', 'Carlos', 'Gómez Torres', 'M', 'carlos.gomez@example.com', 'autónomo', 'inactiva', '2023-02-20', 3),
    ('AF-004', 'David', 'Pérez Fernández', 'M', 'david.perez@example.com', 'asalariado', 'activa', '2023-04-01', 4);

-- Conflictos
INSERT INTO sindicato_inq.conflictos (
    estado, ambito, afectada, causa, fecha_apertura, fecha_cierre, descripcion, resolucion, afiliada_id, usuario_responsable_id
) VALUES
    ('abierto', 'laboral', 'Ana Martínez Ruiz', 'despido improcedente', '2023-02-01', NULL, 'Reclamación de despido sin justificación.', NULL, 1, 1),
    ('cerrado', 'administrativo', 'Beatriz Sánchez López', 'impago de nómina', '2023-04-15', '2023-05-01', 'Reclamación por impago de salario de marzo.', 'Pago realizado tras mediación.', 2, 2),
    ('abierto', 'laboral', 'Carlos Gómez Torres', 'acoso laboral', '2023-05-10', NULL, 'Denuncia de acoso por parte del superior.', NULL, 3, 3),
    ('abierto', 'habitacional', 'David Pérez Fernández', 'problemas de calefacción', '2023-06-01', NULL, 'Reclamación por falta de calefacción en invierno.', NULL, 4, 1);

-- Diario de Conflictos
INSERT INTO sindicato_inq.diario_conflictos (
    estado, ambito, afectada, causa, conflicto_id
) VALUES
    ('abierto', 'laboral', 'Ana Martínez Ruiz', 'despido improcedente', 1),
    ('cerrado', 'administrativo', 'Beatriz Sánchez López', 'impago de nómina', 2),
    ('abierto', 'laboral', 'Carlos Gómez Torres', 'acoso laboral', 3),
    ('abierto', 'habitacional', 'David Pérez Fernández', 'problemas de calefacción', 4);

-- Facturación
INSERT INTO sindicato_inq.facturacion (cuota, periodicidad, iban, afiliada_id) VALUES
    (35.50, 1, 'ES9820385778983000760236', 1),
    (27.00, 2, 'ES1421000418450200051332', 2),
    (40.00, 1, 'ES7000491500052712334567', 3),
    (30.00, 3, 'ES1200120345678901234567', 4);