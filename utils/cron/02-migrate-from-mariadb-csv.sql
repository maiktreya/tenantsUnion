-- =====================================================================
-- ARCHIVO 02: IMPORTACIÓN DESDE GRAVITY FORMS (PIPELINE AUTOMATIZADO)
-- =====================================================================

SET search_path TO sindicato_inq, public;
SET datestyle = 'ISO, DMY';  

-- 1. Crear tabla temporal de staging
CREATE TEMP TABLE staging_gravity (
    entry_id TEXT, date_created TEXT, first_name TEXT, last_name TEXT,
    nif_dni TEXT, birth_date TEXT, gender TEXT, phone TEXT, email TEXT,
    address_full_google TEXT, address_street TEXT, address_number TEXT,
    address_floor TEXT, address_door TEXT, address_city TEXT,
    address_postcode TEXT, num_people_in_home TEXT, tenure_type TEXT,
    contract_start_date TEXT, landlord_contact_type TEXT, field_41 TEXT,
    field_46 TEXT, field_48 TEXT, field_49_1 TEXT, membership_type TEXT,
    fee_amount TEXT, fee_period TEXT, fee_formatted TEXT, bank_iban TEXT,
    computed_address TEXT
);

-- 2. Cargar datos del CSV
COPY staging_gravity (
    entry_id, date_created, first_name, last_name, nif_dni, birth_date, gender, 
    phone, email, address_full_google, address_street, address_number, 
    address_floor, address_door, address_city, address_postcode, num_people_in_home, 
    tenure_type, contract_start_date, landlord_contact_type, field_41, field_46, 
    field_48, field_49_1, membership_type, fee_amount, fee_period, fee_formatted, bank_iban
)
FROM '/csv-data/mariadb_export.csv'
WITH (FORMAT csv, DELIMITER ',', HEADER true);

-- ====================================================================================
-- 2.5 SANITIZACIÓN DE NULOS LITERALES (LA SOLUCIÓN AL ERROR DEL CRONJOB)
-- Convierte el texto "NULL" exportado por bash/mysql en verdaderos valores nulos de SQL
-- ====================================================================================
UPDATE staging_gravity
SET
    first_name = NULLIF(first_name, 'NULL'),
    last_name = NULLIF(last_name, 'NULL'),
    nif_dni = NULLIF(nif_dni, 'NULL'),
    birth_date = NULLIF(birth_date, 'NULL'),
    gender = NULLIF(gender, 'NULL'),
    phone = NULLIF(phone, 'NULL'),
    email = NULLIF(email, 'NULL'),
    address_full_google = NULLIF(address_full_google, 'NULL'),
    address_street = NULLIF(address_street, 'NULL'),
    address_number = NULLIF(address_number, 'NULL'),
    address_floor = NULLIF(address_floor, 'NULL'),
    address_door = NULLIF(address_door, 'NULL'),
    address_city = NULLIF(address_city, 'NULL'),
    address_postcode = NULLIF(address_postcode, 'NULL'),
    num_people_in_home = NULLIF(num_people_in_home, 'NULL'),
    tenure_type = NULLIF(tenure_type, 'NULL'),
    contract_start_date = NULLIF(contract_start_date, 'NULL'),
    landlord_contact_type = NULLIF(landlord_contact_type, 'NULL'),
    field_41 = NULLIF(field_41, 'NULL'),
    field_46 = NULLIF(field_46, 'NULL'),
    field_48 = NULLIF(field_48, 'NULL'),
    field_49_1 = NULLIF(field_49_1, 'NULL'),
    membership_type = NULLIF(membership_type, 'NULL'),
    fee_amount = NULLIF(fee_amount, 'NULL'),
    fee_period = NULLIF(fee_period, 'NULL'),
    fee_formatted = NULLIF(fee_formatted, 'NULL'),
    bank_iban = NULLIF(bank_iban, 'NULL');

-- 3. Normalizar la Dirección
UPDATE staging_gravity
SET computed_address = 
    TRIM(SPLIT_PART(address_full_google, ',', 1)) || 
    CASE WHEN NULLIF(TRIM(address_number), '') IS NOT NULL THEN ', ' || TRIM(address_number) ELSE '' END ||
    CASE WHEN NULLIF(TRIM(address_floor), '') IS NOT NULL THEN ', Piso ' || TRIM(address_floor) ELSE '' END ||
    CASE WHEN NULLIF(TRIM(address_door), '') IS NOT NULL THEN ', Pta ' || TRIM(address_door) ELSE '' END;

