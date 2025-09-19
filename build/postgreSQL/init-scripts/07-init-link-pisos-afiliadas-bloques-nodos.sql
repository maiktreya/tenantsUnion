-- =====================================================================
-- A: LOGIC TO LINK PISOS TO BLOQUES AND BLOQUES TO NODOS
-- =====================================================================

-- This statement will iterate over each 'piso' that doesn't have a 'bloque_id'
-- and will attempt to find a match using the function.
SET search_path TO sindicato_inq, public;

-- 1. LINK PISOS TO BLOQUES: Ensure all pisos are linked to their bloques
UPDATE pisos
SET
    bloque_id = find_best_match_bloque_id (direccion)
WHERE
    bloque_id IS NULL;

-- 2. SYNC BLOQUES TO NODOS: Ensure all bloques are linked to their nodos
CALL sync_all_bloques_to_nodos ();

-- =====================================================================
-- B: LOGIC TO CAPTURE AND LINK ORPHANED EMPRESAS (APPENDED)
-- =====================================================================
-- This section identifies, creates, and links empresas from the legacy
-- system that were not associated with a 'bloque'.

-- 1. Re-create the staging table to access the original 'propiedad' field.
CREATE TABLE staging_pisos_check (
    direccion TEXT,
    estado TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    num_afiliadas TEXT,
    num_preafiliadas TEXT,
    num_inq_colaboradoras TEXT,
    prop_vertical TEXT
);
-- 2. Load the original data from the CSV file again for comparison.
COPY staging_pisos_check
FROM '/csv-data/Pisos.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

-- 3. Add a new nullable foreign key column to 'pisos' to hold the link
--    to these orphaned 'empresas'.
ALTER TABLE sindicato_inq.pisos
ADD COLUMN IF NOT EXISTS empresa_nobloque_id INTEGER REFERENCES sindicato_inq.empresas (id) ON DELETE SET NULL;

-- 4. Insert the missing 'empresas' into the main 'empresas' table.
--    This identifies properties from unlinked pisos that don't exist yet.
INSERT INTO
    sindicato_inq.empresas (nombre)
SELECT DISTINCT
    spc.propiedad
FROM
    pisos p
    JOIN staging_pisos_check spc ON p.direccion = spc.direccion
WHERE
    p.bloque_id IS NULL
    AND spc.propiedad IS NOT NULL
    AND spc.propiedad != ''
    AND NOT EXISTS (
        SELECT 1
        FROM empresas e
        WHERE
            e.nombre = spc.propiedad
    );

-- 5. Update the 'pisos' table to link to these newly created 'empresas'.
--    This joins 'pisos' with the staging table and the 'empresas' table
--    to find the correct ID for the new 'empresa_nobloque_id' field.
UPDATE pisos p
SET
    empresa_nobloque_id = e.id
FROM
    staging_pisos_check spc
    JOIN empresas e ON spc.propiedad = e.nombre
WHERE
    p.direccion = spc.direccion
    AND p.bloque_id IS NULL;
-- Only update pisos that are not linked to a bloque.

-- 6. Clean up the temporary staging table.
DROP TABLE staging_pisos_check;