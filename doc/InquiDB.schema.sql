CREATE SCHEMA IF NOT EXISTS sindicato_inq;

CREATE SEQUENCE sindicato_inq.afiliadas_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.asesorias_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.bloques_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.conflictos_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.diario_conflictos_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.empresas_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.entramado_empresas_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.facturacion_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.nodos_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.pisos_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.roles_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE sindicato_inq.usuarios_id_seq AS integer START WITH 1 INCREMENT BY 1;

CREATE  TABLE sindicato_inq.entramado_empresas ( 
	id                   integer DEFAULT nextval('sindicato_inq.entramado_empresas_id_seq'::regclass) NOT NULL  ,
	nombre               text    ,
	descripcion          text    ,
	CONSTRAINT entramado_empresas_pkey PRIMARY KEY ( id ),
	CONSTRAINT entramado_empresas_nombre_key UNIQUE ( nombre ) 
 );

CREATE  TABLE sindicato_inq.nodos ( 
	id                   integer DEFAULT nextval('sindicato_inq.nodos_id_seq'::regclass) NOT NULL  ,
	nombre               text  NOT NULL  ,
	descripcion          text    ,
	CONSTRAINT nodos_pkey PRIMARY KEY ( id ),
	CONSTRAINT nodos_nombre_key UNIQUE ( nombre ) 
 );

CREATE  TABLE sindicato_inq.nodos_cp_mapping ( 
	cp                   integer  NOT NULL  ,
	nodo_id              integer  NOT NULL  ,
	CONSTRAINT nodos_cp_mapping_pkey PRIMARY KEY ( cp )
 );

CREATE INDEX idx_nodos_cp_mapping_nodo_id ON sindicato_inq.nodos_cp_mapping USING  btree ( nodo_id );

CREATE  TABLE sindicato_inq.roles ( 
	id                   integer DEFAULT nextval('sindicato_inq.roles_id_seq'::regclass) NOT NULL  ,
	nombre               text  NOT NULL  ,
	descripcion          text    ,
	CONSTRAINT roles_pkey PRIMARY KEY ( id ),
	CONSTRAINT roles_nombre_key UNIQUE ( nombre ) 
 );

CREATE  TABLE sindicato_inq.usuarios ( 
	id                   integer DEFAULT nextval('sindicato_inq.usuarios_id_seq'::regclass) NOT NULL  ,
	"alias"              text    ,
	nombre               text    ,
	apellidos            text    ,
	email                text    ,
	roles                text    ,
	is_active            boolean DEFAULT true   ,
	created_at           timestamp DEFAULT CURRENT_TIMESTAMP   ,
	CONSTRAINT usuarios_pkey PRIMARY KEY ( id ),
	CONSTRAINT usuarios_alias_key UNIQUE ( "alias" ) 
 );

CREATE  TABLE sindicato_inq.empresas ( 
	id                   integer DEFAULT nextval('sindicato_inq.empresas_id_seq'::regclass) NOT NULL  ,
	entramado_id         integer    ,
	nombre               text    ,
	cif_nif_nie          text    ,
	directivos           text    ,
	api                  text    ,
	direccion_fiscal     text    ,
	CONSTRAINT empresas_pkey PRIMARY KEY ( id ),
	CONSTRAINT empresas_cif_nif_nie_key UNIQUE ( cif_nif_nie ) 
 );

CREATE INDEX idx_empresas_entramado_id ON sindicato_inq.empresas USING  btree ( entramado_id );

CREATE  TABLE sindicato_inq.usuario_credenciales ( 
	usuario_id           integer  NOT NULL  ,
	password_hash        text DEFAULT ''::text   ,
	CONSTRAINT usuario_credenciales_pkey PRIMARY KEY ( usuario_id )
 );

CREATE  TABLE sindicato_inq.usuario_roles ( 
	usuario_id           integer  NOT NULL  ,
	role_id              integer  NOT NULL  ,
	CONSTRAINT usuario_roles_pkey PRIMARY KEY ( usuario_id, role_id )
 );

CREATE INDEX idx_usuario_roles_usuario_id ON sindicato_inq.usuario_roles USING  btree ( usuario_id );

CREATE INDEX idx_usuario_roles_role_id ON sindicato_inq.usuario_roles USING  btree ( role_id );

CREATE  TABLE sindicato_inq.bloques ( 
	id                   integer DEFAULT nextval('sindicato_inq.bloques_id_seq'::regclass) NOT NULL  ,
	empresa_id           integer    ,
	direccion            text    ,
	estado               text    ,
	api                  text    ,
	nodo_id              integer    ,
	CONSTRAINT bloques_pkey PRIMARY KEY ( id ),
	CONSTRAINT bloques_direccion_key UNIQUE ( direccion ) 
 );

