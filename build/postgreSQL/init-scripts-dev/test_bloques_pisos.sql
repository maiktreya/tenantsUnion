-- ============================================================================
-- ALGORITHM TO MATCH PISO DETAILED ADDRESSES TO BLOQUE BASE ADDRESSES
-- Pattern: Piso "Calle juan 23, 7ªa, 28030" → Bloque "Calle juan 23, 28030"
-- ============================================================================

-- Step 1: Check current state before starting
SELECT
    'Before matching' as stage,
    COUNT(*) as total_pisos,
    COUNT(bloque_id) as pisos_with_bloque,
    COUNT(*) - COUNT(bloque_id) as pisos_without_bloque
FROM sindicato_inq.pisos;

-- Step 2: Analyze the address patterns to understand the data
SELECT
    'ADDRESS PATTERN ANALYSIS' as analysis_type,
    'PISO ADDRESSES' as address_type,
    direccion,
    LENGTH(direccion) as length,
    -- Count commas to see the pattern
    LENGTH(direccion) - LENGTH(
        REPLACE (direccion, ',', '')
    ) as comma_count
FROM sindicato_inq.pisos
WHERE
    bloque_id IS NULL
ORDER BY comma_count DESC, direccion
LIMIT 20;

SELECT
    'ADDRESS PATTERN ANALYSIS' as analysis_type,
    'BLOQUE ADDRESSES' as address_type,
    direccion,
    LENGTH(direccion) as length,
    LENGTH(direccion) - LENGTH(
        REPLACE (direccion, ',', '')
    ) as comma_count
FROM sindicato_inq.bloques
ORDER BY comma_count DESC, direccion
LIMIT 20;

-- Step 3: Create a function to extract base address from piso address
-- This extracts everything except apartment details (between first and last comma)
CREATE OR REPLACE FUNCTION extract_base_address(full_address TEXT)
RETURNS TEXT AS $$
BEGIN
    -- If there are at least 2 commas, extract first part + last part (skip middle apartment details)
    IF LENGTH(full_address) - LENGTH(REPLACE(full_address, ',', '')) >= 2 THEN
        RETURN TRIM(
            SPLIT_PART(full_address, ',', 1) || ', ' ||
            SPLIT_PART(full_address, ',', LENGTH(full_address) - LENGTH(REPLACE(full_address, ',', '')) + 1)
        );
    -- If there's only 1 comma, it might be "street, postal_code" so return as-is
    ELSIF LENGTH(full_address) - LENGTH(REPLACE(full_address, ',', '')) = 1 THEN
        RETURN TRIM(full_address);
    -- If no commas, return as-is
    ELSE
        RETURN TRIM(full_address);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Step 4: Test the extraction function with sample data
SELECT
    'BASE ADDRESS EXTRACTION TEST' as test_type,
    direccion as original_piso_address,
    extract_base_address (direccion) as extracted_base_address,
    LENGTH(direccion) - LENGTH(
        REPLACE (direccion, ',', '')
    ) as comma_count
FROM sindicato_inq.pisos
WHERE
    bloque_id IS NULL
ORDER BY comma_count DESC
LIMIT 20;

-- Step 5: Preview potential matches using base address extraction
SELECT
    'EXTRACTED ADDRESS MATCHES' as match_type,
    p.id as piso_id,
    p.direccion as piso_full_address,
    extract_base_address (p.direccion) as piso_base_address,
    b.id as bloque_id,
    b.direccion as bloque_address,
    'EXACT_MATCH' as match_level
FROM sindicato_inq.pisos p
    INNER JOIN sindicato_inq.bloques b ON LOWER(
        TRIM(
            extract_base_address (p.direccion)
        )
    ) = LOWER(TRIM(b.direccion))
WHERE
    p.bloque_id IS NULL
UNION ALL
-- Also try with some normalization in case of minor differences
SELECT
    'NORMALIZED ADDRESS MATCHES' as match_type,
    p.id as piso_id,
    p.direccion as piso_full_address,
    extract_base_address (p.direccion) as piso_base_address,
    b.id as bloque_id,
    b.direccion as bloque_address,
    'NORMALIZED_MATCH' as match_level
