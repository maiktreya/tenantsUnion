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
    -- Field 13 = "Dirección completa (calle y número)" - a plain text box,
    -- not a Google-validated/composite address field, but kept under BOTH
    -- original column names since the downstream Postgres load script
    -- splits "address_full_google" on commas to build computed_address -
    -- that column is load-critical even though it duplicates address_street.
    MAX(CASE WHEN m.meta_key = '13'   THEN m.meta_value END)    AS address_full_google,
    MAX(CASE WHEN m.meta_key = '13'   THEN m.meta_value END)    AS address_street,
    NULL                                                        AS address_number, -- no dedicated field exists; number is inline in field 13
    MAX(CASE WHEN m.meta_key = '15'   THEN m.meta_value END)    AS address_floor,   -- "Piso"
    MAX(CASE WHEN m.meta_key = '47'   THEN m.meta_value END)    AS address_door,    -- "Puerta" - corrected from field 14 (Portal)
    MAX(CASE WHEN m.meta_key = '16'   THEN m.meta_value END)    AS address_city,
    MAX(CASE WHEN m.meta_key = '19'   THEN m.meta_value END)    AS address_postcode,

    -- ── Housing situation ──────────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '54'   THEN m.meta_value END)    AS num_people_in_home,
    MAX(CASE WHEN m.meta_key = '21'   THEN m.meta_value END)    AS tenure_type,
    MAX(CASE WHEN m.meta_key = '55'   THEN m.meta_value END)    AS contract_start_date,

    -- landlord_contact_type is not consumed anywhere in the Postgres load
    -- script - kept as-is (field 22, agency name) purely for column-count
    -- compatibility with the existing staging table.
    MAX(CASE WHEN m.meta_key = '22'   THEN m.meta_value END)    AS landlord_contact_type,

    -- field_41 is selected into staging but never referenced in any
    -- INSERT/UPDATE/WHERE downstream - functionally dead for this
    -- pipeline. Kept populated with CIF Agencia (field 23) for audit
    -- purposes only; safe to repoint if that ever changes.
    MAX(CASE WHEN m.meta_key = '23'   THEN m.meta_value END)    AS field_41,

    -- field_46 is consumed by the load script's step 5 as "inmobiliaria"
    -- (agency name) -> must be field 22, NOT field 47 as the old query had it.
    MAX(CASE WHEN m.meta_key = '22'   THEN m.meta_value END)    AS field_46,

    -- field_48 is consumed by the load script's step 4 (populates the
    -- "empresas" table) and step 5 as "propiedad" (landlord/owner name)
    -- -> must be field 24, NOT field 48 ("Escalera") as the old query had it.
    MAX(CASE WHEN m.meta_key = '24'   THEN m.meta_value END)    AS field_48,

    -- field_49_1 = "prop_vertical" in the load script (step 5) - the
    -- checkbox. Presence of a sub-key value means it was checked in GF,
    -- regardless of the exact option text on the live form.
    CASE
        WHEN MAX(CASE WHEN m.meta_key = '27.1' THEN m.meta_value END) IS NOT NULL THEN 'Si'
        ELSE 'No'
    END AS field_49_1,

    -- ── Membership / payment ───────────────────────────────────────────────
    MAX(CASE WHEN m.meta_key = '50'   THEN m.meta_value END)    AS membership_type,

    -- FIX: each membership type stores its fee in a DIFFERENT conditional
    -- field, depending on which option was selected in the GF form:
    --   Cuota Social    -> field 53
    --   Cuota Sindical  -> field 52
    --   Cuota de Apoyo  -> field 51
    -- The previous version only ever read field 53, so Sindical/Apoyo
    -- always came back NULL. We now pick the correct raw field first,
    -- then apply the same "take text after the last |" extraction to it.
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

-- DEDUP BY NIF/DNI: if the same person (same field '5' value) submitted
-- more than once within the window, keep only their latest entry. Scoped
-- to the same 30-day window as the outer query, matching the pattern from
-- the reference query - it does not dedup across the full table history,
-- only among entries already in scope.
INNER JOIN (
    SELECT MAX(e_sub.id) AS max_id
    FROM mod685_gf_entry e_sub
    JOIN mod685_gf_entry_meta m_sub ON e_sub.id = m_sub.entry_id
    WHERE e_sub.form_id = 1
      AND m_sub.meta_key = '5'  -- NIF/DNI
      AND e_sub.date_created >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY m_sub.meta_value
) latest_entries ON e.id = latest_entries.max_id

LEFT JOIN mod685_gf_entry_meta m
       ON e.id = m.entry_id
          AND m.meta_key NOT IN ('submission_speeds', 'gform_product_info_1_')

-- TARGET ONLY MEMBERSHIP FORM & OPEN THE TIMEFRAME
WHERE e.form_id = 1
  AND e.date_created >= DATE_SUB(NOW(), INTERVAL 30 DAY)

GROUP BY e.id, e.date_created

ORDER BY e.id DESC;