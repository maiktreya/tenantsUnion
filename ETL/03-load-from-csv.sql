-- =====================================================================
-- ARCHIVO 03: IMPORTACIÓN Y ENRIQUECIMIENTO ESPACIAL DESDE GRAVITY FORMS
-- REFACTORIZADO: INTEGRACIÓN DE POSTGIS Y AGRUPACIÓN AUTOMÁTICA DE BLOQUES
-- =====================================================================

SET search_path TO sindicato_inq, public;
SET datestyle = 'ISO, DMY';  

-- 1. Crear tabla temporal de staging (Actualizada con los 3 campos de enriquecimiento)
CREATE TEMP TABLE staging_gravity (
    entry_id TEXT, date_created TEXT, first_name TEXT, last_name TEXT,
    nif_dni TEXT, birth_date TEXT, gender TEXT, phone TEXT, email TEXT,
    address_full_google TEXT, address_street TEXT, address_number TEXT,
    address_floor TEXT, address_door TEXT, address_city TEXT,
    address_postcode TEXT, num_people_in_home TEXT, tenure_type TEXT,
    contract_start_date TEXT, landlord_contact_type TEXT, field_41 TEXT,
    field_46 TEXT, field_48 TEXT, field_49_1 TEXT, membership_type TEXT,
    fee_amount TEXT, fee_period TEXT, fee_formatted TEXT, bank_iban TEXT,
    ref_catastral TEXT, coordenadas TEXT, geocoded_address TEXT, -- Nuevas columnas de Python
    computed_address TEXT
);

-- 2. Cargar datos del CSV (Estructura de COPY sincronizada)
COPY staging_gravity (
    entry_id, date_created, first_name, last_name, nif_dni, birth_date, gender, 
    phone, email, address_full_google, address_street, address_number, 
    address_floor, address_door, address_city, address_postcode, num_people_in_home, 
    tenure_type, contract_start_date, landlord_contact_type, field_41, field_46, 
    field_48, field_49_1, membership_type, fee_amount, fee_period, fee_formatted, bank_iban,
    ref_catastral, coordenadas, geocoded_address
)
FROM '/csv-data/mariadb_export.csv'
WITH (FORMAT csv, DELIMITER ',', HEADER true);

-- ====================================================================================
-- 2.5 SANITIZACIÓN DE NULOS LITERALES
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
    bank_iban = NULLIF(bank_iban, 'NULL'),
    ref_catastral = NULLIF(ref_catastral, 'NULL'),
    coordenadas = NULLIF(coordenadas, 'NULL'),
    geocoded_address = NULLIF(geocoded_address, 'NULL');

-- ====================================================================================
-- 3. NORMALIZACIÓN AVANZADA DE DIRECCIÓN (Basada en geocoded_address)
-- Reemplaza la dirección antigua por la versión sanitizada de CartoCiudad,
-- aplicando reducciones de abreviaturas uniformes y corrigiendo Capitalización (INITCAP)
-- ====================================================================================
UPDATE staging_gravity
SET computed_address = 
    INITCAP(
        REGEXP_REPLACE(
            REGEXP_REPLACE(TRIM(geocoded_address), '\yCalle\y', 'C.', 'ig'),
            '\yAvenida\y', 'Av.', 'ig'
        )
    )
WHERE geocoded_address IS NOT NULL;

-- Fallback por si la geolocalización falló por completo para no perder el registro
UPDATE staging_gravity
SET computed_address = 
    INITCAP(
        REGEXP_REPLACE(
            REGEXP_REPLACE(TRIM(SPLIT_PART(address_full_google, ',', 1)), '\yCalle\y', 'C.', 'ig'),
            '\yAvenida\y', 'Av.', 'ig'
        )
    ) || 
    CASE WHEN NULLIF(TRIM(address_number), '') IS NOT NULL THEN ', ' || TRIM(address_number) ELSE '' END ||
    CASE WHEN NULLIF(TRIM(address_floor), '') IS NOT NULL THEN ', Piso ' || TRIM(address_floor) ELSE '' END ||
    CASE WHEN NULLIF(TRIM(address_door), '') IS NOT NULL THEN ', Pta ' || TRIM(address_door) ELSE '' END
WHERE computed_address IS NULL AND address_full_google IS NOT NULL;

