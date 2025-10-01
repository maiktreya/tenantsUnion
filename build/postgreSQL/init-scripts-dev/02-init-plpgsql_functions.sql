-- Dev: Fuzzy matching helpers and RPCs for bloque suggestions
SET search_path TO sindicato_inq,
                   public;

-- Ensure trigram extension is available for similarity()

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Dev normalization helper to align with production scoring logic

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
                FOR token IN ARRAY parts[2:array_length(parts, 1)] LOOP
                    token := btrim(token);
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

-- View: top bloque match per piso with score

CREATE OR REPLACE VIEW sindicato_inq.v_bloque_suggestion_scores AS WITH normalized_pisos AS
    (SELECT p.id AS piso_id,
            p.direccion AS piso_direccion,
            normalize_address_for_match(p.direccion) AS normalized_direccion
     FROM sindicato_inq.pisos p
     WHERE p.direccion IS NOT NULL
         AND btrim(p.direccion) <> ''
         AND normalize_address_for_match(p.direccion) <> '' ),
                                                                        normalized_bloques AS
    (SELECT b.id AS bloque_id,
            b.direccion AS bloque_direccion,
            normalize_address_for_match(b.direccion) AS normalized_direccion
     FROM sindicato_inq.bloques b
     WHERE b.direccion IS NOT NULL
         AND btrim(b.direccion) <> ''
         AND normalize_address_for_match(b.direccion) <> '' ),
                                                                        scored AS
    (SELECT np.piso_id,
            np.piso_direccion,
            nb.bloque_id,
            nb.bloque_direccion,
            similarity(np.normalized_direccion, nb.normalized_direccion) AS score,
            ROW_NUMBER() OVER (PARTITION BY np.piso_id
                               ORDER BY (np.normalized_direccion <-> nb.normalized_direccion) ASC) AS rn
     FROM normalized_pisos np
     JOIN normalized_bloques nb ON (np.normalized_direccion % nb.normalized_direccion))
SELECT piso_id,
       piso_direccion,
       bloque_id AS top_match_bloque_id,
       bloque_direccion AS top_match_bloque_direccion,
       score AS top_match_score
FROM scored
WHERE rn = 1;

-- RPC: get bloque suggestions for provided addresses (by index)

CREATE OR REPLACE FUNCTION rpc_get_bloque_suggestions(p_addresses JSONB DEFAULT NULL, p_score_limit REAL DEFAULT 0.88) RETURNS TABLE(piso_id INT, piso_direccion TEXT, suggested_bloque_id INT, suggested_bloque_direccion TEXT, suggested_score REAL) LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = sindicato_inq,
    public AS $$
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

CREATE INDEX IF NOT EXISTS idx_bloques_normalized_trgm ON sindicato_inq.bloques USING gin (normalize_address_for_match(direccion) gin_trgm_ops);