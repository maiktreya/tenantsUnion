-- 1. Main new schema tables
-- Note: This script assumes a table named 'empresas' with at least 'id' and 'nombre' columns already exists.
CREATE TABLE bloques (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas (id) ON DELETE SET NULL,
    direccion TEXT UNIQUE,
    estado TEXT,
    api TEXT
);

CREATE TABLE pisos (
    id SERIAL PRIMARY KEY,
    bloque_id INTEGER REFERENCES bloques (id) ON DELETE SET NULL,
    direccion TEXT NOT NULL UNIQUE,
    municipio TEXT,
    cp INTEGER,
    api TEXT,
    prop_vertical BOOLEAN,
    por_habitaciones BOOLEAN
);

CREATE INDEX idx_pisos_bloque_id ON pisos (bloque_id);

-- 2. Define intermediate staging tables
CREATE TABLE staging_bloques (
    direccion TEXT,
    estado TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    col_extra_1 TEXT,
    col_extra_2 TEXT,
    col_extra_3 TEXT
);

CREATE TABLE staging_pisos (
    direccion TEXT,
    estado TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    num_afiliadas TEXT,
    num_preafiliadas TEXT,
    num_inq_colaboradoras TEXT
);

-- 3. Populate the staging tables from CSV files
-- Make sure the CSV files are accessible at the specified path from the PostgreSQL server.
COPY staging_bloques
FROM '/csv-data/Bloques.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

COPY staging_pisos
FROM '/csv-data/Pisos.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

-- 4. Clean and migrate data from staging to final tables

-- STEP 4.1: Clean the addresses in the staging_bloques table
-- This helps avoid duplicate blocks due to minor formatting differences like ", España" vs ", Espanya".
UPDATE staging_bloques
SET
    direccion = trim(
        regexp_replace(
            direccion,
            ',\s*(españa|espanya)$',
            '',
            'i'
        )
    );

-- STEP 4.2: Migrate data to the 'bloques' table
INSERT INTO
    bloques (
        direccion,
        empresa_id,
        estado,
        api
    )
SELECT DISTINCT
    ON (s.direccion) -- Use DISTINCT ON to handle potential duplicates in staging data
    s.direccion,
    e.id,
    s.estado,
    s.api
FROM
    staging_bloques s
    -- Using a LEFT JOIN is safer in case a 'propiedad' doesn't match any 'empresa'
    LEFT JOIN empresas e ON s.propiedad = e.nombre
WHERE
    s.direccion IS NOT NULL
    AND s.direccion <> '' ON CONFLICT (direccion) DO NOTHING;

-- STEP 4.3: Migrate data to the 'pisos' table, finding the best associated 'bloque'
WITH BloqueCandidatos AS (
    -- For each piso, find potential bloques by using a flexible pattern match.
    -- This pattern converts the bloque address into a sequence of keywords separated by wildcards.
    -- e.g., "Calle Sol, 8, Madrid" becomes "%Calle%Sol%8%Madrid%".
    -- This correctly matches a piso address like "Calle Sol, 8, 1ºA, 28013, Madrid".
    SELECT
        p.direccion AS piso_direccion,
        b.id AS bloque_id,
        -- We rank matches by the length of the original bloque address. The longest,
        -- most specific address gets rank 1. This prevents a short, ambiguous
        -- address like "Calle Sol, Madrid" from matching incorrectly if a more
        -- specific "Calle Sol, 8, Madrid" also exists.
        ROW_NUMBER() OVER(PARTITION BY p.direccion ORDER BY LENGTH(b.direccion) DESC) as rn
    FROM
        staging_pisos p
    JOIN
        -- The ILIKE is case-insensitive. The regexp_replace function turns spaces and commas
        -- into the '%' SQL wildcard for a flexible match.
        bloques b ON p.direccion ILIKE ('%' || regexp_replace(b.direccion, '[\s,]+', '%', 'g') || '%')
    WHERE
        p.direccion IS NOT NULL AND p.direccion <> ''
),
MejorCoincidenciaBloque AS (
    -- Select only the best match (rn=1) for each piso.
    SELECT piso_direccion, bloque_id FROM BloqueCandidatos WHERE rn = 1
)
INSERT INTO
    pisos (
        direccion,
        municipio,
        cp,
        api,
        bloque_id,
        prop_vertical,
        por_habitaciones
    )
SELECT
    s.direccion,
    -- Extracts the municipality from the last part of the address string, separated by commas.
    TRIM((string_to_array(s.direccion, ','))[array_upper(string_to_array(s.direccion, ','), 1)]),
    -- Extracts the postal code from the second-to-last part, cleans it of non-digit characters, and casts to integer.
    CAST(NULLIF(regexp_replace((string_to_array(s.direccion, ','))[array_upper(string_to_array(s.direccion, ','), 1) - 1], '\D', '', 'g'), '') AS INTEGER),
    NULLIF(s.api, ''),
    mcb.bloque_id,
    FALSE, -- Default value, as this info is not in the source CSV
    FALSE  -- Default value, as this info is not in the source CSV
FROM
    staging_pisos s
LEFT JOIN
    MejorCoincidenciaBloque mcb ON s.direccion = mcb.piso_direccion
WHERE
    s.direccion IS NOT NULL AND s.direccion <> ''
-- Added conflict handling for safety in case of duplicate piso addresses in the source file.
ON CONFLICT (direccion) DO NOTHING;