FROM sindicato_inq.pisos p
    INNER JOIN sindicato_inq.bloques b ON LOWER(
        TRIM(
            REGEXP_REPLACE(
                extract_base_address (p.direccion), '[.,;:\-\s]+', ' ', 'g'
            )
        )
    ) = LOWER(
        TRIM(
            REGEXP_REPLACE(
                b.direccion, '[.,;:\-\s]+', ' ', 'g'
            )
        )
    )
WHERE
    p.bloque_id IS NULL
    AND NOT EXISTS (
        SELECT 1
        FROM sindicato_inq.bloques b2
        WHERE
            LOWER(
                TRIM(
                    extract_base_address (p.direccion)
                )
            ) = LOWER(TRIM(b2.direccion))
    )
ORDER BY match_type, piso_id
LIMIT 50;

-- Step 6: Apply EXACT matches first (base address extraction)
UPDATE sindicato_inq.pisos
SET
    bloque_id = (
        SELECT b.id
        FROM sindicato_inq.bloques b
        WHERE
            LOWER(
                TRIM(
                    extract_base_address (pisos.direccion)
                )
            ) = LOWER(TRIM(b.direccion))
        LIMIT 1
    )
WHERE
    bloque_id IS NULL
    AND EXISTS (
        SELECT 1
        FROM sindicato_inq.bloques b
        WHERE
            LOWER(
                TRIM(
                    extract_base_address (pisos.direccion)
                )
            ) = LOWER(TRIM(b.direccion))
    );

-- Check progress after base address matching
SELECT
    'After base address extraction matching' as stage,
    COUNT(*) as total_pisos,
    COUNT(bloque_id) as pisos_with_bloque,
    COUNT(*) - COUNT(bloque_id) as pisos_without_bloque,
    ROUND(
        100.0 * COUNT(bloque_id) / COUNT(*),
        2
    ) as percentage_matched
FROM sindicato_inq.pisos;

-- Step 7: Apply NORMALIZED matches for remaining pisos
UPDATE sindicato_inq.pisos
SET
    bloque_id = (
        SELECT b.id
        FROM sindicato_inq.bloques b
        WHERE
            LOWER(
                TRIM(
                    REGEXP_REPLACE(
                        extract_base_address (pisos.direccion),
                        '[.,;:\-\s]+',
                        ' ',
                        'g'
                    )
                )
            ) = LOWER(
                TRIM(
                    REGEXP_REPLACE(
                        b.direccion,
                        '[.,;:\-\s]+',
                        ' ',
                        'g'
                    )
                )
            )
        LIMIT 1
    )
WHERE
    bloque_id IS NULL
    AND EXISTS (
        SELECT 1
        FROM sindicato_inq.bloques b
        WHERE
            LOWER(
                TRIM(
                    REGEXP_REPLACE(
                        extract_base_address (pisos.direccion),
                        '[.,;:\-\s]+',
                        ' ',
                        'g'
                    )
                )
            ) = LOWER(
                TRIM(
                    REGEXP_REPLACE(
                        b.direccion,
                        '[.,;:\-\s]+',
                        ' ',
                        'g'
                    )
                )
            )
    );

-- Step 8: Check final progress
SELECT
    'Final results' as stage,
    COUNT(*) as total_pisos,
    COUNT(bloque_id) as pisos_with_bloque,
    COUNT(*) - COUNT(bloque_id) as pisos_without_bloque,
    ROUND(
        100.0 * COUNT(bloque_id) / COUNT(*),
        2
    ) as percentage_matched
FROM sindicato_inq.pisos;

-- Step 9: Review successful matches
SELECT
    'SUCCESSFUL MATCHES SAMPLE' as type,
    p.id as piso_id,
    p.direccion as piso_full_address,
    extract_base_address (p.direccion) as extracted_base,
    b.direccion as matched_bloque_address,
    b.id as bloque_id
