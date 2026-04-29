SELECT
    e.id                                              AS entry_id,
    e.date_created,

    -- ── Personal data ──────────────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '11.3'  THEN m.meta_value END)   AS first_name,
    MAX(CASE WHEN m.meta_key = '11.6'  THEN m.meta_value END)   AS last_name,
    MAX(CASE WHEN m.meta_key = '22'    THEN m.meta_value END)   AS nif_dni,
    MAX(CASE WHEN m.meta_key = '26'    THEN m.meta_value END)   AS birth_date,
    MAX(CASE WHEN m.meta_key = '27'    THEN m.meta_value END)   AS gender,
    MAX(CASE WHEN m.meta_key = '13'    THEN m.meta_value END)   AS phone,
    MAX(CASE WHEN m.meta_key = '14'    THEN m.meta_value END)   AS email,

    -- ── Address ────────────────────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '67'    THEN m.meta_value END)   AS address_full_google,
    MAX(CASE WHEN m.meta_key = '69'    THEN m.meta_value END)   AS address_street,
    MAX(CASE WHEN m.meta_key = '37'    THEN m.meta_value END)   AS address_number,
    MAX(CASE WHEN m.meta_key = '58'    THEN m.meta_value END)   AS address_floor,
    MAX(CASE WHEN m.meta_key = '42'    THEN m.meta_value END)   AS address_door,
    MAX(CASE WHEN m.meta_key = '44'    THEN m.meta_value END)   AS address_city,
    MAX(CASE WHEN m.meta_key = '45'    THEN m.meta_value END)   AS address_postcode,

    -- ── Housing situation ──────────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '34'    THEN m.meta_value END)   AS num_people_in_home,
    MAX(CASE WHEN m.meta_key = '35'    THEN m.meta_value END)   AS tenure_type,
    MAX(CASE WHEN m.meta_key = '56'    THEN m.meta_value END)   AS contract_start_date,
    MAX(CASE WHEN m.meta_key = '47.1'  THEN m.meta_value END)   AS landlord_contact_type,

    -- ── Optional housing fields ────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '41'    THEN m.meta_value END)   AS field_41,
    MAX(CASE WHEN m.meta_key = '46'    THEN m.meta_value END)   AS field_46,
    MAX(CASE WHEN m.meta_key = '48'    THEN m.meta_value END)   AS field_48,
    MAX(CASE WHEN m.meta_key = '49.1'  THEN m.meta_value END)   AS field_49_1,

    -- ── Membership / payment ───────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '1'     THEN m.meta_value END)   AS membership_type,
    
    TRIM(SUBSTRING_INDEX(
        COALESCE(
            MAX(CASE WHEN m.meta_key = '21' THEN m.meta_value END), 
            MAX(CASE WHEN m.meta_key = '55' THEN m.meta_value END), 
            MAX(CASE WHEN m.meta_key = '20' THEN m.meta_value END)
        ), '|', -1
    )) AS fee_amount,

    CASE 
        WHEN MAX(CASE WHEN m.meta_key = '1' THEN m.meta_value END) = 'Cuota Sindical' 
             AND TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '21' THEN m.meta_value END), '|', -1)) = '10' THEN 'mes'
        WHEN MAX(CASE WHEN m.meta_key = '1' THEN m.meta_value END) = 'Cuota de Apoyo' 
             AND TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '20' THEN m.meta_value END), '|', -1)) = '20' THEN 'mes'
        ELSE 'año'
    END AS fee_period,
    
    CASE 
        WHEN MAX(CASE WHEN m.meta_key = '1' THEN m.meta_value END) = 'Cuota Sindical' THEN
            CASE TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '21' THEN m.meta_value END), '|', -1))
                WHEN '10' THEN '10 al mes'
                WHEN '100' THEN '100 al año'
            END
        WHEN MAX(CASE WHEN m.meta_key = '1' THEN m.meta_value END) = 'Cuota Social' THEN
            CASE TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '55' THEN m.meta_value END), '|', -1))
                WHEN '20' THEN '20 al año'
                WHEN '50' THEN '50 al año'
            END
        WHEN MAX(CASE WHEN m.meta_key = '1' THEN m.meta_value END) = 'Cuota de Apoyo' THEN
            CASE TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '20' THEN m.meta_value END), '|', -1))
                WHEN '20' THEN '20 al mes'
                WHEN '200' THEN '200 al año'
            END
    END AS fee_formatted,

    MAX(CASE WHEN m.meta_key = '15'    THEN m.meta_value END)   AS bank_iban

FROM e11fa05ad42a_gf_entry e

INNER JOIN (
    SELECT MAX(e_sub.id) as max_id
    FROM e11fa05ad42a_gf_entry e_sub
    JOIN e11fa05ad42a_gf_entry_meta m_sub ON e_sub.id = m_sub.entry_id
    WHERE m_sub.meta_key = '22'
      -- DYNAMIC DATE FILTER
      AND e_sub.date_created >= DATE_SUB(NOW(), INTERVAL 1 DAY)
    GROUP BY m_sub.meta_value
) latest_entries ON e.id = latest_entries.max_id

LEFT JOIN e11fa05ad42a_gf_entry_meta m
       ON e.id = m.entry_id
          AND m.meta_key NOT IN ('submission_speeds', 'gform_product_info_1_')

-- DYNAMIC DATE FILTER
WHERE e.date_created >= DATE_SUB(NOW(), INTERVAL 1 DAY)

GROUP BY e.id, e.date_created

HAVING bank_iban IS NOT NULL 
   AND TRIM(bank_iban) != ''

ORDER BY e.id DESC;