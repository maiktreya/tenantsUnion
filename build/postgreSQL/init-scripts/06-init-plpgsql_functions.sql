-- =====================================================================
-- Business logic initialization script (safe + consistent PL/pgSQL)
-- =====================================================================

SET search_path TO public;

-- Ensure required extensions exist
CREATE EXTENSION IF NOT EXISTS pg_trgm   WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- FUNCTION: normalize_address_for_match
-- =====================================================================

DROP FUNCTION IF EXISTS normalize_address_for_match(TEXT) CASCADE;

CREATE OR REPLACE FUNCTION normalize_address_for_match(address_text TEXT)
RETURNS TEXT
LANGUAGE plpgsql IMMUTABLE
AS $$
DECLARE
    parts TEXT[];
    first_part TEXT;
    token TEXT;
    candidate TEXT;
    cleaned TEXT;
    idx INT;
BEGIN
    IF address_text IS NULL OR btrim(address_text) = '' THEN
        RETURN '';
    END IF;

    parts := regexp_split_to_array(address_text, ',');
    IF array_length(parts, 1) IS NULL OR array_length(parts, 1) = 0 THEN
        cleaned := lower(public.unaccent(btrim(address_text)));
    ELSE
        first_part := lower(public.unaccent(btrim(parts[1])));
        first_part := regexp_replace(first_part, '\s+', ' ', 'g');

        IF first_part ~ '[0-9]' THEN
            candidate := regexp_replace(first_part, '^(.+?\b)(\d+[a-z]?).*$', '\1\2');
            IF candidate IS NOT NULL AND candidate <> '' THEN
                cleaned := candidate;
            ELSE
                cleaned := first_part;
            END IF;
        ELSE
            cleaned := first_part;
            IF array_length(parts, 1) > 1 THEN
                FOR idx IN 2 .. array_length(parts, 1) LOOP
                    token := lower(public.unaccent(btrim(parts[idx])));
                    token := regexp_replace(token, '\s+', ' ', 'g');
                    IF token ~ '^[0-9]+[a-z]?$' THEN
                        cleaned := cleaned || ' ' || token;
                        EXIT;
                    END IF;
                END LOOP;
            END IF;
        END IF;
    END IF;

    cleaned := regexp_replace(cleaned, '\s+', ' ', 'g');
    RETURN cleaned;
END;
$$;

-- =====================================================================
-- FUNCTION: find_best_match_bloque_id
-- =====================================================================

DROP FUNCTION IF EXISTS find_best_match_bloque_id(TEXT) CASCADE;

