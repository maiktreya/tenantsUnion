-- This script is designed to help you evaluate the accuracy of the data linking processes.

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- PART 1: ACCURACY OF PISO-TO-BLOQUE LINKING
-- =====================================================================
-- This query provides a detailed, row-by-row analysis of the address matching results.
SELECT * FROM comprobar_link_pisos_bloques LIMIT 10;

-- This query aggregates the piso-to-bloque matching data into a single summary row.
WITH
    MatchDetails AS (
        SELECT p.bloque_id, similarity (
                trim(
                    split_part(b.direccion, ',', 1)
                ) || ', ' || trim(
                    split_part(b.direccion, ',', 2)
                ), trim(
                    split_part(p.direccion, ',', 1)
                ) || ', ' || trim(
                    split_part(p.direccion, ',', 2)
                )
            ) AS similarity_score
        FROM pisos p
            JOIN bloques b ON p.bloque_id = b.id
    )
SELECT
    'Piso-to-Bloque Linking' AS process,
    COUNT(*) AS total_records_in_pisos,
    COUNT(bloque_id) AS linked_records,
    (COUNT(*) - COUNT(bloque_id)) AS unlinked_records,
    ROUND(
        (
            COUNT(bloque_id)::numeric / COUNT(*)
        ) * 100,
        2
    ) AS linkage_percentage,
    (
        SELECT AVG(similarity_score)
        FROM MatchDetails
    ) AS average_similarity_of_matches
FROM pisos;

-- =====================================================================
-- PART 2: SUMMARY OF ORPHANED EMPRESA CAPTURE
-- =====================================================================
-- This query measures the effectiveness of the process that captures
-- empresas from pisos that were not linked to a bloque.

SELECT
    'Orphaned Empresa Linking' AS process,
    (
        SELECT COUNT(*)
        FROM pisos
        WHERE
            bloque_id IS NULL
    ) AS total_unlinked_pisos,
    COUNT(empresa_nobloque_id) AS pisos_linked_to_orphaned_empresa,
    (
        (
            SELECT COUNT(*)
            FROM pisos
            WHERE
                bloque_id IS NULL
        ) - COUNT(empresa_nobloque_id)
    ) AS pisos_with_no_empresa_link,
    ROUND(
        (
            COUNT(empresa_nobloque_id)::numeric / GREATEST(
                (
                    SELECT COUNT(*)
                    FROM pisos
                    WHERE
                        bloque_id IS NULL
                ),
                1
            )
        ) * 100,
        2
    ) AS capture_percentage
FROM pisos
WHERE
    bloque_id IS NULL;

# drop temporal column for matching missing records
ALTER TABLE sindicato_inq.pisos DROP COLUMN empresa_nobloque_id;
