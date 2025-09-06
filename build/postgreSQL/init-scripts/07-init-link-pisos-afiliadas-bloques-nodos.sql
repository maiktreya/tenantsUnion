-- Script populating relations between tables with missing links (pisos, bloques, nodos)

-- 1. Preview matches to see how well the function works:
SELECT * FROM preview_address_matches (0.8, 20);

--2. Get all matches for review:
SELECT * FROM match_pisos_to_bloques (0.8);

-- 3. Update the pisos table with matched bloque_id values:
SELECT update_pisos_with_bloque_matches (0.8) as updated_records;

-- 4. SYNC BLOQUES TO NODOS: Ensure all bloques are linked to their nodos
CALL sync_all_bloques_to_nodos ();