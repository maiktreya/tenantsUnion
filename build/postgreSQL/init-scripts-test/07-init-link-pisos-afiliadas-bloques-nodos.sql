-- ACTUAL UPDATE STATEMENT
-- This statement will iterate over each 'piso' that doesn't have a 'bloque_id'
-- and will attempt to find a match using the function.
UPDATE
    pisos
SET
    bloque_id = find_best_match_bloque_id(direccion)
WHERE
    bloque_id IS NULL;

-- After running the update, you can check the results with this query.
-- It will show you how many pisos were successfully linked and how many remain unlinked.
SELECT
  COUNT(CASE WHEN bloque_id IS NOT NULL THEN 1 END) AS linked_pisos,
  COUNT(CASE WHEN bloque_id IS NULL THEN 1 END) AS unlinked_pisos,
  COUNT(*) AS total_pisos
FROM pisos;


-- This query generates a summary report to measure the overall effectiveness
-- and accuracy of the address matching process.

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
