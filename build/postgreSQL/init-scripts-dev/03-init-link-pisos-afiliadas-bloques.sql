-- This SQL script uses the 'find_best_match_bloque_id' function to update the
-- 'bloque_id' foreign key in the 'pisos' table.

-- It's recommended to run this on a subset of your data or within a transaction
-- first to ensure the results are as expected.

-- Example of running within a transaction (you can commit or rollback):
-- BEGIN;
--
-- UPDATE pisos
-- SET bloque_id = find_best_match_bloque_id(direccion)
-- WHERE bloque_id IS NULL; -- Only update rows that are not yet linked.
--
-- -- Check the results before committing
-- SELECT id, direccion, bloque_id FROM pisos WHERE bloque_id IS NOT NULL LIMIT 100;
--
-- -- If you are satisfied with the results:
-- -- COMMIT;
-- --
-- -- If you are not satisfied:
-- -- ROLLBACK;


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
