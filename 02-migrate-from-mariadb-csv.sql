-- =====================================================================
-- ARCHIVO 02: MIGRACIÓN DESDE CSV EXPORTADO DE MARIADB
-- =====================================================================
-- Este script importa registros nuevos desde el CSV de exportación de
-- MariaDB hacia la base de datos PostgreSQL existente (sindicato_inq).
--
-- ALINEADO CON: build/niceGUI/services/import_service.py
-- Replica la misma lógica del importador Python del panel de gestión,
-- garantizando que los datos de esta migración masiva sean idénticos en
-- formato y consistencia a los que produce el flujo habitual de la app.
--
-- DISEÑO:
--   1. Staging table para carga bruta del CSV (sin restricciones)
--   2. Columna dir_norm precalculada → evita recalcular regexp en cada paso
--   3. Normalización de CIF/NIE → UPPER + TRIM (igual que el importer)
--   4. Normalización de estado → 'Alta'/'Baja' capitalizados
--      (igual que config.py field_options y import_service.py)
--   5. num_afiliada → generado por la secuencia afiliadas_num_afiliada_seq
--      con prefijo 'A', igual que cualquier registro creado desde la app.
--   6. cp → NO se inserta manualmente; el trigger extract_cp_from_direccion
--      lo extrae automáticamente de la dirección en el INSERT.
--   7. Bloque: se busca el mejor match usando find_best_match_bloque_id()
--      (la misma función PL/pgSQL que usa _ensure_bloque() del importer).
--      Si no hay match fuzzy, se crea un bloque proxy con la dir del piso.
--   8. INSERT ... ON CONFLICT DO NOTHING + WHERE NOT EXISTS en afiliadas
--      → Triple deduplicación igual que el importer.
--   9. Facturación: solo si la afiliada no tiene ya un registro y hay
--      cuota > 0 o IBAN (replica _create_facturacion() del importer).
--  10. Limpieza de la staging table al final.
--
-- ORDEN DE INSERCIÓN (respeta FK):
--   empresas → bloques → pisos [trigger cp] → [UPDATE bloque_id]
--   → afiliadas [sequence num_afiliada] → facturacion
--
-- COLUMNAS DEL CSV (separador: coma, quoted strings):
--   legacy_afiliada_id, cif, nombre, apellidos, genero, email, telefono,
--   estado, fecha_alta, fecha_baja, forma_pago, frequencia_pago, iban,
--   cuota, regimen, fecha_firma, n_personas, direccion_piso, nom_via,
--   numero, cp, propietat_vertical, municipi, piso_inmobiliaria,
--   piso_propiedad
-- =====================================================================

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- PASO 1: CREAR TABLA STAGING
-- =====================================================================
DROP TABLE IF EXISTS staging_mariadb_afiliadas;

CREATE TEMP TABLE staging_mariadb_afiliadas (
    legacy_afiliada_id  TEXT,
    cif                 TEXT,
    nombre              TEXT,
    apellidos           TEXT,
    genero              TEXT,
    email               TEXT,
    telefono            TEXT,
    estado              TEXT,
    fecha_alta          TEXT,
    fecha_baja          TEXT,
    forma_pago          TEXT,
    frequencia_pago     TEXT,
    iban                TEXT,
    cuota               TEXT,
    regimen             TEXT,
    fecha_firma         TEXT,
    n_personas          TEXT,
    direccion_piso      TEXT,
    nom_via             TEXT,
    numero              TEXT,
    cp                  TEXT,   -- del CSV; NO se usa para insertar en pisos
    propietat_vertical  TEXT,
    municipi            TEXT,
    piso_inmobiliaria   TEXT,
    piso_propiedad      TEXT,
    dir_norm            TEXT    -- columna calculada, se rellena en el PASO 2.5
);

-- =====================================================================
-- PASO 2: IMPORTAR CSV
-- =====================================================================
-- Ruta dentro del contenedor db (bind mount: ./dev/back/SI_MAD/db_fork → /csv-data)
-- Coloca el CSV y este script en esa carpeta en el host y ejecuta:
--   docker exec -it <db_container> psql -U $POSTGRES_USER -d $POSTGRES_DB \
--     -f /csv-data/02-migrate-from-mariadb-csv.sql

