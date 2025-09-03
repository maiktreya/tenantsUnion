-- 1. Main new schema tables
-- This section defines the target schema. It can be run once to set up the database.
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

-- 2. Clean and Associate Existing Data
-- This section assumes that the 'pisos' and 'bloques' tables have already been populated.
-- The following statements will clean the address data and then link the tables.

-- STEP 2.1: (Optional) Clean the addresses in the 'bloques' table
-- This helps improve matching by removing common, non-essential suffixes like ", España".
-- This can be safely re-run, as it only affects addresses with those suffixes.
UPDATE bloques
SET
    direccion = trim(
        regexp_replace(
            direccion,
            ',\s*(españa|espanya)$',
            '',
            'i'
        )
    )
WHERE
    direccion ~ * ',\s*(españa|espanya)$';

-- STEP 2.2: Associate pisos with their corresponding bloques
-- This UPDATE statement finds the best matching 'bloque' for each 'piso'
-- and populates the 'bloque_id' foreign key.
WITH
    BloqueCandidatos AS (
        -- For each piso, find potential bloques by using a flexible pattern match.
        -- This pattern converts the bloque address into a sequence of keywords separated by wildcards.
        -- e.g., "Calle Sol, 8, Madrid" becomes "%Calle%Sol%8%Madrid%".
        -- This correctly matches a piso address like "Calle Sol, 8, 1ºA, 28013, Madrid".
        SELECT p.id AS piso_id, b.id AS bloque_id,
            -- We rank matches by the length of the original bloque address. The longest,
            -- most specific address gets rank 1.
            ROW_NUMBER() OVER (
                PARTITION BY
                    p.id
                ORDER BY LENGTH(b.direccion) DESC
            ) as rn
        FROM pisos p
            JOIN
            -- The ILIKE is case-insensitive. The regexp_replace function turns spaces and commas
            -- into the '%' SQL wildcard for a flexible match.
            bloques b ON p.direccion ILIKE (
                '%' || regexp_replace(
                    b.direccion, '[\s,]+', '%', 'g'
                ) || '%'
            )
            -- Optional: Use the WHERE clause below to only process pisos that haven't been associated yet.
            -- WHERE p.bloque_id IS NULL
    ),
    MejorCoincidenciaBloque AS (
        -- Select only the best match (rn=1) for each piso.
        SELECT piso_id, bloque_id
        FROM BloqueCandidatos
        WHERE
            rn = 1
    )
UPDATE pisos
SET
    bloque_id = mcb.bloque_id
FROM MejorCoincidenciaBloque mcb
WHERE
    pisos.id = mcb.piso_id;