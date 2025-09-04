-- IMPROVED MIGRATION: Match pisos to bloques using similarity scoring
-- SCRIPT TO LINK EXISTING PISOS TO BLOQUES

-- 1. The functions you created are still needed and correct.
-- Ensure these functions exist in your database:
-- normalize_address(TEXT)
-- extract_base_address(TEXT)
-- address_similarity_score(TEXT, TEXT)
SET search_path TO public, sindicato_inq;

-- 2. 🔄 UPDATED SCRIPT: Find the best match and update the pisos table
WITH
    MatchedBloques AS (
        -- This CTE finds the best bloque candidate for each piso that needs matching
        SELECT
            p.direccion AS piso_direccion,
            b.id AS best_bloque_id,
            -- We use ROW_NUMBER to rank the matches by similarity score
            ROW_NUMBER() OVER (
                PARTITION BY
                    p.direccion
                ORDER BY address_similarity_score (p.direccion, b.direccion) DESC, LENGTH(b.direccion) DESC -- Prefer longer, more specific bloque addresses as a tie-breaker
            ) as rn
        FROM pisos p
            CROSS JOIN bloques b
        WHERE
            -- Important: Only process pisos that are not already linked
            p.bloque_id IS NULL
            AND address_similarity_score (p.direccion, b.direccion) >= 0.6 -- Similarity threshold
    )
UPDATE pisos
SET
    bloque_id = mb.best_bloque_id
FROM MatchedBloques mb
WHERE
    -- Join condition to update the correct piso row
    pisos.direccion = mb.piso_direccion
    -- We only want the #1 ranked match for each piso
    AND mb.rn = 1;


-- 3. VERIFICATION QUERY: Check the matching results

SELECT 'MATCHED' as status, COUNT(*) as count
FROM pisos
WHERE
    bloque_id IS NOT NULL
UNION ALL
SELECT 'UNMATCHED (needs linking)' as status, COUNT(*) as count
FROM pisos
WHERE
    bloque_id IS NULL;

-- 4. SYNC BLOQUES TO NODOS: Ensure all bloques are linked to their nodos
CALL sync_all_bloques_to_nodos();