CREATE INDEX idx_bloques_empresa_id ON sindicato_inq.bloques USING  btree ( empresa_id );

CREATE INDEX idx_bloques_nodo_id ON sindicato_inq.bloques USING  btree ( nodo_id );

CREATE  TABLE sindicato_inq.pisos ( 
	id                   integer DEFAULT nextval('sindicato_inq.pisos_id_seq'::regclass) NOT NULL  ,
	bloque_id            integer    ,
	direccion            text  NOT NULL  ,
	municipio            text    ,
	cp                   integer    ,
	api                  text    ,
	prop_vertical        boolean    ,
	por_habitaciones     boolean    ,
	CONSTRAINT pisos_pkey PRIMARY KEY ( id ),
	CONSTRAINT pisos_direccion_key UNIQUE ( direccion ) 
 );

CREATE INDEX idx_pisos_bloque_id ON sindicato_inq.pisos USING  btree ( bloque_id );

CREATE  TABLE sindicato_inq.afiliadas ( 
	id                   integer DEFAULT nextval('sindicato_inq.afiliadas_id_seq'::regclass) NOT NULL  ,
	piso_id              integer    ,
	num_afiliada         text    ,
	nombre               text    ,
	apellidos            text    ,
	cif                  text    ,
	genero               text    ,
	email                text    ,
	telefono             text    ,
	regimen              text    ,
	estado               text    ,
	fecha_alta           date    ,
	fecha_baja           date    ,
	CONSTRAINT afiliadas_pkey PRIMARY KEY ( id ),
	CONSTRAINT afiliadas_num_afiliada_key UNIQUE ( num_afiliada ) ,
	CONSTRAINT afiliadas_cif_key UNIQUE ( cif ) 
 );

CREATE INDEX idx_afiliadas_piso_id ON sindicato_inq.afiliadas USING  btree ( piso_id );

CREATE  TABLE sindicato_inq.asesorias ( 
	id                   integer DEFAULT nextval('sindicato_inq.asesorias_id_seq'::regclass) NOT NULL  ,
	afiliada_id          integer    ,
	tecnica_id           integer    ,
	estado               text    ,
	fecha_asesoria       date    ,
	tipo_beneficiaria    text    ,
	tipo                 text    ,
	resultado            text    ,
	CONSTRAINT asesorias_pkey PRIMARY KEY ( id )
 );

CREATE INDEX idx_asesorias_afiliada_id ON sindicato_inq.asesorias USING  btree ( afiliada_id );

CREATE INDEX idx_asesorias_tecnica_id ON sindicato_inq.asesorias USING  btree ( tecnica_id );

CREATE  TABLE sindicato_inq.conflictos ( 
	id                   integer DEFAULT nextval('sindicato_inq.conflictos_id_seq'::regclass) NOT NULL  ,
	afiliada_id          integer    ,
	usuario_responsable_id integer    ,
	estado               text    ,
	ambito               text    ,
	causa                text    ,
	tarea_actual         text    ,
	fecha_apertura       date    ,
	fecha_cierre         date    ,
	descripcion          text    ,
	resolucion           text    ,
	CONSTRAINT conflictos_pkey PRIMARY KEY ( id )
 );

CREATE INDEX idx_conflictos_afiliada_id ON sindicato_inq.conflictos USING  btree ( afiliada_id );

CREATE INDEX idx_conflictos_usuario_responsable_id ON sindicato_inq.conflictos USING  btree ( usuario_responsable_id );

CREATE  TABLE sindicato_inq.diario_conflictos ( 
	id                   integer DEFAULT nextval('sindicato_inq.diario_conflictos_id_seq'::regclass) NOT NULL  ,
	conflicto_id         integer  NOT NULL  ,
	usuario_id           integer    ,
	estado               text    ,
	accion               text    ,
	notas                text    ,
	tarea_actual         text    ,
	created_at           timestamp DEFAULT CURRENT_TIMESTAMP   ,
	CONSTRAINT diario_conflictos_pkey PRIMARY KEY ( id )
 );

CREATE INDEX idx_diario_conflictos_conflicto_id ON sindicato_inq.diario_conflictos USING  btree ( conflicto_id );

CREATE INDEX idx_diario_conflictos_usuario_id ON sindicato_inq.diario_conflictos USING  btree ( usuario_id );

CREATE  TABLE sindicato_inq.facturacion ( 
	id                   integer DEFAULT nextval('sindicato_inq.facturacion_id_seq'::regclass) NOT NULL  ,
	afiliada_id          integer    ,
	cuota                decimal(8,2)    ,
	periodicidad         smallint    ,
	forma_pago           text    ,
	iban                 text    ,
	CONSTRAINT facturacion_pkey PRIMARY KEY ( id )
 );

CREATE INDEX idx_facturacion_afiliada_id ON sindicato_inq.facturacion USING  btree ( afiliada_id );

