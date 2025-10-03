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
    descripcion TEXT,
    usuario_responsable_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL
);

CREATE TABLE sindicato_inq.nodos_cp_mapping (
    cp INTEGER PRIMARY KEY,
    nodo_id INTEGER REFERENCES nodos (id) ON DELETE CASCADE NOT NULL
);

CREATE INDEX idx_nodos_cp_mapping_nodo_id ON sindicato_inq.nodos_cp_mapping (nodo_id);