-- example extraction query from a source wordpress gravity forms database (Mysql/ Mariadb)

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
    NULL                                                        AS address_number, 
    MAX(CASE WHEN m.meta_key = '15'   THEN m.meta_value END)    AS address_floor,   
    MAX(CASE WHEN m.meta_key = '47'   THEN m.meta_value END)    AS address_door,    
    MAX(CASE WHEN m.meta_key = '16'   THEN m.meta_value END)    AS address_city,
    MAX(CASE WHEN m.meta_key = '19'   THEN m.meta_value END)    AS address_postcode,

    -- ── Housing situation ──────────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '54'   THEN m.meta_value END)    AS num_people_in_home,
    MAX(CASE WHEN m.meta_key = '21'   THEN m.meta_value END)    AS tenure_type,
    MAX(CASE WHEN m.meta_key = '55'   THEN m.meta_value END)    AS contract_start_date,
    MAX(CASE WHEN m.meta_key = '22'   THEN m.meta_value END)    AS landlord_contact_type,
    MAX(CASE WHEN m.meta_key = '23'   THEN m.meta_value END)    AS field_41,
    MAX(CASE WHEN m.meta_key = '22'   THEN m.meta_value END)    AS field_46,
    MAX(CASE WHEN m.meta_key = '24'   THEN m.meta_value END)    AS field_48,

    CASE
        WHEN MAX(CASE WHEN m.meta_key = '27.1' THEN m.meta_value END) IS NOT NULL THEN 'Si'
        ELSE 'No'
    END AS field_49_1,

    -- ── Membership / payment ───────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '50'   THEN m.meta_value END)    AS membership_type,

    TRIM(
        SUBSTRING_INDEX(
            CASE MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END)
                WHEN 'Cuota Social'   THEN MAX(CASE WHEN m.meta_key = '53' THEN m.meta_value END)
                WHEN 'Cuota Sindical' THEN MAX(CASE WHEN m.meta_key = '52' THEN m.meta_value END)
                WHEN 'Cuota de Apoyo' THEN MAX(CASE WHEN m.meta_key = '51' THEN m.meta_value END)
            END,
            '|', -1
        )
    ) AS fee_amount,

    CASE
        WHEN MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END) = 'Cuota Sindical'
             AND TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '52' THEN m.meta_value END), '|', -1)) = '10' THEN 'mes'
        WHEN MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END) = 'Cuota de Apoyo'
             AND TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '51' THEN m.meta_value END), '|', -1)) = '20' THEN 'mes'
        ELSE 'año'
    END AS fee_period,

    CASE
        WHEN MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END) = 'Cuota Sindical' THEN
            CASE TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '52' THEN m.meta_value END), '|', -1))
                WHEN '10'  THEN '10 al mes'
                WHEN '100' THEN '100 al año'
            END
        WHEN MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END) = 'Cuota Social' THEN
            CASE TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '53' THEN m.meta_value END), '|', -1))
                WHEN '20' THEN '20 al año'
                WHEN '50' THEN '50 al año'
            END
        WHEN MAX(CASE WHEN m.meta_key = '50' THEN m.meta_value END) = 'Cuota de Apoyo' THEN
            CASE TRIM(SUBSTRING_INDEX(MAX(CASE WHEN m.meta_key = '51' THEN m.meta_value END), '|', -1))
                WHEN '20'  THEN '20 al mes'
                WHEN '200' THEN '200 al año'
            END
    END AS fee_formatted,

    MAX(CASE WHEN m.meta_key = '30'    THEN m.meta_value END)   AS bank_iban

FROM mod685_gf_entry e

-- Dedup optimization
INNER JOIN (
    SELECT MAX(e_sub.id) AS max_id
    FROM mod685_gf_entry e_sub
    JOIN mod685_gf_entry_meta m_sub ON e_sub.id = m_sub.entry_id
    WHERE e_sub.form_id = 1
      AND m_sub.meta_key = '5'
      AND e_sub.date_created >= DATE_SUB(NOW(), INTERVAL 180 DAY)
    GROUP BY m_sub.meta_value
) latest_entries ON e.id = latest_entries.max_id

-- ── REFACTORED CLEANING LAYER (CHAR FUNCTIONS PREVENT HIGHLIGHTER BUGS) ──────
LEFT JOIN (
    SELECT 
        entry_id,
        meta_key,
        REPLACE(REPLACE(REPLACE(meta_value, CHAR(34), CHAR(39)), CHAR(13), ' '), CHAR(10), ' ') AS meta_value
    FROM mod685_gf_entry_meta
    WHERE meta_key NOT IN ('submission_speeds', 'gform_product_info_1_')
) m ON e.id = m.entry_id

WHERE e.form_id = 1
  AND e.date_created >= DATE_SUB(NOW(), INTERVAL 180 DAY)

GROUP BY e.id, e.date_created

ORDER BY e.id DESC;