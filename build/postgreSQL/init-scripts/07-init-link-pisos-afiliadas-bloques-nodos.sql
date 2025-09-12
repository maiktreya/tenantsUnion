-- ACTUAL UPDATE STATEMENT
-- This statement will iterate over each 'piso' that doesn't have a 'bloque_id'
-- and will attempt to find a match using the function.
SET search_path TO sindicato_inq, public;

UPDATE pisos
SET
    bloque_id = find_best_match_bloque_id (direccion)
WHERE
    bloque_id IS NULL;

-- 4. SYNC BLOQUES TO NODOS: Ensure all bloques are linked to their nodos
CALL sync_all_bloques_to_nodos ();

-- =====================================================================
-- NEW: LEGACY DATA CONSISTENCY CHECK (APPENDED)
-- =====================================================================
-- This section is designed to identify 'empresas' from the legacy system
-- that were associated with a 'piso' but were not linked to a 'bloque',
-- causing them to be missed during the initial data migration.

-- 1. Re-create the staging table for 'pisos' to access the original 'propiedad' field.
CREATE TABLE IF NOT EXISTS staging_pisos_check (
    direccion TEXT,
    estado TEXT,
    api TEXT,
    propiedad TEXT,
    entramado TEXT,
    num_afiliadas TEXT,
    num_preafiliadas TEXT,
    num_inq_colaboradoras TEXT
);

-- 2. Load the original data from the CSV file again for comparison.
COPY staging_pisos_check
FROM '/csv-data/Pisos.csv'
WITH (
        FORMAT csv,
        DELIMITER ';',
        HEADER true
    );

-- 3. Perform the check: Find properties associated with unlinked pisos
--    that do not exist in the final 'empresas' table.
--    This query will return the names of the missing companies.
SELECT DISTINCT
    spc.propiedad AS empresa_faltante
FROM
    pisos p
    JOIN staging_pisos_check spc ON p.direccion = spc.direccion
WHERE
    p.bloque_id IS NULL -- The piso is not linked to a bloque
    AND spc.propiedad IS NOT NULL -- And it had a 'propiedad' in the original file
    AND spc.propiedad != ''
    AND NOT EXISTS ( -- And that 'propiedad' (company name) does not exist...
        SELECT 1
        FROM empresas e
        WHERE
            e.nombre = spc.propiedad -- ...in the final 'empresas' table.
    );

-- 4. Clean up the temporary staging table.
DROP TABLE staging_pisos_check;