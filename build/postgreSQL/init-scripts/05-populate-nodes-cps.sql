-- =====================================================================
-- ARCHIVO 04: POBLACIÓN DE NODOS Y MAPEADO DE CÓDIGOS POSTALES
-- =====================================================================
-- Este script inserta los nodos territoriales del sindicato y asigna
-- los códigos postales correspondientes a cada uno.
-- =====================================================================

SET search_path TO sindicato_inq, public;

-- =====================================================================
-- PARTE 1: INSERCIÓN DE LOS NODOS TERRITORIALES
-- =====================================================================
-- Se insertan los nodos principales. Si ya existen, no se hace nada.

INSERT INTO sindicato_inq.nodos (nombre, descripcion) VALUES
    ('Centro-Arganzuela-Retiro', 'Agrupa los distritos de Centro, Arganzuela, Retiro, Moncloa y Chamberí.'),
    ('Latina', 'Nodo del distrito de Latina.'),
    ('Carabanchel', 'Nodo del distrito de Carabanchel.'),
    ('Usera-Villaverde', 'Agrupa los distritos de Usera y Villaverde.'),
    ('Este', 'Agrupa los distritos del este de Madrid: Salamanca, Chamartín, Ciudad Lineal, Hortaleza, San Blas-Canillejas, Moratalaz, Vicálvaro y Barajas.'),
    ('Sur', 'Agrupa los municipios de la zona sur de la Comunidad de Madrid.'),
    ('Corredor', 'Agrupa los municipios del Corredor del Henares.'),
    ('Sierra Norte', 'Agrupa los municipios de la Sierra Norte.')
ON CONFLICT (nombre) DO NOTHING;

-- =====================================================================
-- PARTE 2: MAPEADO DE CÓDIGOS POSTALES A NODOS
-- =====================================================================
-- Se asocia cada código postal con su nodo correspondiente.

-- Nodo: Centro-Arganzuela-Retiro
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Centro-Arganzuela-Retiro')
FROM (VALUES
    (28004), (28005), (28007), (28008), (28009), (28010),
    (28012), (28013), (28014), (28015), (28045)
) AS data(cp) ON CONFLICT (cp) DO NOTHING;

-- Nodo: Latina
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Latina')
FROM (VALUES (28011), (28024), (28044)) AS data(cp)
ON CONFLICT (cp) DO NOTHING;

-- Nodo: Carabanchel
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Carabanchel')
FROM (VALUES (28047), (28019), (28025)) AS data(cp)
ON CONFLICT (cp) DO NOTHING;

-- Nodo: Usera-Villaverde
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Usera-Villaverde')
FROM (VALUES (28021), (28026), (28041)) AS data(cp)
ON CONFLICT (cp) DO NOTHING;

-- Nodo: Este
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Este')
FROM (VALUES
    (28017), (28022), (28027), (28030), (28032), (28033),
    (28037), (28043), (28052)
) AS data(cp) ON CONFLICT (cp) DO NOTHING;

-- Nodo: Sur
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Sur')
FROM (VALUES
    (28054), (28300), (28312), (28320), (28340), (28341), (28342),
    (28343), (28600), (28609), (28911), (28912), (28913), (28914),
    (28915), (28916), (28917), (28918), (28919), (28921), (28922),
    (28923), (28924), (28925), (28931), (28932), (28933), (28934),
    (28935), (28936), (28937), (28938), (28939), (28941), (28942),
    (28943), (28944), (28945), (28946), (28947), (28950), (28970),
    (28971), (28976), (28977), (28978), (28979), (28980), (28981),
    (28982), (28983), (28984), (28990), (28991)
) AS data(cp) ON CONFLICT (cp) DO NOTHING;

-- Nodo: Corredor
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Corredor')
FROM (VALUES
    (28801), (28802), (28803), (28804), (28805), (28806), (28807),
    (28811), (28812), (28814), (28815), (28816), (28817), (28818),
    (28821), (28822), (28823), (28830), (28850), (28863), (28864),
    (28880), (28890)
) AS data(cp) ON CONFLICT (cp) DO NOTHING;

-- Nodo: Sierra Norte
INSERT INTO sindicato_inq.nodos_cp_mapping (cp, nodo_id)
SELECT cp, (SELECT id FROM sindicato_inq.nodos WHERE nombre = 'Sierra Norte')
FROM (VALUES
    (28180), (28189), (28190), (28191), (28192), (28193), (28194),
    (28195), (28196), (28720), (28721), (28722), (28729), (28730),
    (28737), (28739), (28740), (28742), (28743), (28749), (28751),
    (28752), (28754), (28755), (28756), (28792)
) AS data(cp) ON CONFLICT (cp) DO NOTHING;




-- Populate the 'acciones' table with the predefined values.
INSERT INTO sindicato_inq.acciones (nombre) VALUES
    ('nota simple'),
    ('nota localización propiedades'),
    ('deposito fianza'),
    ('puerta a puerta'),
    ('comunicación enviada'),
    ('llamada'),
    ('acción'),
    ('reunión de negociación'),
    ('informe vulnerabilidad'),
    ('MASC'),
    ('justicia gratuita'),
    ('demanda'),
    ('sentencia')
ON CONFLICT (nombre) DO NOTHING;