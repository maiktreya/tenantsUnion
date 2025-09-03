-- ROBUST ADDRESS MATCHING SOLUTION
-- This script provides a comprehensive approach to match pisos to bloques based on address similarity

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
WITH BloqueCandidatos AS (
    SELECT
        p.direccion AS piso_direccion,
        b.id AS bloque_id,
        b.direccion AS bloque_direccion,
        address_similarity_score(p.direccion, b.direccion) as similarity_score,
        ROW_NUMBER() OVER(
            PARTITION BY p.direccion
            ORDER BY address_similarity_score(p.direccion, b.direccion) DESC,
                     LENGTH(b.direccion) DESC
        ) as rn
    FROM
        staging_pisos p
    CROSS JOIN
        bloques b
    WHERE
        p.direccion IS NOT NULL AND p.direccion != ''
        AND b.direccion IS NOT NULL AND b.direccion != ''
        -- Only consider candidates with reasonable similarity
        AND address_similarity_score(p.direccion, b.direccion) >= 0.6
),
MejorCoincidenciaBloque AS (
    -- Select only the best match for each piso
    SELECT
        piso_direccion,
        bloque_id,
        bloque_direccion,
        similarity_score
    FROM BloqueCandidatos
    WHERE rn = 1
)
INSERT INTO
    pisos (
        direccion,
        municipio,
        cp,
        api,
        bloque_id,
        prop_vertical,
        por_habitaciones
    )
SELECT
    s.direccion,
    -- Extract municipality from address
    TRIM((string_to_array(s.direccion, ','))[array_upper(string_to_array(s.direccion, ','), 1)]),
    -- Extract postal code
    CAST(
        NULLIF(
            regexp_replace(
                (string_to_array(s.direccion, ','))[array_upper(string_to_array(s.direccion, ','), 1) - 1],
                '\D', '', 'g'
            ),
            ''
        ) AS INTEGER
    ),
    NULLIF(s.api, ''),
    mcb.bloque_id,
    FALSE, -- Default value
    FALSE  -- Default value
FROM
    staging_pisos s
LEFT JOIN
    MejorCoincidenciaBloque mcb ON s.direccion = mcb.piso_direccion
WHERE
    s.direccion IS NOT NULL AND s.direccion != '';

-- 5. VERIFICATION QUERY: Check the matching results
SELECT 'MATCHED' as status, COUNT(*) as count
FROM pisos
WHERE
    bloque_id IS NOT NULL
UNION ALL
SELECT 'UNMATCHED' as status, COUNT(*) as count
FROM pisos
WHERE
    bloque_id IS NULL;

-- 6. DETAILED MATCHING REPORT: See what matches were found
WITH
    MatchingReport AS (
        SELECT
            p.direccion as piso_direccion,
            b.direccion as bloque_direccion,
            address_similarity_score (sp.direccion, b.direccion) as similarity_score
        FROM
            pisos p
            LEFT JOIN bloques b ON p.bloque_id = b.id
            LEFT JOIN staging_pisos sp ON p.direccion = sp.direccion
        WHERE
            p.bloque_id IS NOT NULL
    )
SELECT
    similarity_score,
    COUNT(*) as matches,
    AVG(length(piso_direccion)) as avg_piso_addr_length,
    AVG(length(bloque_direccion)) as avg_bloque_addr_length
FROM MatchingReport
GROUP BY
    similarity_score
ORDER BY similarity_score DESC
LIMIT 10;

-- 7. SAMPLE MATCHES: Show examples of successful matches
SELECT
    p.direccion as piso_address,
    b.direccion as bloque_address,
    extract_base_address (p.direccion) as piso_base,
    extract_base_address (b.direccion) as bloque_base,
    address_similarity_score (p.direccion, b.direccion) as score
FROM pisos p
    JOIN bloques b ON p.bloque_id = b.id
ORDER BY address_similarity_score (p.direccion, b.direccion) DESC
LIMIT 10;

-- 8. TROUBLESHOOTING: Show unmatched pisos and potential candidates
WITH
    UnmatchedPisos AS (
        SELECT direccion
        FROM pisos
        WHERE
            bloque_id IS NULL
        LIMIT 5
    ),
    PotentialMatches AS (
        SELECT
            up.direccion as piso_addr,
            b.direccion as bloque_addr,
            address_similarity_score (up.direccion, b.direccion) as score
        FROM UnmatchedPisos up
            CROSS JOIN bloques b
        WHERE
            address_similarity_score (up.direccion, b.direccion) > 0.3
    )
SELECT
    piso_addr,
    bloque_addr,
    score,
    extract_base_address (piso_addr) as piso_base,
    extract_base_address (bloque_addr) as bloque_base
FROM PotentialMatches
ORDER BY piso_addr, score DESC;