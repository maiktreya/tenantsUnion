-- This query is used to verify the accuracy of the address matching process.
-- It joins the 'pisos' and 'bloques' tables on the newly populated 'bloque_id'
-- and displays the addresses from both tables next to each other for easy comparison.

-- You can run this query after executing the update script to see how well the
-- addresses from 'pisos' have been matched to 'bloques'.

SELECT
    p.id AS piso_id,
    p.direccion AS piso_address,
    b.id AS matched_bloque_id,
    b.direccion AS bloque_address
FROM
    pisos p
-- We use an INNER JOIN to fetch only the pisos that have a matching bloque.
JOIN
    bloques b ON p.bloque_id = b.id
-- Optional: You can filter for specific cases or just limit the results for a quick check.
LIMIT 100; -- Show the first 100 matched pairs for a quick review.



-- This query provides a detailed, row-by-row analysis of the matching results.
-- It includes both linked and unlinked 'pisos' to give a complete picture.

SELECT
    p.id AS piso_id,
    p.direccion AS direccion1,
    p.bloque_id,
    b.direccion AS direccion2,
    -- A boolean column to clearly indicate if a link was successfully made.
    (p.bloque_id IS NOT NULL) AS linked,
    -- Calculate the similarity score between the normalized addresses.
    -- This uses the same logic as the matching function to show the exact score
    -- for the link that was made.
    -- The score will be NULL for unlinked pisos, as there is no 'b.direccion' to compare.
    similarity(
        trim(split_part(b.direccion, ',', 1)) || ', ' || trim(split_part(b.direccion, ',', 2)),
        trim(split_part(p.direccion, ',', 1)) || ', ' || trim(split_part(p.direccion, ',', 2))
    ) AS score
FROM
    pisos p
-- We use a LEFT JOIN to include all records from 'pisos',
-- even if they didn't find a match in the 'bloques' table.
LEFT JOIN
    bloques b ON p.bloque_id = b.id
-- You can order by score to see the best or worst matches first.
-- For example, to see the weakest matches:
-- ORDER BY score ASC;
-- Or to see all the unlinked records first:
ORDER BY linked DESC, score DESC;


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
