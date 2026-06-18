SELECT
    e.id                                                              AS entry_id,
    e.date_created,

    -- ── Personal data ──────────────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '1'    THEN m.meta_value END)    AS first_name,
    MAX(CASE WHEN m.meta_key = '3'    THEN m.meta_value END)    AS last_name,
    MAX(CASE WHEN m.meta_key = '5'    THEN m.meta_value END)    AS nif_dni,
    MAX(CASE WHEN m.meta_key = '46'   THEN m.meta_value END)    AS birth_date,
    MAX(CASE WHEN m.meta_key = '42'   THEN m.meta_value END)    AS gender,
    MAX(CASE WHEN m.meta_key = '7'    THEN m.meta_value END)    AS phone,
    MAX(CASE WHEN m.meta_key = '6'    THEN m.meta_value END)    AS email,

    -- ── Address ────────────────────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '13'   THEN m.meta_value END)    AS address_full_google,
    MAX(CASE WHEN m.meta_key = '13'   THEN m.meta_value END)    AS address_street,
    NULL                                                        AS address_number, -- Combined in field 13
    MAX(CASE WHEN m.meta_key = '15'   THEN m.meta_value END)    AS address_floor,
    MAX(CASE WHEN m.meta_key = '14'   THEN m.meta_value END)    AS address_door,
    MAX(CASE WHEN m.meta_key = '16'   THEN m.meta_value END)    AS address_city,
    MAX(CASE WHEN m.meta_key = '19'   THEN m.meta_value END)    AS address_postcode,

    -- ── Housing situation ──────────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '54'   THEN m.meta_value END)    AS num_people_in_home,
    MAX(CASE WHEN m.meta_key = '21'   THEN m.meta_value END)    AS tenure_type,
    MAX(CASE WHEN m.meta_key = '55'   THEN m.meta_value END)    AS contract_start_date,
    MAX(CASE WHEN m.meta_key = '22'   THEN m.meta_value END)    AS landlord_contact_type,

    -- ── Optional housing fields ────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '23'   THEN m.meta_value END)    AS field_41,
    MAX(CASE WHEN m.meta_key = '47'   THEN m.meta_value END)    AS field_46,
    MAX(CASE WHEN m.meta_key = '48'   THEN m.meta_value END)    AS field_48,
    
    -- Modified conditional field (Updated text condition to match new layout)
    CASE 
        WHEN MAX(CASE WHEN m.meta_key = '27.1' THEN m.meta_value END) = 'Mi bloque es todo de la misma propiedad' THEN 'Si'
        ELSE 'No'
    END AS field_49_1,

    -- ── Membership / payment ───────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '50'   THEN m.meta_value END)    AS membership_type,
    
    -- Extracted cleanly from the singular field 53 string
    TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '53' THEN m.meta_value END), '|', -1)) AS fee_amount,

    CASE 
        WHEN MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END) = 'Cuota Sindical' 
             AND TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '53' THEN m.meta_value END), '|', -1)) = '10' THEN 'mes'
        WHEN MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END) = 'Cuota de Apoyo' 
             AND TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '53' THEN m.meta_value END), '|', -1)) = '20' THEN 'mes'
        ELSE 'año'
    END AS fee_period,
    
    CASE 
        WHEN MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END) = 'Cuota Sindical' THEN
            CASE TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '53' THEN m.meta_value END), '|', -1))
                WHEN '10' THEN '10 al mes'
                WHEN '100' THEN '100 al año'
            END
        WHEN MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END) = 'Cuota Social' THEN
            CASE TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '53' THEN m.meta_value END), '|', -1))
                WHEN '20' THEN '20 al año'
                WHEN '50' THEN '50 al año'
            END
        WHEN MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END) = 'Cuota de Apoyo' THEN
            CASE TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '53' THEN m.meta_value END), '|', -1))
                WHEN '20' THEN '20 al mes'
                WHEN '200' THEN '200 al año'
            END
    END AS fee_formatted,

    MAX(CASE WHEN m.meta_key = '30'    THEN m.meta_value END)   AS bank_iban

FROM mod685_gf_entry e

INNER JOIN (
    SELECT MAX(e_sub.id) as max_id
    FROM mod685_gf_entry e_sub
    JOIN mod685_gf_entry_meta m_sub ON e_sub.id = m_sub.entry_id
    WHERE e_sub.form_id = 1 
      AND m_sub.meta_key = '5' -- New NIF/DNI key constraint
      AND e_sub.date_created >= DATE_SUB(NOW(), INTERVAL 30 DAY) -- Switch to '30 DAY' here for back-testing
    GROUP BY m_sub.meta_value
) latest_entries ON e.id = latest_entries.max_id

LEFT JOIN mod685_gf_entry_meta m
       ON e.id = m.entry_id
          AND m.meta_key NOT IN ('submission_speeds', 'gform_product_info_1_')

WHERE e.form_id = 1
  AND e.date_created >= DATE_SUB(NOW(), INTERVAL 30 DAY) -- Switch to '30 DAY' here for back-testing

GROUP BY e.id, e.date_created

ORDER BY e.id DESC;