COPY staging_mariadb_afiliadas (
    legacy_afiliada_id, cif, nombre, apellidos, genero, email, telefono,
    estado, fecha_alta, fecha_baja, forma_pago, frequencia_pago, iban,
    cuota, regimen, fecha_firma, n_personas, direccion_piso, nom_via,
    numero, cp, propietat_vertical, municipi, piso_inmobiliaria, piso_propiedad
)
FROM '/csv-data/mariadb_export.csv'
WITH (
    FORMAT csv,
    DELIMITER ',',
    HEADER true,
    QUOTE '"'
);

-- =====================================================================
-- PASO 2.5: PRECALCULAR DIRECCIÓN NORMALIZADA
-- =====================================================================
-- Se calcula una sola vez y se reutiliza en todos los pasos siguientes.
-- Replica normalize_address_key() de importer_normalization.py:
--   TRIM + colapso de espacios múltiples (unaccent lo hace el motor DB).

UPDATE staging_mariadb_afiliadas
SET dir_norm = regexp_replace(TRIM(direccion_piso), '\s+', ' ', 'g')
WHERE NULLIF(TRIM(direccion_piso), '') IS NOT NULL;

-- =====================================================================
-- PASO 3: INSERTAR EMPRESAS (propietarias de pisos)
-- =====================================================================
-- Sin CIF → WHERE NOT EXISTS para deduplicar sin UNIQUE en nombre.
-- Replica la parte de empresa de _ensure_bloque() del importer.

INSERT INTO empresas (nombre)
SELECT DISTINCT TRIM(piso_propiedad)
FROM staging_mariadb_afiliadas
WHERE NULLIF(TRIM(piso_propiedad), '') IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM empresas e
      WHERE e.nombre = TRIM(piso_propiedad)
  );

-- =====================================================================
-- PASO 4: INSERTAR BLOQUES PROXY
-- =====================================================================
-- El CSV no tiene direcciones de bloque independientes.
-- Igual que _ensure_bloque() del importer:
--   - Si find_best_match_bloque_id() devuelve un ID → no creamos bloque nuevo,
--     el piso se vinculará a ese bloque en el PASO 5b.
--   - Si no hay match fuzzy → creamos un bloque proxy con la dirección
--     normalizada del piso, vinculado a su empresa propietaria.

INSERT INTO bloques (direccion, empresa_id)
SELECT DISTINCT ON (s.dir_norm)
    s.dir_norm  AS direccion,
    e.id        AS empresa_id
FROM staging_mariadb_afiliadas s
LEFT JOIN empresas e ON e.nombre = TRIM(s.piso_propiedad)
WHERE s.dir_norm IS NOT NULL
  -- Solo crear proxy si la función fuzzy no encuentra ningún bloque existente
  AND find_best_match_bloque_id(s.dir_norm) IS NULL
  -- No duplicar si ya existe un bloque con exactamente esa dirección
  AND NOT EXISTS (
      SELECT 1 FROM bloques b WHERE b.direccion = s.dir_norm
  );

-- =====================================================================
-- PASO 5: INSERTAR PISOS
-- =====================================================================
-- cp: OMITIDO intencionalmente → el trigger extract_cp_from_direccion
-- lo extrae del campo 'direccion' automáticamente en cada INSERT,
-- exactamente igual que cuando se crea un piso desde la app.
--
-- bloque_id: se intenta primero fuzzy match con bloques existentes;
-- si no hay match, se usa el bloque proxy creado en el PASO 4.

INSERT INTO pisos (
    bloque_id,
    direccion,
    municipio,
    prop_vertical,
    inmobiliaria,
    propiedad,
    n_personas,
    fecha_firma
)
SELECT DISTINCT ON (s.dir_norm)
    COALESCE(
        find_best_match_bloque_id(s.dir_norm),
        (SELECT b.id FROM bloques b WHERE b.direccion = s.dir_norm LIMIT 1)
    )                                                           AS bloque_id,
    s.dir_norm                                                  AS direccion,
    NULLIF(TRIM(s.municipi), '')                                AS municipio,
    -- Normalización de prop_vertical replicando importer_utils.py
    CASE LOWER(TRIM(s.propietat_vertical))
        WHEN 's'     THEN 's'
        WHEN 'si'    THEN 's'
        WHEN 'sí'    THEN 's'
        WHEN 'yes'   THEN 's'
        WHEN '1'     THEN 's'
        WHEN 'true'  THEN 's'
        WHEN 'n'     THEN 'n'
        WHEN 'no'    THEN 'n'
        WHEN '0'     THEN 'n'
        WHEN 'false' THEN 'n'
        ELSE NULLIF(TRIM(s.propietat_vertical), '')
    END                                                         AS prop_vertical,
    NULLIF(TRIM(s.piso_inmobiliaria), '')                       AS inmobiliaria,
    NULLIF(TRIM(s.piso_propiedad), '')                          AS propiedad,
    CAST(NULLIF(TRIM(s.n_personas), '') AS INTEGER)             AS n_personas,
    CASE
        WHEN NULLIF(TRIM(s.fecha_firma), '') IS NOT NULL
        THEN to_date(LEFT(TRIM(s.fecha_firma), 10), 'YYYY-MM-DD')
        ELSE NULL
    END                                                         AS fecha_firma
