-- ROBUST ADDRESS MATCHING SOLUTION
-- This script provides a comprehensive approach to match pisos to bloques based on address similarity
SET search_path to sindicato_inq;
-- 1. Create a function to normalize addresses for better matching
CREATE OR REPLACE FUNCTION normalize_address(addr TEXT) RETURNS TEXT AS $$
BEGIN
    -- Remove extra spaces, convert to lowercase, remove special characters
    -- Keep only letters, numbers, spaces and commas
    RETURN TRIM(REGEXP_REPLACE(
        REGEXP_REPLACE(LOWER(COALESCE(addr, '')), '[^a-z0-9\s,áéíóúñü]', '', 'g'),
        '\s+', ' ', 'g'
    ));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 2. Create a function to extract the base address (street + number + postal code + city)
CREATE OR REPLACE FUNCTION extract_base_address(addr TEXT) RETURNS TEXT AS $$
DECLARE
    parts TEXT[];
    street_part TEXT;
    postal_code TEXT;
    city_part TEXT;
    result TEXT;
BEGIN
    -- Split by comma and clean parts
    parts := string_to_array(normalize_address(addr), ',');

    -- Extract street part (first part, remove apartment/floor info)
    street_part := TRIM(parts[1]);
    -- Remove apartment/floor indicators like "2B 2", "piso 2F", "bajo C", etc.
    street_part := REGEXP_REPLACE(street_part, '\s+(piso|bajo|portal|escalera)\s+.*$', '', 'i');
    street_part := REGEXP_REPLACE(street_part, '\s+\d+[a-z]?\s*\d*\s*[a-z]?\s*$', '', 'i');
    street_part := REGEXP_REPLACE(street_part, '\s+-?\d+[a-z]?\s*$', '', 'i');

    -- Extract postal code (5 digits)
    postal_code := '';
    FOR i IN 1..array_length(parts, 1) LOOP
        IF parts[i] ~ '^\s*\d{5}\s*$' THEN
            postal_code := TRIM(parts[i]);
            EXIT;
        END IF;
    END LOOP;

    -- Extract city (usually the last non-empty part)
    city_part := '';
    FOR i IN REVERSE array_length(parts, 1)..1 LOOP
        IF TRIM(parts[i]) != '' AND TRIM(parts[i]) != postal_code THEN
            city_part := TRIM(parts[i]);
            EXIT;
        END IF;
    END LOOP;

    -- Combine parts
    result := street_part;
    IF postal_code != '' THEN
        result := result || ', ' || postal_code;
    END IF;
    IF city_part != '' THEN
        result := result || ', ' || city_part;
    END IF;

    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 3. Create a similarity scoring function
CREATE OR REPLACE FUNCTION address_similarity_score(addr1 TEXT, addr2 TEXT) RETURNS NUMERIC AS $$
DECLARE
    base1 TEXT;
    base2 TEXT;
    score NUMERIC := 0;
    parts1 TEXT[];
    parts2 TEXT[];
    common_words INTEGER := 0;
    total_words INTEGER := 0;
BEGIN
    base1 := extract_base_address(addr1);
    base2 := extract_base_address(addr2);

    -- If addresses are very similar, return high score
    IF base1 = base2 THEN
        RETURN 1.0;
    END IF;

    -- Calculate word-based similarity
    parts1 := string_to_array(base1, ' ');
    parts2 := string_to_array(base2, ' ');

    total_words := GREATEST(array_length(parts1, 1), array_length(parts2, 1));

    -- Count common words
    FOR i IN 1..array_length(parts1, 1) LOOP
        FOR j IN 1..array_length(parts2, 1) LOOP
            IF parts1[i] = parts2[j] AND length(parts1[i]) > 2 THEN
                common_words := common_words + 1;
                EXIT;
            END IF;
        END LOOP;
    END LOOP;

    -- Calculate similarity score
    IF total_words > 0 THEN
        score := common_words::NUMERIC / total_words::NUMERIC;
    END IF;

    -- Boost score if postal codes match
    IF base1 ~ '\d{5}' AND base2 ~ '\d{5}' THEN
        IF (SELECT regexp_matches(base1, '(\d{5})'))[1] = (SELECT regexp_matches(base2, '(\d{5})'))[1] THEN
            score := score + 0.3;
        END IF;
    END IF;

    RETURN LEAST(score, 1.0);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 4. IMPROVED MIGRATION: Match pisos to bloques using similarity scoring
-- SCRIPT TO LINK EXISTING PISOS TO BLOQUES

-- 1. (UNCHANGED) The functions you created are still needed and correct.
-- Ensure these functions exist in your database:
-- normalize_address(TEXT)
-- extract_base_address(TEXT)
-- address_similarity_score(TEXT, TEXT)
SET search_path TO public, sindicato_inq;
-- 2. 🔄 UPDATED SCRIPT: Find the best match and update the pisos table
WITH
    MatchedBloques AS (
        -- This CTE finds the best bloque candidate for each piso that needs matching
        SELECT
            p.direccion AS piso_direccion,
            b.id AS best_bloque_id,
            -- We use ROW_NUMBER to rank the matches by similarity score
            ROW_NUMBER() OVER (
                PARTITION BY
                    p.direccion
                ORDER BY address_similarity_score (p.direccion, b.direccion) DESC, LENGTH(b.direccion) DESC -- Prefer longer, more specific bloque addresses as a tie-breaker
            ) as rn
        FROM pisos p
            CROSS JOIN bloques b
        WHERE
            -- Important: Only process pisos that are not already linked
            p.bloque_id IS NULL
            AND address_similarity_score (p.direccion, b.direccion) >= 0.6 -- Similarity threshold
    )
UPDATE pisos
SET
    bloque_id = mb.best_bloque_id
FROM MatchedBloques mb
WHERE
    -- Join condition to update the correct piso row
    pisos.direccion = mb.piso_direccion
    -- We only want the #1 ranked match for each piso
    AND mb.rn = 1;


-- 5. VERIFICATION QUERY: Check the matching results

-- SELECT 'MATCHED' as status, COUNT(*) as count
-- FROM pisos
-- WHERE
--     bloque_id IS NOT NULL
-- UNION ALL
-- SELECT 'UNMATCHED (needs linking)' as status, COUNT(*) as count
-- FROM pisos
-- WHERE
--     bloque_id IS NULL;