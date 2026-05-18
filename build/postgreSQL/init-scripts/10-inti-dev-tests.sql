-- =====================================================================
-- SCRIPT: dev_views.sql
-- DESCRIPCIÓN: Vistas avanzadas para auditoría de calidad de datos, 
-- detección de registros huérfanos y validación de titularidad.
-- =====================================================================

SET search_path TO sindicato_inq, public;

-- ---------------------------------------------------------------------
-- 0. LIMPIEZA DE VISTAS OBSOLETAS O PREVIAS
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS sindicato_inq.comprobar_link_pisos_bloques CASCADE;
DROP VIEW IF EXISTS sindicato_inq.v_auditoria_links_pisos_bloques CASCADE;
DROP VIEW IF EXISTS sindicato_inq.v_sugerencias_pisos_huerfanos CASCADE;
DROP VIEW IF EXISTS sindicato_inq.v_bloques_huerfanos CASCADE;

-- ---------------------------------------------------------------------
-- 1. VISTA: v_auditoria_links_pisos_bloques
-- Propósito: Evaluar la calidad de los enlaces actuales entre pisos y bloques,
-- detectando direcciones subóptimas y discrepancias en la titularidad.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW sindicato_inq.v_auditoria_links_pisos_bloques AS
SELECT
    p.id AS piso_id,
    p.direccion AS piso_direccion,
    p.propiedad AS piso_propiedad,
    p.bloque_id AS current_bloque_id,
    b_current.direccion AS current_bloque_direccion,
    e.nombre AS bloque_empresa,
    
    (p.bloque_id IS NOT NULL) AS is_linked,
    
    -- Sugerencia de match por dirección
    s.top_match_bloque_id AS suggested_bloque_id,
    s.top_match_bloque_direccion AS suggested_bloque_direccion,
    s.top_match_score AS suggested_score,
    
    -- Score de la dirección del enlace actual
    CASE 
        WHEN p.bloque_id IS NOT NULL THEN 
            similarity(
                normalize_address_for_match(p.direccion),
                normalize_address_for_match(b_current.direccion)
            )
        ELSE NULL 
    END AS current_link_score,

    -- ALERTA 1: ¿La dirección del enlace actual es mala comparada con la sugerencia?
    (p.bloque_id IS DISTINCT FROM s.top_match_bloque_id AND s.top_match_score >= 0.88) AS alerta_direccion_suboptima,

    -- ALERTA 2: ¿Coincide el propietario del piso con la empresa del bloque?
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
LEFT JOIN sindicato_inq.v_bloque_suggestion_scores s ON p.id = s.piso_id
ORDER BY alerta_direccion_suboptima DESC, estado_titularidad DESC;


-- ---------------------------------------------------------------------
-- 2. VISTA: v_sugerencias_pisos_huerfanos
-- Propósito: Listar exclusivamente los pisos que no tienen bloque asignado
-- y ofrecer la mejor sugerencia de match para enlazarlos rápidamente.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW sindicato_inq.v_sugerencias_pisos_huerfanos AS
SELECT
    p.id AS piso_id,
    p.direccion AS piso_direccion,
    p.municipio AS piso_municipio,
    s.top_match_bloque_id AS suggested_bloque_id,
    s.top_match_bloque_direccion AS suggested_bloque_direccion,
    s.top_match_score AS score
FROM sindicato_inq.pisos p
JOIN sindicato_inq.v_bloque_suggestion_scores s ON p.id = s.piso_id
WHERE p.bloque_id IS NULL
  AND s.top_match_bloque_id IS NOT NULL
ORDER BY s.top_match_score DESC, p.id;


-- ---------------------------------------------------------------------
-- 3. VISTA: v_bloques_huerfanos
-- Propósito: Identificar bloques "fantasma" que ya no tienen ningún 
-- piso asociado, permitiendo su limpieza segura de la base de datos.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW sindicato_inq.v_bloques_huerfanos AS
SELECT
    b.id AS bloque_id,
    b.direccion AS bloque_direccion,
    b.empresa_id,
    e.nombre AS empresa_nombre,
    b.nodo_id,
    n.nombre AS nodo_nombre
FROM sindicato_inq.bloques b
LEFT JOIN sindicato_inq.pisos p ON b.id = p.bloque_id
LEFT JOIN sindicato_inq.empresas e ON b.empresa_id = e.id
LEFT JOIN sindicato_inq.nodos n ON b.nodo_id = n.id
WHERE p.id IS NULL
ORDER BY b.id;