FROM staging_mariadb_afiliadas s
WHERE s.dir_norm IS NOT NULL
ON CONFLICT (direccion) DO NOTHING;

-- =====================================================================
-- PASO 5b: VINCULAR PISOS EXISTENTES A SU MEJOR BLOQUE
-- =====================================================================
-- Para pisos que ya existían (ON CONFLICT DO NOTHING los saltó), intentar
-- vincularlos a un bloque si aún están sin vincular.
-- Replica el script 07-init-link-pisos-afiliadas-bloques-nodos.sql.

UPDATE pisos p
SET bloque_id = find_best_match_bloque_id(p.direccion)
WHERE p.bloque_id IS NULL
  AND find_best_match_bloque_id(p.direccion) IS NOT NULL
  AND EXISTS (
      SELECT 1 FROM staging_mariadb_afiliadas s
      WHERE s.dir_norm = p.direccion
  );

-- =====================================================================
-- PASO 6: INSERTAR AFILIADAS
-- =====================================================================
-- Triple deduplicación (igual que el importer):
--   a) WHERE NOT EXISTS por CIF → guarda pre-INSERT
--   b) ON CONFLICT (cif) DO NOTHING → constraint UNIQUE de la tabla
--   c) ON CONFLICT (num_afiliada) DO NOTHING → fallback de secuencia
--
-- num_afiliada: omitido → generado por el DEFAULT de la secuencia
-- 'A' || nextval('afiliadas_num_afiliada_seq') configurado en
-- 06-init-plpgsql_functions.sql. Los nuevos registros seguirán la
-- misma numeración que el resto de afiliadas del sistema.
--
-- estado: 'Alta'/'Baja' capitalizados, igual que config.py field_options.
-- nombre/apellidos: INITCAP para normalizar MAYÚSCULAS del legado.

INSERT INTO afiliadas (
    piso_id,
    nombre,
    apellidos,
    cif,
    genero,
    email,
    telefono,
    estado,
    regimen,
    fecha_alta,
    fecha_baja,
    nivel_participacion,
    afiliacion
)
SELECT
    p.id                                                        AS piso_id,
    INITCAP(TRIM(s.nombre))                                     AS nombre,
    INITCAP(TRIM(s.apellidos))                                  AS apellidos,
    UPPER(TRIM(s.cif))                                          AS cif,
    TRIM(s.genero)                                              AS genero,
    LOWER(TRIM(s.email))                                        AS email,
    TRIM(s.telefono)                                            AS telefono,
    -- Normalizar estado a los valores canónicos de config.py
    CASE LOWER(TRIM(s.estado))
        WHEN 'alta'  THEN 'Alta'
        WHEN 'baixa' THEN 'Baja'   -- legado Catalán del MariaDB
        WHEN 'baja'  THEN 'Baja'
        ELSE INITCAP(TRIM(s.estado))
    END                                                         AS estado,
    NULLIF(TRIM(s.regimen), '')                                 AS regimen,
    CASE
        WHEN NULLIF(TRIM(s.fecha_alta), '') IS NOT NULL
        THEN to_date(LEFT(TRIM(s.fecha_alta), 10), 'YYYY-MM-DD')
        ELSE NULL
    END                                                         AS fecha_alta,
    CASE
        WHEN NULLIF(TRIM(s.fecha_baja), '') IS NOT NULL
        THEN to_date(LEFT(TRIM(s.fecha_baja), 10), 'YYYY-MM-DD')
        ELSE NULL
    END                                                         AS fecha_baja,
    NULL                                                        AS nivel_participacion,
    CASE LOWER(TRIM(s.estado))
        WHEN 'alta' THEN TRUE
        ELSE FALSE
    END                                                         AS afiliacion
