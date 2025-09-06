-- Script populating relations between tables with missing links (pisos, bloques, nodos)

-- 1. Preview matches to see how well the function works:
SELECT * FROM preview_address_matches (0.6, 20);

--2. Get all matches for review:
SELECT * FROM match_pisos_to_bloques (0.6);

-- 3. Update the pisos table with matched bloque_id values:
SELECT update_pisos_with_bloque_matches (0.6) as updated_records;

-- 4. Check the results:
SELECT
    p.id,
    p.direccion as piso_address,
    b.direccion as bloque_address,
    p.bloque_id
FROM sindicato_inq.pisos p
    LEFT JOIN sindicato_inq.bloques b ON p.bloque_id = b.id
WHERE
    p.bloque_id IS NOT NULL
LIMIT 20;

-- 5. SYNC BLOQUES TO NODOS: Ensure all bloques are linked to their nodos
CALL sync_all_bloques_to_nodos ();