-- Function to calculate similarity between two text strings

-- 1. First, enable the pg_trgm extension if not already enabled:
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Uses a combination of techniques for fuzzy matching
CREATE OR REPLACE FUNCTION calculate_similarity(text1 TEXT, text2 TEXT)
RETURNS FLOAT AS $$
DECLARE
    clean_text1 TEXT;
    clean_text2 TEXT;
    similarity_score FLOAT;
BEGIN
    -- Normalize and clean the text
    clean_text1 := LOWER(TRIM(REGEXP_REPLACE(text1, '\s+', ' ', 'g')));
    clean_text2 := LOWER(TRIM(REGEXP_REPLACE(text2, '\s+', ' ', 'g')));

    -- Remove common variations and standardize
    clean_text1 := REGEXP_REPLACE(clean_text1, ',\s*(españa|espanya|spain)\s*$', '', 'i');
    clean_text2 := REGEXP_REPLACE(clean_text2, ',\s*(españa|espanya|spain)\s*$', '', 'i');

    -- Calculate similarity using PostgreSQL's similarity function
    -- Note: This requires the pg_trgm extension
    similarity_score := SIMILARITY(clean_text1, clean_text2);

    RETURN similarity_score;
END;
$$ LANGUAGE plpgsql;

-- Function to extract base address from piso address
-- Removes apartment-specific details like "Bajo A", "1º B", etc.
CREATE OR REPLACE FUNCTION extract_base_address(direccion_piso TEXT)
RETURNS TEXT AS $$
DECLARE
    base_address TEXT;
BEGIN
    base_address := direccion_piso;

    -- Remove apartment/floor details (common patterns in Spanish addresses)
    base_address := REGEXP_REPLACE(base_address, ',\s*(Bajo|Entresuelo|Principal|[0-9]+º?)\s*[A-Z]?,?', '', 'gi');
    base_address := REGEXP_REPLACE(base_address, ',\s*(Ático|Dúplex|Estudio)\s*[A-Z]?,?', '', 'gi');
    base_address := REGEXP_REPLACE(base_address, ',\s*[A-Z]\s*,?', '', 'g'); -- Single letter apartments

    -- Clean up extra commas and spaces
    base_address := REGEXP_REPLACE(base_address, ',\s*,', ',', 'g');
    base_address := REGEXP_REPLACE(base_address, '\s+', ' ', 'g');
    base_address := TRIM(base_address);

    RETURN base_address;
END;
$$ LANGUAGE plpgsql;

-- Main function to find matching bloques for pisos with 80% similarity threshold
CREATE OR REPLACE FUNCTION match_pisos_to_bloques(similarity_threshold FLOAT DEFAULT 0.8)

