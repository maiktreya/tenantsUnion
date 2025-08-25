-- =====================================================================
-- PARTE A: SOLUCIÓN HÍBRIDA PARA LA INTEGRACIÓN DE NODOS
-- =====================================================================
SET search_path TO sindicato_inq, public;

-- 1. Se mantienen la tabla 'nodos' y la tabla de mapeo como fuente de la verdad.

DROP TABLE IF EXISTS sindicato_inq.nodos;
DROP TABLE IF EXISTS sindicato_inq.nodos_cp_mapping;

CREATE TABLE sindicato_inq.nodos (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE sindicato_inq.nodos_cp_mapping (
    cp INTEGER PRIMARY KEY,
    nodo_id INTEGER REFERENCES nodos (id) ON DELETE CASCADE NOT NULL
);

CREATE INDEX idx_nodos_cp_mapping_nodo_id ON sindicato_inq.nodos_cp_mapping (nodo_id);

-- 2. Se añade la columna 'nodo_id' a 'bloques' para rendimiento, como sugiere Claude.
--    Esta columna puede ser NULL para manejar bloques sin un CP definido.
ALTER TABLE sindicato_inq.bloques
ADD COLUMN nodo_id INTEGER REFERENCES sindicato_inq.nodos (id) ON DELETE SET NULL;

CREATE INDEX idx_bloques_nodo_id ON sindicato_inq.bloques (nodo_id);

-- 3. (LA CLAVE) Se crea una función y un trigger para mantener la sincronización AUTOMÁTICAMENTE.
--    Esto garantiza la integridad de mi diseño con el rendimiento del diseño de Claude.
CREATE OR REPLACE FUNCTION sync_bloque_nodo()
RETURNS TRIGGER AS $$
BEGIN
    -- Cuando se inserta o actualiza un piso...
    -- Se busca el nodo correspondiente a su CP y se actualiza el bloque padre.
    UPDATE sindicato_inq.bloques
    SET nodo_id = (SELECT nodo_id FROM sindicato_inq.nodos_cp_mapping WHERE cp = NEW.cp)
    WHERE id = NEW.bloque_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- El trigger se activa cada vez que se crea o modifica un piso.
CREATE TRIGGER trigger_sync_bloque_nodo
AFTER INSERT OR UPDATE OF cp ON sindicato_inq.pisos
FOR EACH ROW EXECUTE FUNCTION sync_bloque_nodo();
