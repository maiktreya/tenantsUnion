-- This script is designed to help you evaluate the accuracy of the address matching process

SET search_path TO sindicato_inq, public;

-- This query provides a detailed, row-by-row analysis of the matching results.
-- It includes both linked and unlinked 'pisos' to give a complete picture.

-- After running the update, you can check the results with this query.
-- It will show you how many pisos were successfully linked and how many remain unlinked.
SELECT  * FROM comprobar_link_pisos_bloques LIMIT 10;

-- We use a Common Table Expression (CTE) to first calculate the details
-- for each individual match.
WITH MatchDetails AS (
    SELECT
        p.bloque_id,
        -- Calculate the similarity score for each linked record.
        similarity(
            trim(split_part(b.direccion, ',', 1)) || ', ' || trim(split_part(b.direccion, ',', 2)),
            trim(split_part(p.direccion, ',', 1)) || ', ' || trim(split_part(p.direccion, ',', 2))
        ) AS similarity_score
    FROM
        pisos p
    -- We only need to calculate scores for records that were actually linked.
    JOIN
        bloques b ON p.bloque_id = b.id
)
-- The final SELECT statement aggregates the data into a single summary row.
SELECT
    COUNT(*) AS total_records_in_pisos,
    COUNT(bloque_id) AS linked_records,
    -- Calculate unlinked records by subtracting linked from total.
    (COUNT(*) - COUNT(bloque_id)) AS unlinked_records,
    -- Calculate the percentage of linked records.
    -- We cast to numeric to ensure floating-point division for an accurate percentage.
    ROUND((COUNT(bloque_id)::numeric / COUNT(*)) * 100, 2) AS linkage_percentage,
    -- Calculate the average similarity score across all successful matches from the CTE.
    (SELECT AVG(similarity_score) FROM MatchDetails) AS average_similarity_of_matches
FROM
    pisos;
