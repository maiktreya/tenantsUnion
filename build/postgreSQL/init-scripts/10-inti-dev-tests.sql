SET search_path TO public, sindicato_inq;

-- =====================================================================
-- VISTA: v_sugerencias_pisos_huerfanos (Filtrado > 0.5 y Tiers de 0.05)
-- =====================================================================
DROP VIEW IF EXISTS sindicato_inq.v_sugerencias_pisos_huerfanos CASCADE;

CREATE OR REPLACE VIEW sindicato_inq.v_sugerencias_pisos_huerfanos AS
SELECT
    p.id AS piso_id,
    p.direccion AS "Dirección Piso",
    p.municipio AS "Municipio",
    s.id AS "ID Bloque Sugerido",
    s.direccion AS "Dirección Bloque Sugerido",
    (ROUND(s.score::numeric * 20) / 20)::numeric(3,2) AS "Score"
FROM sindicato_inq.pisos p
CROSS JOIN LATERAL (
    SELECT
        b.id,
        b.direccion,
        public.similarity(
            sindicato_inq.normalize_address_for_match(p.direccion)::text, 
            sindicato_inq.normalize_address_for_match(b.direccion)::text
        ) AS score
    FROM sindicato_inq.bloques b
    WHERE sindicato_inq.normalize_address_for_match(p.direccion)::text OPERATOR(public.%) sindicato_inq.normalize_address_for_match(b.direccion)::text
    ORDER BY 
        sindicato_inq.normalize_address_for_match(p.direccion)::text OPERATOR(public.<->) sindicato_inq.normalize_address_for_match(b.direccion)::text ASC
    LIMIT 1
) s
WHERE p.bloque_id IS NULL             
  AND p.direccion IS NOT NULL 
  AND btrim(p.direccion) <> ''
  AND s.score > 0.5; -- 💡 Only report records whose match confidence is strictly above 0.5


-- ---------------------------------------------------------------------
-- VISTA: v_consolidar_pisos_bloques (Consolidada y de Alto Rendimiento)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_consolidar_pisos_bloques CASCADE;

CREATE OR REPLACE VIEW v_consolidar_pisos_bloques AS
SELECT
    p.id,
    p.bloque_id,
    b.empresa_id,
    p.prop_vertical AS "Prop. Vertical",
    p.direccion AS "Dirección Piso",
    b.direccion AS "Dirección Bloque",
    p.propiedad AS "Propiedad Piso",
    e.nombre AS "Propiedad Bloque",
    
    -- 1. Métrica de Auditoría: Calidad del enlace actual (Similitud de texto)
    CASE
        WHEN p.bloque_id IS NOT NULL AND b.id IS NOT NULL THEN
            public.similarity(
                sindicato_inq.normalize_address_for_match(p.direccion),
                sindicato_inq.normalize_address_for_match(b.direccion)
            )
        ELSE NULL
    END AS "Score Enlace Actual",

    -- 2. Métrica de Auditoría: Bloque alternativo sugerido por proximidad difusa
    s.id AS "ID Bloque Sugerido",
    s.direccion AS "Dirección Bloque Sugerido",
    s.score AS "Score Sugerido",

    -- 3. Bandera de Alerta: Indica si existe un bloque en el sistema que encaja mucho mejor
    (p.bloque_id IS DISTINCT FROM s.id AND s.score >= 0.88) AS "Alerta Dirección Subóptima",

    -- 4. Matriz combinada de Consistencia de Propiedad (Simplificada y extendida)
    CASE
        WHEN p.bloque_id IS NULL THEN 'No enlazado'
        WHEN b.empresa_id IS NULL AND p.propiedad IS NOT NULL THEN 'Falta empresa Bloque'
        WHEN p.propiedad IS NULL AND b.empresa_id IS NOT NULL THEN 'Falta propiedad Piso'
        WHEN COALESCE(NULLIF(LOWER(TRIM(p.propiedad)), ''), '') = 
             COALESCE(NULLIF(LOWER(TRIM(e.nombre)), ''), '') THEN 'OK'
        ELSE 'Inconsistente'
    END AS "Consistencia Propiedad"

FROM pisos p
    LEFT JOIN bloques b ON p.bloque_id = b.id
    LEFT JOIN empresas e ON b.empresa_id = e.id
    -- Búsqueda lateral indexada de máxima velocidad
    LEFT JOIN LATERAL (
        SELECT
            b_sug.id,
            b_sug.direccion,
            public.similarity(
                sindicato_inq.normalize_address_for_match(p.direccion), 
                sindicato_inq.normalize_address_for_match(b_sug.direccion)
            ) AS score
        FROM bloques b_sug
        WHERE sindicato_inq.normalize_address_for_match(p.direccion) OPERATOR(public.%) sindicato_inq.normalize_address_for_match(b_sug.direccion)
        ORDER BY 
            sindicato_inq.normalize_address_for_match(p.direccion) OPERATOR(public.<->) sindicato_inq.normalize_address_for_match(b_sug.direccion) ASC
        LIMIT 1
    ) s ON p.direccion IS NOT NULL AND btrim(p.direccion) <> '';

CREATE INDEX IF NOT EXISTS bloques_normalized_gist_idx 
ON bloques USING gist (sindicato_inq.normalize_address_for_match(direccion) public.gist_trgm_ops);

CREATE INDEX IF NOT EXISTS pisos_normalized_gist_idx 
ON pisos USING gist (sindicato_inq.normalize_address_for_match(direccion) public.gist_trgm_ops);