FROM staging_mariadb_afiliadas s
LEFT JOIN pisos p ON p.direccion = s.dir_norm
WHERE NOT EXISTS (
    SELECT 1 FROM afiliadas a
    WHERE a.cif = UPPER(TRIM(s.cif))
)
AND NULLIF(TRIM(s.cif), '') IS NOT NULL
ON CONFLICT (cif) DO NOTHING;

-- =====================================================================
-- PASO 7: INSERTAR FACTURACIÓN
-- =====================================================================
-- Replica _create_facturacion() del importer:
--   - Solo si la afiliada aún no tiene registro de facturación
--   - Solo si hay cuota > 0 o IBAN presente (no crear filas vacías)
--   - IBAN validado contra el constraint chk_iban_format (^ES[0-9]{22}$)

INSERT INTO facturacion (
    afiliada_id,
    cuota,
    periodicidad,
    forma_pago,
    iban
)
SELECT
    a.id                                                        AS afiliada_id,
    CAST(
        REPLACE(NULLIF(TRIM(s.cuota), ''), ',', '.')
        AS DECIMAL(8,2)
    )                                                           AS cuota,
    CASE UPPER(TRIM(s.frequencia_pago))
        WHEN 'A'          THEN 12
        WHEN 'ANUAL'      THEN 12
        WHEN 'M'          THEN 1
        WHEN 'MENSUAL'    THEN 1
        WHEN 'T'          THEN 3
        WHEN 'TRIMESTRAL' THEN 3
        ELSE 0
    END                                                         AS periodicidad,
    NULLIF(TRIM(s.forma_pago), '')                              AS forma_pago,
    CASE
        WHEN TRIM(s.iban) ~ '^ES[0-9]{22}$' THEN TRIM(s.iban)
        ELSE NULL
    END                                                         AS iban
FROM staging_mariadb_afiliadas s
JOIN afiliadas a ON a.cif = UPPER(TRIM(s.cif))
WHERE NOT EXISTS (
    SELECT 1 FROM facturacion f WHERE f.afiliada_id = a.id
)
AND NULLIF(TRIM(s.cif), '') IS NOT NULL
-- Solo crear registro si hay algo que facturar
AND (
    NULLIF(TRIM(s.iban), '') IS NOT NULL
    OR CAST(REPLACE(NULLIF(TRIM(s.cuota), ''), ',', '.') AS DECIMAL(8,2)) > 0
);

-- =====================================================================
-- PASO 8: RESUMEN DE LA MIGRACIÓN
-- =====================================================================
-- Descomenta y ejecuta para auditar los resultados.

/*
-- Afiliadas importadas (identificadas por id reciente, no por prefijo):
SELECT COUNT(*) AS nuevas_afiliadas,
       MIN(id) AS primer_id_nuevo,
       MAX(id) AS ultimo_id_nuevo
FROM afiliadas
WHERE fecha_alta >= CURRENT_DATE - INTERVAL '1 day';

-- Tasa de vinculación piso-bloque para los pisos de este CSV:
SELECT
    COUNT(*)                                                    AS total_pisos_csv,
    COUNT(p.bloque_id)                                          AS pisos_con_bloque,
    ROUND(COUNT(p.bloque_id)::numeric / COUNT(*) * 100, 1)     AS pct_vinculados
FROM pisos p
WHERE p.direccion IN (SELECT dir_norm FROM staging_mariadb_afiliadas);

-- Bloques proxy creados (sin empresa asignada):
SELECT COUNT(*) AS bloques_proxy
FROM bloques WHERE empresa_id IS NULL;

-- IBANs descartados por no cumplir el formato ES + 22 dígitos:
SELECT s.cif, s.nombre, s.apellidos, s.iban AS iban_original
FROM staging_mariadb_afiliadas s
WHERE NULLIF(TRIM(s.iban), '') IS NOT NULL
  AND TRIM(s.iban) !~ '^ES[0-9]{22}$';

-- CIFs del CSV que ya existían y fueron omitidos:
SELECT UPPER(TRIM(s.cif)) AS cif_duplicado, s.nombre, s.apellidos
FROM staging_mariadb_afiliadas s
JOIN afiliadas a ON a.cif = UPPER(TRIM(s.cif));
*/

-- =====================================================================
-- PASO 9: LIMPIEZA
-- =====================================================================
DROP TABLE IF EXISTS staging_mariadb_afiliadas;
