-- ACTUAL UPDATE STATEMENT
-- This statement will iterate over each 'piso' that doesn't have a 'bloque_id'
-- and will attempt to find a match using the function.
SET search_path TO sindicato_inq, public;

UPDATE
    pisos
SET
    bloque_id = find_best_match_bloque_id(direccion)
WHERE
    bloque_id IS NULL;

-- 4. SYNC BLOQUES TO NODOS: Ensure all bloques are linked to their nodos
CALL sync_all_bloques_to_nodos ();