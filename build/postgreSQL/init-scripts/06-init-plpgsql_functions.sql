-- This SQL script creates a function to find the best matching 'bloque' for a given 'piso' address.
--
-- PRE-REQUISITE:
-- This function requires the 'pg_trgm' extension for fuzzy string matching. (INSTALLED IN AN EARLIER SCRIPT)
-- If you haven't enabled it yet, run the following command as a superuser on your database:
SET search_path TO sindicato_inq, public;

-- Normalization helper to keep address comparison consistent with UI logic

CREATE OR REPLACE FUNCTION normalize_address_for_match(address_text TEXT) RETURNS TEXT LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
    parts TEXT[];
    first_part TEXT;
    token TEXT;
    cleaned TEXT;
BEGIN
    IF address_text IS NULL OR btrim(address_text) = '' THEN
        RETURN '';
    END IF;

    parts := regexp_split_to_array(address_text, ',');
    IF array_length(parts, 1) IS NULL OR array_length(parts, 1) = 0 THEN
        cleaned := btrim(address_text);
    ELSE
        first_part := btrim(parts[1]);

        IF first_part ~ '[0-9]' THEN
            cleaned := first_part;
        ELSE
            cleaned := first_part;
            IF array_length(parts, 1) > 1 THEN
                FOR idx IN 2 .. array_length(parts, 1) LOOP
                    token := btrim(parts[idx]);
                    IF token ~ '^[0-9]+[A-Za-z]?$' THEN
                        cleaned := cleaned || ' ' || token;
                        EXIT;
                    END IF;
                END LOOP;
            END IF;
        END IF;
    END IF;

    cleaned := lower(regexp_replace(cleaned, '\s+', ' ', 'g'));
    RETURN cleaned;
END;
$$;

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
    normalized_piso_address := normalize_address_for_match(piso_direccion);

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
            normalize_address_for_match(b.direccion),
            normalized_piso_address
        ) >= similarity_threshold
    -- Order the results by similarity score in descending order to find the best match first.
    ORDER BY
        similarity(
            normalize_address_for_match(b.direccion),
            normalized_piso_address
        ) DESC
    -- We only want the top result.
    LIMIT 1;

    -- STEP 3: Return the found ID.
    -- If no match meets the threshold, this will return NULL.
    RETURN best_match_id;
END;
$$ LANGUAGE plpgsql;

-- API WRAPPER TO EXPOSE THE MATCH FUNCTION VIA POSTGREST
CREATE SCHEMA IF NOT EXISTS api;

CREATE OR REPLACE FUNCTION api.find_best_match_bloque_id(piso_direccion TEXT)
RETURNS INTEGER
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
    SELECT sindicato_inq.find_best_match_bloque_id(piso_direccion);
$$;

-- VIEW TO EXPOSE TOP BLOQUE MATCH PER PISO WITH SCORE DETAILS
CREATE OR REPLACE VIEW sindicato_inq.v_bloque_suggestion_scores AS
WITH normalized_pisos AS (
    SELECT
        p.id AS piso_id,
        p.direccion AS piso_direccion,
        normalize_address_for_match(p.direccion) AS normalized_direccion
    FROM sindicato_inq.pisos p
    WHERE p.direccion IS NOT NULL
      AND btrim(p.direccion) <> ''
      AND normalize_address_for_match(p.direccion) <> ''
),
normalized_bloques AS (
    SELECT
        b.id AS bloque_id,
        b.direccion AS bloque_direccion,
        normalize_address_for_match(b.direccion) AS normalized_direccion
    FROM sindicato_inq.bloques b
    WHERE b.direccion IS NOT NULL
      AND btrim(b.direccion) <> ''
      AND normalize_address_for_match(b.direccion) <> ''
),
scored AS (
    SELECT
        np.piso_id,
        np.piso_direccion,
        nb.bloque_id,
        nb.bloque_direccion,
        similarity(np.normalized_direccion, nb.normalized_direccion) AS score,
        ROW_NUMBER() OVER (
            PARTITION BY np.piso_id
            ORDER BY (np.normalized_direccion <-> nb.normalized_direccion) ASC
        ) AS rn
    FROM normalized_pisos np
    JOIN normalized_bloques nb
        ON (np.normalized_direccion % nb.normalized_direccion)
)
SELECT
    piso_id,
    piso_direccion,
    bloque_id AS top_match_bloque_id,
    bloque_direccion AS top_match_bloque_direccion,
    score AS top_match_score
FROM scored
WHERE rn = 1;