-- 4. Poblar Empresas
INSERT INTO empresas (nombre)
SELECT DISTINCT TRIM(field_48) FROM staging_gravity
WHERE NULLIF(TRIM(field_48), '') IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM empresas WHERE nombre = TRIM(staging_gravity.field_48));

-- 5. Poblar Pisos 
INSERT INTO pisos (
    direccion, municipio, cp, inmobiliaria, propiedad, prop_vertical, n_personas, fecha_firma
)
SELECT DISTINCT
    computed_address,
    TRIM(address_city), 
    CAST(NULLIF(REGEXP_REPLACE(address_postcode, '[^0-9]', '', 'g'), '') AS INTEGER),
    TRIM(field_46), TRIM(field_48), TRIM(field_49_1),
    CAST(NULLIF(REGEXP_REPLACE(num_people_in_home, '[^0-9]', '', 'g'), '') AS INTEGER),
    CAST(NULLIF(contract_start_date, '') AS DATE)
FROM staging_gravity WHERE computed_address IS NOT NULL
ON CONFLICT (direccion) DO NOTHING;

-- 5.5 Limpiar facturación "ficticia" antigua de las preafiliadas 
DELETE FROM facturacion
WHERE afiliada_id IN (
    SELECT id FROM afiliadas 
    WHERE UPPER(afiliacion) = 'FALSE'
      AND cif IN (SELECT UPPER(TRIM(nif_dni)) FROM staging_gravity)
);

-- 6. Poblar Afiliadas
INSERT INTO afiliadas (
    piso_id, num_afiliada, nombre, apellidos, cif, fecha_nac, genero, 
    email, telefono, estado, regimen, fecha_alta, nivel_participacion, afiliacion
)
SELECT 
    p.id,
    s.entry_id, 
    TRIM(s.first_name),
    TRIM(s.last_name),
    TRIM(s.nif_dni),
    CAST(NULLIF(s.birth_date, '') AS DATE),
    TRIM(s.gender),
    TRIM(s.email),
    TRIM(s.phone),
    'Alta', 
    TRIM(s.tenure_type),
    CAST(NULLIF(SPLIT_PART(s.date_created, ' ', 1), '') AS DATE), 
    TRIM(s.membership_type),
    'Importado'
FROM staging_gravity s
JOIN pisos p ON s.computed_address = p.direccion
WHERE NOT EXISTS (
    SELECT 1 FROM afiliadas a WHERE a.num_afiliada = s.entry_id
)
ON CONFLICT (cif) DO UPDATE SET
    piso_id = EXCLUDED.piso_id,
    num_afiliada = EXCLUDED.num_afiliada,
    nombre = EXCLUDED.nombre,
    apellidos = EXCLUDED.apellidos,
    fecha_nac = EXCLUDED.fecha_nac,
    genero = EXCLUDED.genero,
    email = EXCLUDED.email,
    telefono = EXCLUDED.telefono,
    estado = EXCLUDED.estado,
    regimen = EXCLUDED.regimen,
    fecha_alta = EXCLUDED.fecha_alta,
    nivel_participacion = EXCLUDED.nivel_participacion,
    afiliacion = 'Importado'
WHERE UPPER(afiliadas.afiliacion) = 'FALSE';

-- 7. Poblar Facturación 
INSERT INTO facturacion (afiliada_id, cuota, periodicidad, forma_pago, iban)
SELECT 
    a.id,
    CAST(REPLACE(NULLIF(s.fee_amount, ''), ',', '.') AS DECIMAL(8, 2)),
    CASE TRIM(LOWER(s.fee_period)) WHEN 'año' THEN 1 WHEN 'mes' THEN 12 ELSE 0 END,
    CASE WHEN UPPER(REGEXP_REPLACE(s.bank_iban, '\s+', '', 'g')) ~ '^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$' THEN 'Domiciliación' ELSE 'Metálico' END,
    CASE WHEN UPPER(REGEXP_REPLACE(s.bank_iban, '\s+', '', 'g')) ~ '^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$' THEN UPPER(REGEXP_REPLACE(s.bank_iban, '\s+', '', 'g')) ELSE NULL END
FROM staging_gravity s
JOIN afiliadas a ON s.entry_id = a.num_afiliada
WHERE NOT EXISTS (
    SELECT 1 FROM facturacion f WHERE f.afiliada_id = a.id
);

-- 8. Limpieza final
DROP TABLE staging_gravity;