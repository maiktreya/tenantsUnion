-- =====================================================================
-- ARCHIVO 02: IMPORTACIÓN DESDE GRAVITY FORMS (PIPELINE AUTOMATIZADO)
-- =====================================================================

SET search_path TO sindicato_inq, public;
SET datestyle = 'ISO, DMY';  -- Prevents DD/MM/YYYY inversion errors

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

-- 2. Cargar datos del CSV generado por el Cron Bash Script
COPY staging_gravity (
    entry_id, date_created, first_name, last_name, nif_dni, birth_date, gender, 
    phone, email, address_full_google, address_street, address_number, 
    address_floor, address_door, address_city, address_postcode, num_people_in_home, 
    tenure_type, contract_start_date, landlord_contact_type, field_41, field_46, 
    field_48, field_49_1, membership_type, fee_amount, fee_period, fee_formatted, bank_iban
)
FROM '/csv-data/mariadb_export.csv'
WITH (FORMAT csv, DELIMITER ',', HEADER true);

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
-- (Confiando en el Trigger trg_normalize_piso para capitalización)
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

-- 6. Poblar Afiliadas (UPSERT CONFIANDO EN EL TRIGGER trg_normalize_afiliada)
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

-- 7. Poblar Facturación (Con limpieza de espacios en IBAN)
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