-- FLEXIBLE RPC TO FETCH BLOQUE SUGGESTIONS WITH OPTIONAL PAYLOAD INPUT
CREATE OR REPLACE FUNCTION rpc_get_bloque_suggestions(
    p_addresses JSONB DEFAULT NULL,
    p_score_limit REAL DEFAULT 0.88
)
RETURNS TABLE(
    piso_id INT,
    piso_direccion TEXT,
    suggested_bloque_id INT,
    suggested_bloque_direccion TEXT,
    suggested_score REAL
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = sindicato_inq, public
AS $$
BEGIN
    PERFORM set_limit(p_score_limit);
    IF p_addresses IS NULL THEN
        RETURN QUERY
        SELECT
            v.piso_id,
            v.piso_direccion,
            CASE WHEN v.top_match_score >= p_score_limit THEN v.top_match_bloque_id ELSE NULL END,
            CASE WHEN v.top_match_score >= p_score_limit THEN v.top_match_bloque_direccion ELSE NULL END,
            CASE WHEN v.top_match_score >= p_score_limit THEN v.top_match_score ELSE NULL END
        FROM sindicato_inq.v_bloque_suggestion_scores v
        ORDER BY v.top_match_score DESC NULLS LAST, v.piso_id;
    ELSE
        RETURN QUERY
        WITH input_rows AS (
            SELECT
                COALESCE(
                    CASE
                        WHEN value ? 'index' AND (value->>'index') ~ '^[0-9]+$' THEN (value->>'index')::INT
                    END,
                    CASE
                        WHEN value ? 'piso_id' AND (value->>'piso_id') ~ '^[0-9]+$' THEN (value->>'piso_id')::INT
                    END,
                    (ord::INT - 1)
                ) AS idx,
                NULLIF(btrim(value->>'direccion'), '') AS direccion
            FROM jsonb_array_elements(p_addresses) WITH ORDINALITY AS t(value, ord)
        ),
        normalized_inputs AS (
            SELECT
                idx,
                direccion,
                normalize_address_for_match(direccion) AS normalized
            FROM input_rows
            WHERE direccion IS NOT NULL
              AND normalize_address_for_match(direccion) <> ''
        ),
        normalized_bloques AS (
            SELECT
                b.id,
                b.direccion,
                normalize_address_for_match(b.direccion) AS normalized
            FROM sindicato_inq.bloques b
            WHERE b.direccion IS NOT NULL
              AND btrim(b.direccion) <> ''
              AND normalize_address_for_match(b.direccion) <> ''
        ),
        scored AS (
            SELECT
                ni.idx,
                ni.direccion,
                nb.id AS bloque_id,
                nb.direccion AS bloque_direccion,
                similarity(ni.normalized, nb.normalized) AS score,
                ROW_NUMBER() OVER (
                    PARTITION BY ni.idx
                    ORDER BY (ni.normalized <-> nb.normalized) ASC
                ) AS rn
            FROM normalized_inputs ni
            JOIN normalized_bloques nb
                ON (ni.normalized % nb.normalized)
        ),
        ranked AS (
            SELECT
                idx,
                direccion,
                CASE WHEN score >= p_score_limit THEN bloque_id ELSE NULL END AS suggested_bloque_id,
                CASE WHEN score >= p_score_limit THEN bloque_direccion ELSE NULL END AS suggested_bloque_direccion,
                CASE WHEN score >= p_score_limit THEN score ELSE NULL END AS suggested_score
            FROM scored
            WHERE rn = 1
        )
        SELECT
            ir.idx AS piso_id,
            ir.direccion AS piso_direccion,
            r.suggested_bloque_id,
            r.suggested_bloque_direccion,
            r.suggested_score
        FROM input_rows ir
        LEFT JOIN ranked r ON r.idx = ir.idx
        ORDER BY r.suggested_score DESC NULLS LAST, ir.idx;
    END IF;
END;
$$;

-- Trigram index to accelerate normalized comparison
CREATE INDEX IF NOT EXISTS idx_bloques_normalized_trgm ON sindicato_inq.bloques USING gin (
    normalize_address_for_match(direccion) gin_trgm_ops
);

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

-- =====================================================================
-- NEW: Function and Trigger to auto-populate 'cp' from 'direccion'
-- =====================================================================

-- This function extracts a 5-digit postal code from the 'direccion' string.
CREATE OR REPLACE FUNCTION extract_cp_from_direccion()
RETURNS TRIGGER AS $$
DECLARE
    matches TEXT[];
BEGIN
    -- Only run if 'direccion' is new or has changed.
    IF (TG_OP = 'INSERT' OR NEW.direccion IS DISTINCT FROM OLD.direccion) THEN
        -- Find the first 5-digit number in the direccion string.
        matches := regexp_matches(NEW.direccion, '\m([0-9]{5})\M');
        IF array_length(matches, 1) > 0 THEN
            NEW.cp := matches[1]::INTEGER;
        END IF;
    END IF;
    -- Return the (potentially modified) new row to be inserted/updated.
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- This trigger executes the function BEFORE any insert or update on the 'pisos' table.
-- It runs before 'trigger_sync_bloque_nodo' because BEFORE triggers execute before AFTER triggers.
CREATE TRIGGER trigger_a_extract_cp
BEFORE INSERT OR UPDATE ON sindicato_inq.pisos
FOR EACH ROW EXECUTE FUNCTION extract_cp_from_direccion();




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