-- 4. Poblar Empresas
INSERT INTO empresas (nombre)
SELECT DISTINCT TRIM(field_48) FROM staging_gravity
WHERE NULLIF(TRIM(field_48), '') IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM empresas WHERE nombre = TRIM(staging_gravity.field_48));

-- ====================================================================================
-- 5. POBLAR PISOS (Incluyendo Datos de Catastro y Coordenadas Geográficas)
-- Convertimos "Lat, Lng" de texto a un objeto nativo de tipo Punto Espacial (SRID 4326)
-- ====================================================================================
INSERT INTO pisos (
    direccion, municipio, cp, inmobiliaria, propiedad, prop_vertical, n_personas, 
    fecha_firma, ref_catastral, coordenadas
)
SELECT DISTINCT
    computed_address,
    TRIM(address_city), 
    CAST(NULLIF(REGEXP_REPLACE(address_postcode, '[^0-9]', '', 'g'), '') AS INTEGER),
    TRIM(field_46), TRIM(field_48), TRIM(field_49_1),
    CAST(NULLIF(REGEXP_REPLACE(num_people_in_home, '[^0-9]', '', 'g'), '') AS INTEGER),
    CAST(NULLIF(contract_start_date, '') AS DATE),
    NULLIF(TRIM(ref_catastral), ''),
    -- PostGIS requiere Longitud (segmento 2) primero, luego Latitud (segmento 1)
    CASE WHEN NULLIF(TRIM(coordenadas), '') IS NOT NULL THEN
        ST_SetSRID(ST_MakePoint(
            CAST(TRIM(SPLIT_PART(coordenadas, ',', 2)) AS DOUBLE PRECISION),
            CAST(TRIM(SPLIT_PART(coordenadas, ',', 1)) AS DOUBLE PRECISION)
        ), 4326)
    ELSE NULL END
FROM staging_gravity WHERE computed_address IS NOT NULL
ON CONFLICT (direccion) DO UPDATE SET
    ref_catastral = COALESCE(EXCLUDED.ref_catastral, pisos.ref_catastral),
    coordenadas = COALESCE(EXCLUDED.coordenadas, pisos.coordenadas),
    municipio = EXCLUDED.municipio,
    cp = EXCLUDED.cp,
    inmobiliaria = EXCLUDED.inmobiliaria,
    propiedad = EXCLUDED.propiedad,
    prop_vertical = EXCLUDED.prop_vertical,
    n_personas = EXCLUDED.n_personas,
    fecha_firma = EXCLUDED.fecha_firma,
    updated_at = CURRENT_TIMESTAMP;

-- ====================================================================================
-- 5.1 ORQUESTACIÓN DE PARENTALIDAD DE BLOQUES (TU LÓGICA DE PROPIEDAD VERTICAL)
-- ====================================================================================

-- PASO A: Si ya existe un bloque asociado a este Catastro en la BD, vincular el nuevo piso automáticamente
UPDATE pisos p
SET bloque_id = sub.max_bloque_id
FROM (
    SELECT ref_catastral, MAX(bloque_id) as max_bloque_id
    FROM pisos
    WHERE ref_catastral IS NOT NULL AND bloque_id IS NOT NULL
    GROUP BY ref_catastral
) sub
WHERE p.ref_catastral = sub.ref_catastral
  AND p.bloque_id IS NULL;

-- PASO B: Si es Propiedad Vertical y ningún piso con este catastro tiene bloque, crear el Bloque base (Calle + Número)
INSERT INTO bloques (direccion, empresa_id)
SELECT DISTINCT
    -- Extraemos solo Calle y Número del geocoded_address original usando comas
    INITCAP(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                TRIM(SPLIT_PART(s.geocoded_address, ',', 1)) || 
                CASE WHEN NULLIF(TRIM(SPLIT_PART(s.geocoded_address, ',', 2)), '') IS NOT NULL 
                     THEN ', ' || TRIM(SPLIT_PART(s.geocoded_address, ',', 2)) ELSE '' END,
                '\yCalle\y', 'C.', 'ig'
            ),
            '\yAvenida\y', 'Av.', 'ig'
        )
    ),
    e.id
