-- This SQL script creates a function to find the best matching 'bloque' for a given 'piso' address.
--
-- PRE-REQUISITE:
-- This function requires the 'pg_trgm' extension for fuzzy string matching. (INSTALLED IN AN EARLIER SCRIPT)
-- If you haven't enabled it yet, run the following command as a superuser on your database:
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
    similarity_threshold REAL := 0.88;
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

-- PROCEDURE TO SYNC BLOQUES TO NODOS BASED ON PISOS' CPs
-- This procedure assigns nodo_id to bloques based on the most common nodo_id among their pisos' CPs
-- It assumes the existence of a mapping table 'nodos_cp_mapping' with columns
CREATE OR REPLACE PROCEDURE sync_all_bloques_to_nodos()
LANGUAGE plpgsql
AS $$
DECLARE
    bloque_record RECORD;
    most_common_nodo_id INTEGER;
BEGIN
    -- Itera sobre cada bloque que no tiene un nodo asignado
    FOR bloque_record IN SELECT id FROM sindicato_inq.bloques WHERE nodo_id IS NULL LOOP
        -- Encuentra el nodo_id más común entre los pisos de este bloque
        SELECT ncm.nodo_id INTO most_common_nodo_id
        FROM sindicato_inq.pisos p
        JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
        WHERE p.bloque_id = bloque_record.id
        GROUP BY ncm.nodo_id
        ORDER BY COUNT(*) DESC
        LIMIT 1;

        -- Si se encontró un nodo común, actualiza el bloque
        IF FOUND AND most_common_nodo_id IS NOT NULL THEN
            UPDATE sindicato_inq.bloques
            SET nodo_id = most_common_nodo_id
            WHERE id = bloque_record.id;
        END IF;
    END LOOP;
END;
$$;


-- TRIGGER TO AUTOMATICALLY SYNC BLOQUES WHEN A PISO IS INSERTED OR UPDATED
-- This trigger updates the nodo_id of the parent bloque whenever a piso's CP is set or changed
-- It uses the mapping table 'nodos_cp_mapping' to find the corresponding nodo_id
CREATE OR REPLACE FUNCTION sync_bloque_nodo()
RETURNS TRIGGER AS $$
BEGIN
    -- Cuando se inserta o actualiza un piso...
    -- Se busca el nodo correspondiente a su CP y se actualiza el bloque padre.
    UPDATE sindicato_inq.bloques
    SET nodo_id = (SELECT nodo_id FROM sindicato_inq.nodos_cp_mapping WHERE cp = NEW.cp)
    WHERE id = NEW.bloque_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- El trigger se activa cada vez que se crea o modifica un piso.
CREATE TRIGGER trigger_sync_bloque_nodo
AFTER INSERT OR UPDATE OF cp ON sindicato_inq.pisos
FOR EACH ROW EXECUTE FUNCTION sync_bloque_nodo();



-- ACTIVATE AUTO-INCREMENT FOR FUTURE RECORDS
-- =====================================================================
-- This is the new section that handles the sequence logic.

DO $$ -- Use a DO block to declare a variable
DECLARE
    max_id_num INTEGER;
BEGIN
    -- 3.1: Find the highest numeric part of the legacy 'num_afiliada'.
    -- We use regexp_replace to strip the non-numeric prefix (like 'A') and cast to integer.
    SELECT
        COALESCE(MAX(CAST(regexp_replace(num_afiliada, '[^0-9]+', '', 'g') AS INTEGER)), 0)
    INTO
        max_id_num
    FROM
        afiliadas;

    -- 3.2: Create the sequence for generating new affiliate numbers.
    CREATE SEQUENCE IF NOT EXISTS sindicato_inq.afiliadas_num_afiliada_seq;

    -- 3.3: "Fast-forward" the sequence to start from the next available number.
    -- The third argument 'true' means the NEXT call to nextval() will return max_id_num + 1.
    PERFORM setval('sindicato_inq.afiliadas_num_afiliada_seq', max_id_num, true);

    -- 3.4: Now that legacy data is in and the sequence is set, apply the DEFAULT
    -- constraint to the 'num_afiliada' column for all future inserts.
    ALTER TABLE sindicato_inq.afiliadas
    ALTER COLUMN num_afiliada SET DEFAULT 'A' || nextval('sindicato_inq.afiliadas_num_afiliada_seq'::regclass);

END $$;