RETURNS TABLE(
    piso_id INTEGER,
    piso_direccion TEXT,
    bloque_id INTEGER,
    bloque_direccion TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id AS piso_id,
        p.direccion AS piso_direccion,
        b.id AS bloque_id,
        b.direccion AS bloque_direccion,
        calculate_similarity(extract_base_address(p.direccion), b.direccion) AS similarity_score
    FROM sindicato_inq.pisos p
    CROSS JOIN sindicato_inq.bloques b
    WHERE calculate_similarity(extract_base_address(p.direccion), b.direccion) >= similarity_threshold
    ORDER BY p.id, similarity_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to update pisos table with matched bloque_id
CREATE OR REPLACE FUNCTION update_pisos_with_bloque_matches(similarity_threshold FLOAT DEFAULT 0.8)

RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER := 0;
    match_record RECORD;
BEGIN
    -- First, let's create a temporary table with the best matches
    CREATE TEMP TABLE temp_matches AS
    SELECT DISTINCT ON (piso_id)
        piso_id,
        bloque_id,
        similarity_score
    FROM match_pisos_to_bloques(similarity_threshold)
    ORDER BY piso_id, similarity_score DESC;

    -- Update pisos table with the best matches
    FOR match_record IN
        SELECT piso_id, bloque_id FROM temp_matches
    LOOP
        UPDATE sindicato_inq.pisos
        SET bloque_id = match_record.bloque_id
        WHERE id = match_record.piso_id;

        updated_count := updated_count + 1;
    END LOOP;

    DROP TABLE temp_matches;

    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Utility function to test the matching before applying updates
CREATE OR REPLACE FUNCTION preview_address_matches(similarity_threshold FLOAT DEFAULT 0.8, limit_results INTEGER DEFAULT 50)
RETURNS TABLE(
    piso_id INTEGER,
    original_piso_address TEXT,
    cleaned_piso_address TEXT,
    bloque_id INTEGER,
    bloque_address TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id AS piso_id,
        p.direccion AS original_piso_address,
        extract_base_address(p.direccion) AS cleaned_piso_address,
        b.id AS bloque_id,
        b.direccion AS bloque_address,
        calculate_similarity(extract_base_address(p.direccion), b.direccion) AS similarity_score
    FROM sindicato_inq.pisos p
    CROSS JOIN sindicato_inq.bloques b
    WHERE calculate_similarity(extract_base_address(p.direccion), b.direccion) >= similarity_threshold
    ORDER BY similarity_score DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;




-- 4. PROCEDURE TO SYNC BLOQUES TO NODOS BASED ON PISOS' CPs
-- This procedure assigns nodo_id to bloques based on the most common nodo_id among their pisos' CPs
-- It assumes the existence of a mapping table 'nodos_cp_mapping' with columns
CREATE OR REPLACE PROCEDURE sync_all_bloques_to_nodos()
LANGUAGE plpgsql
AS $$
DECLARE
    bloque_record RECORD;
    most_common_nodo_id INTEGER;
BEGIN
    -- Itera sobre cada bloque que no tiene un nodo asignado
    FOR bloque_record IN SELECT id FROM sindicato_inq.bloques WHERE nodo_id IS NULL LOOP
        -- Encuentra el nodo_id más común entre los pisos de este bloque
        SELECT ncm.nodo_id INTO most_common_nodo_id
        FROM sindicato_inq.pisos p
        JOIN sindicato_inq.nodos_cp_mapping ncm ON p.cp = ncm.cp
        WHERE p.bloque_id = bloque_record.id
        GROUP BY ncm.nodo_id
        ORDER BY COUNT(*) DESC
        LIMIT 1;

        -- Si se encontró un nodo común, actualiza el bloque
        IF FOUND AND most_common_nodo_id IS NOT NULL THEN
            UPDATE sindicato_inq.bloques
            SET nodo_id = most_common_nodo_id
            WHERE id = bloque_record.id;
        END IF;
    END LOOP;
END;
$$;


-- 5. TRIGGER TO AUTOMATICALLY SYNC BLOQUES WHEN A PISO IS INSERTED OR UPDATED
-- This trigger updates the nodo_id of the parent bloque whenever a piso's CP is set or changed
-- It uses the mapping table 'nodos_cp_mapping' to find the corresponding nodo_id
CREATE OR REPLACE FUNCTION sync_bloque_nodo()
RETURNS TRIGGER AS $$
BEGIN
    -- Cuando se inserta o actualiza un piso...
    -- Se busca el nodo correspondiente a su CP y se actualiza el bloque padre.
    UPDATE sindicato_inq.bloques
    SET nodo_id = (SELECT nodo_id FROM sindicato_inq.nodos_cp_mapping WHERE cp = NEW.cp)
    WHERE id = NEW.bloque_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- El trigger se activa cada vez que se crea o modifica un piso.
CREATE TRIGGER trigger_sync_bloque_nodo
AFTER INSERT OR UPDATE OF cp ON sindicato_inq.pisos
FOR EACH ROW EXECUTE FUNCTION sync_bloque_nodo();