ALTER TABLE sindicato_inq.afiliadas ADD CONSTRAINT afiliadas_piso_id_fkey FOREIGN KEY ( piso_id ) REFERENCES sindicato_inq.pisos( id ) ON DELETE SET NULL;

ALTER TABLE sindicato_inq.asesorias ADD CONSTRAINT asesorias_afiliada_id_fkey FOREIGN KEY ( afiliada_id ) REFERENCES sindicato_inq.afiliadas( id ) ON DELETE SET NULL;

ALTER TABLE sindicato_inq.asesorias ADD CONSTRAINT asesorias_tecnica_id_fkey FOREIGN KEY ( tecnica_id ) REFERENCES sindicato_inq.usuarios( id ) ON DELETE SET NULL;

ALTER TABLE sindicato_inq.bloques ADD CONSTRAINT bloques_empresa_id_fkey FOREIGN KEY ( empresa_id ) REFERENCES sindicato_inq.empresas( id ) ON DELETE SET NULL;

ALTER TABLE sindicato_inq.bloques ADD CONSTRAINT bloques_nodo_id_fkey FOREIGN KEY ( nodo_id ) REFERENCES sindicato_inq.nodos( id ) ON DELETE SET NULL;

ALTER TABLE sindicato_inq.conflictos ADD CONSTRAINT conflictos_afiliada_id_fkey FOREIGN KEY ( afiliada_id ) REFERENCES sindicato_inq.afiliadas( id ) ON DELETE SET NULL;

ALTER TABLE sindicato_inq.conflictos ADD CONSTRAINT conflictos_usuario_responsable_id_fkey FOREIGN KEY ( usuario_responsable_id ) REFERENCES sindicato_inq.usuarios( id ) ON DELETE SET NULL;

ALTER TABLE sindicato_inq.diario_conflictos ADD CONSTRAINT diario_conflictos_conflicto_id_fkey FOREIGN KEY ( conflicto_id ) REFERENCES sindicato_inq.conflictos( id ) ON DELETE CASCADE;

ALTER TABLE sindicato_inq.diario_conflictos ADD CONSTRAINT diario_conflictos_usuario_id_fkey FOREIGN KEY ( usuario_id ) REFERENCES sindicato_inq.usuarios( id ) ON DELETE SET NULL;

ALTER TABLE sindicato_inq.empresas ADD CONSTRAINT empresas_entramado_id_fkey FOREIGN KEY ( entramado_id ) REFERENCES sindicato_inq.entramado_empresas( id ) ON DELETE SET NULL;

ALTER TABLE sindicato_inq.facturacion ADD CONSTRAINT facturacion_afiliada_id_fkey FOREIGN KEY ( afiliada_id ) REFERENCES sindicato_inq.afiliadas( id ) ON DELETE CASCADE;

ALTER TABLE sindicato_inq.nodos_cp_mapping ADD CONSTRAINT nodos_cp_mapping_nodo_id_fkey FOREIGN KEY ( nodo_id ) REFERENCES sindicato_inq.nodos( id ) ON DELETE CASCADE;

ALTER TABLE sindicato_inq.pisos ADD CONSTRAINT pisos_bloque_id_fkey FOREIGN KEY ( bloque_id ) REFERENCES sindicato_inq.bloques( id ) ON DELETE SET NULL;

ALTER TABLE sindicato_inq.usuario_credenciales ADD CONSTRAINT usuario_credenciales_usuario_id_fkey FOREIGN KEY ( usuario_id ) REFERENCES sindicato_inq.usuarios( id ) ON DELETE CASCADE;

ALTER TABLE sindicato_inq.usuario_roles ADD CONSTRAINT usuario_roles_usuario_id_fkey FOREIGN KEY ( usuario_id ) REFERENCES sindicato_inq.usuarios( id ) ON DELETE CASCADE;

ALTER TABLE sindicato_inq.usuario_roles ADD CONSTRAINT usuario_roles_role_id_fkey FOREIGN KEY ( role_id ) REFERENCES sindicato_inq.roles( id ) ON DELETE CASCADE;

CREATE TRIGGER trigger_sync_bloque_nodo AFTER INSERT OR UPDATE OF cp ON sindicato_inq.pisos FOR EACH ROW EXECUTE FUNCTION sync_bloque_nodo();

CREATE OR REPLACE FUNCTION sindicato_inq.sync_bloque_nodo()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Cuando se inserta o actualiza un piso...
    -- Se busca el nodo correspondiente a su CP y se actualiza el bloque padre.
    UPDATE sindicato_inq.bloques
    SET nodo_id = (SELECT nodo_id FROM sindicato_inq.nodos_cp_mapping WHERE cp = NEW.cp)
    WHERE id = NEW.bloque_id;
    RETURN NEW;
END;
$function$
;


