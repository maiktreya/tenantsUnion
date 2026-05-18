SET search_path TO public, sindicato_inq;

-- =================================================================
-- 1. VISTA: v_sugerencias_pisos_huerfanos (ROBUSTA Y CON ÍNDICE)
-- =================================================================
DROP VIEW IF EXISTS sindicato_inq.v_sugerencias_pisos_huerfanos CASCADE;

CREATE OR REPLACE VIEW sindicato_inq.v_sugerencias_pisos_huerfanos AS
SELECT
    p.id AS piso_id,
    p.direccion AS piso_direccion,
    p.municipio AS piso_municipio,
    s.id AS suggested_bloque_id,
    s.direccion AS suggested_bloque_direccion,
    s.score
FROM sindicato_inq.pisos p
CROSS JOIN LATERAL (
    SELECT
        b.id,
        b.direccion,
        similarity(
            sindicato_inq.normalize_address_for_match(p.direccion), 
            sindicato_inq.normalize_address_for_match(b.direccion)
        ) AS score
    FROM sindicato_inq.bloques b
    -- Obligamos a usar el índice GIN pre-filtrando por similitud mínima
    WHERE sindicato_inq.normalize_address_for_match(p.direccion) % sindicato_inq.normalize_address_for_match(b.direccion)
    -- Usamos el operador de distancia trigrámica para ordenar ultrarrápido
    ORDER BY 
        sindicato_inq.normalize_address_for_match(p.direccion) <-> 
        sindicato_inq.normalize_address_for_match(b.direccion) ASC
    LIMIT 1
) s
WHERE p.bloque_id IS NULL 
  AND p.direccion IS NOT NULL 
  AND btrim(p.direccion) <> ''
ORDER BY s.score DESC, p.id;


-- =================================================================
-- 2. VISTA: v_auditoria_links_pisos_bloques (ROBUSTA Y CON ÍNDICE)
-- =================================================================
DROP VIEW IF EXISTS sindicato_inq.v_auditoria_links_pisos_bloques CASCADE;

CREATE OR REPLACE VIEW sindicato_inq.v_auditoria_links_pisos_bloques AS
SELECT
    p.id AS piso_id,
    p.direccion AS piso_direccion,
    p.propiedad AS piso_propiedad,
    p.bloque_id AS current_bloque_id,
    b_current.direccion AS current_bloque_direccion,
    e.nombre AS bloque_empresa,
    
    (p.bloque_id IS NOT NULL) AS is_linked,
    
    s.id AS suggested_bloque_id,
    s.direccion AS suggested_bloque_direccion,
    s.score AS suggested_score,
    
    CASE 
        WHEN p.bloque_id IS NOT NULL AND b_current.id IS NOT NULL THEN 
            similarity(
                sindicato_inq.normalize_address_for_match(p.direccion),
                sindicato_inq.normalize_address_for_match(b_current.direccion)
            )
        ELSE NULL 
    END AS current_link_score,

    (p.bloque_id IS DISTINCT FROM s.id AND s.score >= 0.88) AS alerta_direccion_suboptima,

    CASE
        WHEN p.bloque_id IS NULL THEN 'No enlazado'
        WHEN b_current.empresa_id IS NULL AND p.propiedad IS NOT NULL THEN 'Falta empresa en el Bloque'
        WHEN p.propiedad IS NULL AND b_current.empresa_id IS NOT NULL THEN 'Falta propiedad en el Piso'
        WHEN COALESCE(NULLIF(LOWER(TRIM(p.propiedad)), ''), '') != COALESCE(NULLIF(LOWER(TRIM(e.nombre)), ''), '') THEN 'Inconsistencia de Titularidad'
        ELSE 'OK'
    END AS estado_titularidad

FROM sindicato_inq.pisos p
LEFT JOIN sindicato_inq.bloques b_current ON p.bloque_id = b_current.id
LEFT JOIN sindicato_inq.empresas e ON b_current.empresa_id = e.id
LEFT JOIN LATERAL (
    SELECT
        b.id,
        b.direccion,
        similarity(
            sindicato_inq.normalize_address_for_match(p.direccion), 
            sindicato_inq.normalize_address_for_match(b.direccion)
        ) AS score
    FROM sindicato_inq.bloques b
    WHERE sindicato_inq.normalize_address_for_match(p.direccion) % sindicato_inq.normalize_address_for_match(b.direccion)
    ORDER BY 
        sindicato_inq.normalize_address_for_match(p.direccion) <-> 
        sindicato_inq.normalize_address_for_match(b.direccion) ASC
    LIMIT 1
) s ON p.direccion IS NOT NULL AND btrim(p.direccion) <> ''
ORDER BY alerta_direccion_suboptima DESC, estado_titularidad DESC;