CREATE OR REPLACE FUNCTION find_best_match_bloque_id(piso_direccion TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    best_match_id INTEGER;
    similarity_threshold REAL := 0.88;
    normalized_piso_address TEXT;
BEGIN
    normalized_piso_address := normalize_address_for_match(piso_direccion);

    SELECT b.id
    INTO best_match_id
    FROM sindicato_inq.bloques b
    WHERE similarity(
              normalize_address_for_match(b.direccion),
              normalized_piso_address
          ) >= similarity_threshold
    ORDER BY similarity(
              normalize_address_for_match(b.direccion),
              normalized_piso_address
          ) DESC
    LIMIT 1;

    RETURN best_match_id;
END;
$$;

-- =====================================================================
-- API SCHEMA + WRAPPER FUNCTION
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS api;

DROP FUNCTION IF EXISTS api.find_best_match_bloque_id(TEXT) CASCADE;

CREATE OR REPLACE FUNCTION api.find_best_match_bloque_id(piso_direccion TEXT)
RETURNS INTEGER
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
    SELECT sindicato_inq.find_best_match_bloque_id(piso_direccion);
$$;

-- =====================================================================
-- VIEW: sindicato_inq.v_bloque_suggestion_scores
-- =====================================================================

DROP VIEW IF EXISTS sindicato_inq.v_bloque_suggestion_scores CASCADE;

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

-- =====================================================================
-- FUNCTION: rpc_get_bloque_suggestions
-- =====================================================================

DROP FUNCTION IF EXISTS rpc_get_bloque_suggestions(JSONB, REAL) CASCADE;

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
                        WHEN value ? 'index'
                             AND (value->>'index') ~ '^[0-9]+$'
                             THEN (value->>'index')::INT
                    END,
                    CASE
                        WHEN value ? 'piso_id'
                             AND (value->>'piso_id') ~ '^[0-9]+$'
                             THEN (value->>'piso_id')::INT
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

-- =====================================================================
-- INDEX: accelerate normalized comparison
-- =====================================================================

DROP INDEX IF EXISTS idx_bloques_normalized_trgm;

CREATE INDEX idx_bloques_normalized_trgm
ON sindicato_inq.bloques
USING gin (normalize_address_for_match(direccion) gin_trgm_ops);

-- =====================================================================
-- FUNCTION + TRIGGER: extract_cp_from_direccion
-- =====================================================================

DROP FUNCTION IF EXISTS extract_cp_from_direccion() CASCADE;

CREATE OR REPLACE FUNCTION extract_cp_from_direccion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    matches TEXT[];
BEGIN
    IF (TG_OP = 'INSERT' OR NEW.direccion IS DISTINCT FROM OLD.direccion) THEN
        matches := regexp_matches(NEW.direccion, '\m([0-9]{5})\M');
        IF array_length(matches, 1) > 0 THEN
            NEW.cp := matches[1]::INTEGER;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trigger_a_extract_cp ON sindicato_inq.pisos;

CREATE TRIGGER trigger_a_extract_cp
BEFORE INSERT OR UPDATE ON sindicato_inq.pisos
FOR EACH ROW EXECUTE FUNCTION extract_cp_from_direccion();

-- =====================================================================
-- SEQUENCE SETUP FOR afiliadas.num_afiliada
-- =====================================================================

DO $$
DECLARE
    max_id_num INTEGER;
BEGIN
    SELECT COALESCE(MAX(CAST(regexp_replace(num_afiliada, '[^0-9]+', '', 'g') AS INTEGER)), 0)
    INTO max_id_num
    FROM sindicato_inq.afiliadas;

    CREATE SEQUENCE IF NOT EXISTS sindicato_inq.afiliadas_num_afiliada_seq;
    PERFORM setval('sindicato_inq.afiliadas_num_afiliada_seq', max_id_num, TRUE);

    ALTER TABLE sindicato_inq.afiliadas
    ALTER COLUMN num_afiliada
    SET DEFAULT 'A' || nextval('sindicato_inq.afiliadas_num_afiliada_seq'::regclass);
END;
$$;

-- =====================================================================
-- PROCEDURE: sync_all_bloques_to_nodos
-- =====================================================================

DROP PROCEDURE IF EXISTS sync_all_bloques_to_nodos() CASCADE;

CREATE OR REPLACE PROCEDURE sync_all_bloques_to_nodos()
LANGUAGE plpgsql
AS $$
DECLARE
    bloque_record RECORD;
    most_common_nodo_id INTEGER;
BEGIN
    FOR bloque_record IN
        SELECT id FROM sindicato_inq.bloques WHERE nodo_id IS NULL
    LOOP
        SELECT ncm.nodo_id INTO most_common_nodo_id
        FROM sindicato_inq.pisos p
        JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
        WHERE p.bloque_id = bloque_record.id
        GROUP BY ncm.nodo_id
        ORDER BY COUNT(*) DESC
        LIMIT 1;

        IF FOUND AND most_common_nodo_id IS NOT NULL THEN
            UPDATE sindicato_inq.bloques
            SET nodo_id = most_common_nodo_id
            WHERE id = bloque_record.id;
        END IF;
    END LOOP;
END;
$$;

-- =====================================================================
-- FUNCTION: sync_bloque_nodo (trigger helper)
-- =====================================================================

DROP FUNCTION IF EXISTS sync_bloque_nodo() CASCADE;

CREATE OR REPLACE FUNCTION sync_bloque_nodo()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE sindicato_inq.bloques
    SET nodo_id = (
        SELECT nodo_id
        FROM sindicato_inq.nodos_cp_mapping
        WHERE cp = NEW.cp
    )
    WHERE id = NEW.bloque_id;

    RETURN NEW;
END;
$$;