FROM sindicato_inq.pisos p
    INNER JOIN sindicato_inq.bloques b ON p.bloque_id = b.id
WHERE
    p.bloque_id IS NOT NULL
ORDER BY p.id
LIMIT 20;

-- Step 10: Analyze remaining unmatched pisos
SELECT
    'UNMATCHED PISOS ANALYSIS' as type,
    p.id as piso_id,
    p.direccion as piso_full_address,
    extract_base_address (p.direccion) as extracted_base_address,
    p.municipio,
    p.cp,
    -- Look for the closest bloque addresses
    (
        SELECT b.direccion
        FROM sindicato_inq.bloques b
        WHERE
            LOWER(b.direccion) LIKE '%' || LOWER(
                SPLIT_PART (
                    TRIM(
                        extract_base_address (p.direccion)
                    ),
                    ' ',
                    1
                )
            ) || '%'
        LIMIT 1
    ) as potential_similar_bloque
FROM sindicato_inq.pisos p
WHERE
    p.bloque_id IS NULL
ORDER BY p.direccion
LIMIT 30;

-- Step 11: Find potential manual matches by looking for shared street names
SELECT
    'POTENTIAL MANUAL MATCHES' as type,
    p.id as piso_id,
    p.direccion as piso_address,
    extract_base_address (p.direccion) as piso_base,
    b.id as bloque_id,
    b.direccion as bloque_address,
    -- Simple similarity indicator
    CASE
        WHEN POSITION(
            LOWER(
                SPLIT_PART (
                    TRIM(
                        extract_base_address (p.direccion)
                    ),
                    ' ',
                    2
                )
            ) IN LOWER(b.direccion)
        ) > 0 THEN 'STREET_NAME_MATCH'
        WHEN POSITION(
            LOWER(
                SPLIT_PART (
                    TRIM(
                        extract_base_address (p.direccion)
                    ),
                    ' ',
                    3
                )
            ) IN LOWER(b.direccion)
        ) > 0 THEN 'STREET_NUMBER_MATCH'
        ELSE 'WEAK_MATCH'
    END as match_strength
FROM sindicato_inq.pisos p
    CROSS JOIN sindicato_inq.bloques b
WHERE
    p.bloque_id IS NULL
    AND LENGTH(
        TRIM(
            extract_base_address (p.direccion)
        )
    ) > 10
    AND (
        -- Look for shared words in the addresses
        LOWER(b.direccion) LIKE '%' || LOWER(
            SPLIT_PART (
                TRIM(
                    extract_base_address (p.direccion)
                ),
                ' ',
                2
            )
        ) || '%'
        OR LOWER(b.direccion) LIKE '%' || LOWER(
            SPLIT_PART (
                TRIM(
                    extract_base_address (p.direccion)
                ),
                ' ',
                3
            )
        ) || '%'
        OR LOWER(
            extract_base_address (p.direccion)
        ) LIKE '%' || LOWER(
            SPLIT_PART (TRIM(b.direccion), ' ', 2)
        ) || '%'
    )
ORDER BY match_strength, p.id, b.id
LIMIT 50;

-- Step 12: Final summary report
SELECT
    'FINAL MATCHING REPORT' as report_section,
    'SUMMARY' as report_type,
    (
        SELECT COUNT(*)
        FROM sindicato_inq.pisos
    ) as total_pisos,
    (
        SELECT COUNT(*)
        FROM sindicato_inq.bloques
    ) as total_bloques,
    (
        SELECT COUNT(*)
        FROM sindicato_inq.pisos
        WHERE
            bloque_id IS NOT NULL
    ) as pisos_matched,
    (
        SELECT COUNT(*)
        FROM sindicato_inq.pisos
        WHERE
            bloque_id IS NULL
    ) as pisos_unmatched,
    (
        SELECT ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE
                        bloque_id IS NOT NULL
                ) / COUNT(*), 2
            )
        FROM sindicato_inq.pisos
    ) as match_percentage;

-- Clean up the temporary function if you want
-- DROP FUNCTION IF EXISTS extract_base_address(TEXT);