FROM staging_gravity s
LEFT JOIN empresas e ON TRIM(s.field_48) = e.nombre
JOIN pisos p ON p.direccion = s.computed_address
WHERE NULLIF(TRIM(p.prop_vertical), '') IS NOT NULL -- Flag de Propiedad Vertical activo
  AND p.ref_catastral IS NOT NULL
  AND p.bloque_id IS NULL
ON CONFLICT (direccion) DO NOTHING;

-- PASO C: Vincular el bloque recién creado al piso que lo generó
UPDATE pisos p
SET bloque_id = b.id
FROM staging_gravity s
JOIN bloques b ON b.direccion = INITCAP(
    REGEXP_REPLACE(
        REGEXP_REPLACE(
            TRIM(SPLIT_PART(s.geocoded_address, ',', 1)) || 
            CASE WHEN NULLIF(TRIM(SPLIT_PART(s.geocoded_address, ',', 2)), '') IS NOT NULL 
                 THEN ', ' || TRIM(SPLIT_PART(s.geocoded_address, ',', 2)) ELSE '' END,
            '\yCalle\y', 'C.', 'ig'
        ),
        '\yAvenida\y', 'Av.', 'ig'
    )
)
WHERE p.direccion = s.computed_address
  AND p.bloque_id IS NULL;

-- PASO D: Efecto Cascada - Propagar el bloque id a CUALQUIER otro piso con la misma Ref. Catastral en la BD
UPDATE pisos p
SET bloque_id = sub.max_bloque_id
FROM (
    SELECT ref_catastral, MAX(bloque_id) as max_bloque_id
    FROM pisos
    WHERE ref_catastral IS NOT NULL AND bloque_id IS NOT NULL
    GROUP BY ref_catastral
) sub
WHERE p.ref_catastral = sub.ref_catastral
  AND p.bloque_id IS NULL;


-- ====================================================================================
-- 5.5 LIMPIEZA DE FACTURACIÓN ANTERIOR
-- ====================================================================================
DELETE FROM facturacion
WHERE afiliada_id IN (
    SELECT id FROM afiliadas 
    WHERE UPPER(TRIM(cif)) IN (SELECT UPPER(TRIM(nif_dni)) FROM staging_gravity)
);

-- ====================================================================================
-- 6. POBLAR AFILIADAS
-- ====================================================================================
INSERT INTO afiliadas (
    piso_id, nombre, apellidos, cif, fecha_nac, genero, 
    email, telefono, estado, regimen, fecha_alta, nivel_participacion, afiliacion
)
SELECT 
    p.id,
    TRIM(s.first_name),
    TRIM(s.last_name),
    UPPER(TRIM(s.nif_dni)), 
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
ON CONFLICT (cif) DO UPDATE SET
    piso_id = EXCLUDED.piso_id,
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
WHERE UPPER(afiliadas.afiliacion) = 'FALSE'
   OR NOT EXISTS (
       SELECT 1 FROM facturacion WHERE facturacion.afiliada_id = afiliadas.id
   );

-- ====================================================================================
-- 7. POBLAR FACTURACIÓN
-- ====================================================================================
INSERT INTO facturacion (afiliada_id, cuota, periodicidad, forma_pago, iban)
SELECT 
    a.id,
    CAST(REPLACE(NULLIF(s.fee_amount, ''), ',', '.') AS DECIMAL(8, 2)),
    CASE TRIM(LOWER(s.fee_period)) WHEN 'año' THEN 1 WHEN 'mes' THEN 12 ELSE 0 END,
    CASE WHEN UPPER(REGEXP_REPLACE(s.bank_iban, '\s+', '', 'g')) ~ '^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$' THEN 'Domiciliación' ELSE 'Metálico' END,
    CASE WHEN UPPER(REGEXP_REPLACE(s.bank_iban, '\s+', '', 'g')) ~ '^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$' THEN UPPER(REGEXP_REPLACE(s.bank_iban, '\s+', '', 'g')) ELSE NULL END
FROM staging_gravity s
JOIN afiliadas a ON UPPER(TRIM(s.nif_dni)) = UPPER(TRIM(a.cif))
WHERE NOT EXISTS (
    SELECT 1 FROM facturacion f WHERE f.afiliada_id = a.id
);

-- 8. Limpieza final de la tabla de staging
DROP TABLE staging_gravity;