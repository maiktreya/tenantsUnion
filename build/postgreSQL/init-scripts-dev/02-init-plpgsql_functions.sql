-- =====================================================================
-- Business logic initialization script (safe + consistent PL/pgSQL)
-- =====================================================================

SET search_path TO public;

-- Ensure required extensions exist
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;
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
-- SEQUENCE SETUP FOR afiliadas.num_afiliada + trigger to autoincrement
-- =====================================================================

-- 1. Bloque anónimo para inicializar/sincronizar la secuencia de forma segura
DO $$
DECLARE
    max_id_num INTEGER;
BEGIN
    -- Determinar el número correlativo más alto actualmente en la base de datos
    SELECT MAX(CAST(regexp_replace(num_afiliada, '[^0-9]+', '', 'g') AS INTEGER))
    INTO max_id_num
    FROM sindicato_inq.afiliadas;

    -- Crear la secuencia base si no existe en el esquema
    CREATE SEQUENCE IF NOT EXISTS sindicato_inq.afiliadas_num_afiliada_seq;
    
    -- Sincronizar el puntero del contador secuencial de forma dinámica
    IF max_id_num IS NOT NULL THEN
        -- Si la tabla tiene datos, inicializa en el número máximo existente
        PERFORM setval('sindicato_inq.afiliadas_num_afiliada_seq', max_id_num, TRUE);
    ELSE
        -- Si la tabla está vacía, inicializa en 1 listo para el primer llamado
        PERFORM setval('sindicato_inq.afiliadas_num_afiliada_seq', 1, FALSE);
    END IF;

    -- ELIMINACIÓN CRÍTICA: Quitamos el antiguo DEFAULT de la columna. 
    -- Al no existir DEFAULT estructural, PostgreSQL ya no "quemará" números al construir la fila del INSERT.
    ALTER TABLE sindicato_inq.afiliadas ALTER COLUMN num_afiliada DROP DEFAULT;

EXCEPTION
    WHEN undefined_column OR invalid_table_definition THEN
        -- Control de seguridad por si la columna no posee un default previo al desplegar
        NULL;
END;
$$;

-- 2. Definición de la función lógica del Trigger (Evaluación preventiva de Upserts)
CREATE OR REPLACE FUNCTION sindicato_inq.tg_assign_consecutive_num_afiliada()
RETURNS TRIGGER AS $$
BEGIN
    -- CONTROL DE GAPLESS: Verificamos si el CIF del registro entrante ya existe en el sistema.
    -- El chequeo aplica limpieza de espacios y homogeneización de mayúsculas (Case-Insensitive).
    -- Si existe, sabemos que el pipeline derivará en "ON CONFLICT DO UPDATE", por lo que pasamos la fila
    -- de largo SIN tocar ni incrementar la secuencia. El registro conservará su num_afiliada original.
    IF EXISTS (
        SELECT 1 FROM sindicato_inq.afiliadas 
        WHERE UPPER(TRIM(cif)) = UPPER(TRIM(NEW.cif))
    ) THEN
        RETURN NEW;
    END IF;

    -- Si la afiliada es estrictamente nueva y el campo no fue provisto manualmente, asignamos el correlativo
    IF NEW.num_afiliada IS NULL THEN
        NEW.num_afiliada := 'A' || nextval('sindicato_inq.afiliadas_num_afiliada_seq'::regclass);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Vinculación del Trigger a la tabla de Afiliadas (Idempotente)
-- Eliminamos cualquier iteración previa del trigger para asegurar un despliegue limpio
DROP TRIGGER IF EXISTS trg_bi_afiliadas_num_afiliada ON sindicato_inq.afiliadas;

-- Creamos el nuevo disparador en modo BEFORE INSERT para interceptar la fila antes de evaluar exclusiones
CREATE TRIGGER trg_bi_afiliadas_num_afiliada
    BEFORE INSERT ON sindicato_inq.afiliadas
    FOR EACH ROW
    EXECUTE FUNCTION sindicato_inq.tg_assign_consecutive_num_afiliada();

-- ==============================================================================
-- NORMALIZACIÓN DE AFILIADAS (CIF/NIF)
-- ==============================================================================

-- Crear la función interceptora
CREATE OR REPLACE FUNCTION fn_normalize_afiliada_data()
RETURNS TRIGGER AS $$
BEGIN
    -- Si el NIF no es nulo, le quita espacios y lo fuerza a mayúsculas
    IF NEW.cif IS NOT NULL THEN
        NEW.cif := UPPER(TRIM(NEW.cif));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Enganchar la función a la tabla afiliadas
DROP TRIGGER IF EXISTS trg_normalize_afiliada ON afiliadas;
CREATE TRIGGER trg_normalize_afiliada
BEFORE INSERT OR UPDATE ON afiliadas
FOR EACH ROW
EXECUTE FUNCTION fn_normalize_afiliada_data();


-- ==============================================================================
-- NORMALIZACIÓN DE PISOS (MUNICIPIO)
-- ==============================================================================

-- Crear la función interceptora
CREATE OR REPLACE FUNCTION fn_normalize_piso_data()
RETURNS TRIGGER AS $$
BEGIN
    -- Si el municipio no es nulo, aplica capitalización (ej. "mAdRiD" -> "Madrid")
    IF NEW.municipio IS NOT NULL THEN
        NEW.municipio := INITCAP(LOWER(TRIM(NEW.municipio)));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Enganchar la función a la tabla pisos
DROP TRIGGER IF EXISTS trg_normalize_piso ON pisos;
CREATE TRIGGER trg_normalize_piso
BEFORE INSERT OR UPDATE ON pisos
FOR EACH ROW
EXECUTE FUNCTION fn_normalize_piso_data();