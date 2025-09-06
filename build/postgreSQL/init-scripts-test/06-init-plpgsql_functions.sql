-- This SQL script creates a function to find the best matching 'bloque' for a given 'piso' address.
--
-- PRE-REQUISITE:
-- This function requires the 'pg_trgm' extension for fuzzy string matching.
-- If you haven't enabled it yet, run the following command as a superuser on your database:
CREATE EXTENSION IF NOT EXISTS pg_trgm;

SET search_path TO sindicato_inq, public;

-- FUNCTION DEFINITION
-- This function takes a 'direccion' from the 'pisos' table and returns the 'id' of the
-- most similar 'bloque' if the similarity is above a certain threshold (80%).
CREATE OR REPLACE FUNCTION find_best_match_bloque_id(piso_direccion TEXT)
RETURNS INTEGER AS $$
DECLARE
    -- The ID of the best matching 'bloque' to be returned.
    best_match_id INTEGER;
    -- The threshold for a match to be considered valid (0.6 = 80% similarity).
    -- You can adjust this value to be more or less strict.
    similarity_threshold REAL := 0.8;
    -- Variable to hold the normalized address from the 'pisos' table.
    normalized_piso_address TEXT;
BEGIN
    -- STEP 1: Normalize the input address from the 'pisos' table.
    -- We extract the most significant parts: the street name and number.
    -- This is done by splitting the string by the comma and taking the first two parts.
    -- Example: "Avenida Cerro de los Ángeles, 11, Bajo A..." -> "Avenida Cerro de los Ángeles, 11"
    normalized_piso_address := trim(split_part(piso_direccion, ',', 1)) || ', ' || trim(split_part(piso_direccion, ',', 2));

    -- STEP 2: Find the best match in the 'bloques' table.
    -- This query compares the normalized 'piso' address with the normalized version
    -- of every address in the 'bloques' table.
    SELECT
        b.id INTO best_match_id
    FROM
        bloques b
    -- We only consider matches that meet or exceed our similarity threshold.
    WHERE
        similarity(
            -- Normalize the 'bloques.direccion' in the same way.
            trim(split_part(b.direccion, ',', 1)) || ', ' || trim(split_part(b.direccion, ',', 2)),
            normalized_piso_address
        ) >= similarity_threshold
    -- Order the results by similarity score in descending order to find the best match first.
    ORDER BY
        similarity(
            trim(split_part(b.direccion, ',', 1)) || ', ' || trim(split_part(b.direccion, ',', 2)),
            normalized_piso_address
        ) DESC
    -- We only want the top result.
    LIMIT 1;

    -- STEP 3: Return the found ID.
    -- If no match meets the threshold, this will return NULL.
    RETURN best_match_id;
END;
$$ LANGUAGE plpgsql;
