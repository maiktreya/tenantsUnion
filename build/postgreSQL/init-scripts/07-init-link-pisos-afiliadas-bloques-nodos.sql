-- Script populating relations between tables with missing links (pisos, bloques, nodos)

SET search_path TO sindicato_inq;

-- 1. First, enable the pg_trgm extension if not already enabled:
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Preview matches to see how well the function works:
SELECT * FROM preview_address_matches(0.8, 20);

-- 3. Get all matches for review:
SELECT * FROM match_pisos_to_bloques(0.8);

-- 4. Update the pisos table with matched bloque_id values:
SELECT update_pisos_with_bloque_matches(0.8) as updated_records;

-- 5. Check the results:
SELECT 
    p.id, 
    p.direccion as piso_address, 
    b.direccion as bloque_address,
    p.bloque_id
FROM pisos p 
LEFT JOIN bloques b ON p.bloque_id = b.id 
WHERE p.bloque_id IS NOT NULL
LIMIT 20;
*/


-- 6. SYNC BLOQUES TO NODOS: Ensure all bloques are linked to their nodos
CALL sync_all_bloques_to_nodos();