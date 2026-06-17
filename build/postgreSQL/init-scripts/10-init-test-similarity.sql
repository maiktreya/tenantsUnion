SET search_path TO public, sindicato_inq;

-- Start the transaction block FIRST
BEGIN;

WITH best_matches AS (
    -- 1. Identify the best matching bloque for each orphaned piso
    SELECT 
        p.id AS piso_id,
        s.id AS bloque_id,
        s.score
    FROM sindicato_inq.pisos p
    CROSS JOIN LATERAL (
        SELECT 
            b.id,
            public.similarity(
                sindicato_inq.normalize_address_for_match(p.direccion)::text, 
                sindicato_inq.normalize_address_for_match(b.direccion)::text
            ) AS score
        FROM sindicato_inq.bloques b
        WHERE sindicato_inq.normalize_address_for_match(p.direccion)::text OPERATOR(public.%) sindicato_inq.normalize_address_for_match(b.direccion)::text
        ORDER BY 
            sindicato_inq.normalize_address_for_match(p.direccion)::text OPERATOR(public.<->) sindicato_inq.normalize_address_for_match(b.direccion)::text ASC
        LIMIT 1
    ) s
    WHERE p.bloque_id IS NULL             
      AND p.direccion IS NOT NULL 
      AND btrim(p.direccion) <> ''
      AND s.score >= 0.92 
)
-- 2. Apply the update and output the affected rows
UPDATE sindicato_inq.pisos p
SET bloque_id = bm.bloque_id
FROM best_matches bm
WHERE p.id = bm.piso_id
RETURNING 
    p.id AS updated_piso_id, 
    p.bloque_id AS linked_bloque_id, 
    bm.score AS match_score; -- 💡 This will print a table of the matched records to your Docker logs

-- 3. Discard the changes safely
ROLLBACK;