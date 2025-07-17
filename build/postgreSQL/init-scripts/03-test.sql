-- PostgreSQL version of the provided MySQL schema

-- Drop tables if exist (for idempotency, you can remove in production)
DROP TABLE IF EXISTS vw_afiliades CASCADE;

DROP TABLE IF EXISTS afiliada_historic_regims CASCADE;

DROP TABLE IF EXISTS afiliades CASCADE;

DROP TABLE IF EXISTS afiliades_delegades_conflicte CASCADE;

DROP TABLE IF EXISTS agrupacions_blocs CASCADE;

DROP TABLE IF EXISTS assessoraments CASCADE;

DROP TABLE IF EXISTS assessorament_documents CASCADE;

DROP TABLE IF EXISTS blocs CASCADE;

DROP TABLE IF EXISTS blocs_agrupacio_blocs CASCADE;

DROP TABLE IF EXISTS blocs_entramat CASCADE;

DROP TABLE IF EXISTS blocs_importats CASCADE;

DROP TABLE IF EXISTS causes_conflicte CASCADE;

DROP TABLE IF EXISTS changes_log CASCADE;

DROP TABLE IF EXISTS colaboradores_collectiu CASCADE;

DROP TABLE IF EXISTS collectius CASCADE;

DROP TABLE IF EXISTS comissions CASCADE;

DROP TABLE IF EXISTS conflictes CASCADE;

DROP TABLE IF EXISTS directius CASCADE;

DROP TABLE IF EXISTS directius_empresa CASCADE;

DROP TABLE IF EXISTS domiciliacions CASCADE;

DROP TABLE IF EXISTS empreses CASCADE;

DROP TABLE IF EXISTS entramats CASCADE;

DROP TABLE IF EXISTS especialitats CASCADE;

DROP TABLE IF EXISTS estats_habitatge CASCADE;

DROP TABLE IF EXISTS "groups" CASCADE;

DROP TABLE IF EXISTS import_templates CASCADE;

DROP TABLE IF EXISTS interessades CASCADE;

DROP TABLE IF EXISTS medias CASCADE;

DROP TABLE IF EXISTS municipis CASCADE;

DROP TABLE IF EXISTS negociacions_conflicte CASCADE;

DROP TABLE IF EXISTS nivells_participacio CASCADE;

DROP TABLE IF EXISTS no_afiliades CASCADE;

DROP TABLE IF EXISTS options CASCADE;

DROP TABLE IF EXISTS origens_afiliacio CASCADE;

DROP TABLE IF EXISTS patterns CASCADE;

DROP TABLE IF EXISTS persones CASCADE;

DROP TABLE IF EXISTS pisos CASCADE;

DROP TABLE IF EXISTS pisos_entramat CASCADE;

DROP TABLE IF EXISTS processes CASCADE;

DROP TABLE IF EXISTS process_executions CASCADE;

DROP TABLE IF EXISTS provincies CASCADE;

DROP TABLE IF EXISTS remote_printers CASCADE;

DROP TABLE IF EXISTS remote_printer_jobs CASCADE;

DROP TABLE IF EXISTS resolucions_conflicte CASCADE;

DROP TABLE IF EXISTS resultats_assessoraments CASCADE;

DROP TABLE IF EXISTS roles CASCADE;

DROP TABLE IF EXISTS role_permissions CASCADE;

DROP TABLE IF EXISTS seccions_sindicals CASCADE;

DROP TABLE IF EXISTS serveis_juridics CASCADE;

DROP TABLE IF EXISTS servei_juridic_documents CASCADE;

DROP TABLE IF EXISTS service_tokens CASCADE;

DROP TABLE IF EXISTS simpatitzants CASCADE;

DROP TABLE IF EXISTS simpatitzant_historic_regims CASCADE;

DROP TABLE IF EXISTS sollicituds CASCADE;

DROP TABLE IF EXISTS tecniques CASCADE;

DROP TABLE IF EXISTS tipus_assessoraments CASCADE;

DROP TABLE IF EXISTS tipus_serveis_juridics CASCADE;

DROP TABLE IF EXISTS tipus_sseguiment CASCADE;

DROP TABLE IF EXISTS users CASCADE;

DROP TABLE IF EXISTS user_groups CASCADE;

DROP TABLE IF EXISTS user_page_options CASCADE;

DROP TABLE IF EXISTS user_roles CASCADE;

-- Table definitions

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(150) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    default_group INTEGER NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    phone VARCHAR(50)
);

CREATE TABLE "groups" (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(150) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(150) NOT NULL,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE role_permissions (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    permission VARCHAR(50) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    level VARCHAR(1),
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    UNIQUE (
        parent_id,
        permission,
        operation
    )
);

CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (parent_id, child_id)
);

CREATE TABLE user_groups (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (parent_id, child_id)
);

CREATE TABLE user_page_options (
    id SERIAL PRIMARY KEY,
    user_code VARCHAR(50) NOT NULL,
    page_code VARCHAR(200) NOT NULL,
    option_key VARCHAR(200) NOT NULL,
    option_value TEXT,
    UNIQUE (
        user_code,
        page_code,
        option_key
    )
);

CREATE TABLE persones (
    id SERIAL PRIMARY KEY,
    genere VARCHAR(1),
    nom VARCHAR(100) NOT NULL,
    cognoms VARCHAR(100),
    email VARCHAR(150),
    telefon VARCHAR(50),
    butlleti SMALLINT,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    no_rebre_info SMALLINT
);

CREATE TABLE estats_habitatge (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    nom_es VARCHAR(50),
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE provincies (
    id SERIAL PRIMARY KEY,
    codi VARCHAR(2) NOT NULL UNIQUE,
    nom VARCHAR(100) NOT NULL,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE municipis (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(200) NOT NULL UNIQUE,
    provincia INTEGER NOT NULL,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE empreses (
    id SERIAL PRIMARY KEY,
    cif VARCHAR(20) UNIQUE,
    nom VARCHAR(100) NOT NULL,
    api SMALLINT,
    web VARCHAR(200),
    email TEXT,
    telefon VARCHAR(50),
    google_id VARCHAR(400),
    adreca VARCHAR(400),
    nom_via VARCHAR(200),
    numero VARCHAR(20),
    escala VARCHAR(10),
    pis VARCHAR(10),
    porta VARCHAR(10),
    complement VARCHAR(50),
    municipi INTEGER,
    codi_postal VARCHAR(5),
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    web_info_empresa VARCHAR(200),
    entramat INTEGER,
    descripcio TEXT
);

CREATE TABLE pisos (
    id SERIAL PRIMARY KEY,
    adreca VARCHAR(400) NOT NULL,
    bloc INTEGER NOT NULL,
    escala VARCHAR(10),
    pis VARCHAR(50),
    porta VARCHAR(10),
    complement VARCHAR(50),
    estat INTEGER,
    superficie NUMERIC(3, 0),
    num_habitacions NUMERIC(2, 0),
    cedula_habitabilitat VARCHAR(1),
    certificat_energetic VARCHAR(1),
    buit VARCHAR(1),
    data_buit TIMESTAMP,
    api INTEGER,
    propietat INTEGER,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    propietat_ultima_actualitzacio TIMESTAMP,
    propietat_any_actualitzacio NUMERIC(4, 0)
);

CREATE TABLE blocs (
    id SERIAL PRIMARY KEY,
    google_id VARCHAR(400) NOT NULL,
    adreca VARCHAR(400) NOT NULL,
    nom_via VARCHAR(200) NOT NULL,
    numero VARCHAR(20) NOT NULL,
    municipi INTEGER NOT NULL,
    codi_postal VARCHAR(5) NOT NULL,
    estat INTEGER,
    any_construccio NUMERIC(4, 0),
    num_habitatges NUMERIC(3, 0),
    num_locals NUMERIC(3, 0),
    propietat_vertical VARCHAR(1),
    ascensor VARCHAR(1),
    parquing VARCHAR(1),
    buit VARCHAR(1),
    data_buit TIMESTAMP,
    api INTEGER,
    propietat INTEGER,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    superficie NUMERIC(5, 0),
    propietat_ultima_actualitzacio TIMESTAMP,
    propietat_any_actualitzacio NUMERIC(4, 0),
    observacions VARCHAR(200),
    hpo VARCHAR(1),
    data_fi_hpo TIMESTAMP
);

CREATE TABLE agrupacions_blocs (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(200) NOT NULL UNIQUE,
    propietat INTEGER NOT NULL,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    api INTEGER,
    propietat_any_actualitzacio NUMERIC(4, 0)
);

CREATE TABLE blocs_agrupacio_blocs (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    bloc INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    UNIQUE (parent_id, bloc)
);

CREATE TABLE blocs_entramat (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (parent_id, child_id)
);

CREATE TABLE blocs_importats (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    nom_via_original VARCHAR(200),
    numero_original VARCHAR(20),
    municipi_original VARCHAR(200),
    codi_postal_original VARCHAR(5),
    adreca_original VARCHAR(400),
    google_id VARCHAR(400),
    adreca VARCHAR(400),
    nom_via VARCHAR(200),
    numero VARCHAR(20),
    municipi INTEGER,
    codi_postal VARCHAR(5),
    estat INTEGER,
    any_construccio NUMERIC(4, 0),
    num_habitatges NUMERIC(3, 0),
    num_locals NUMERIC(3, 0),
    propietat_vertical VARCHAR(1),
    superficie NUMERIC(5, 0),
    ascensor VARCHAR(1),
    parquing VARCHAR(1),
    buit VARCHAR(1),
    data_buit TIMESTAMP,
    cif_api_original VARCHAR(20),
    api_original VARCHAR(200),
    cif_propietat_original VARCHAR(20),
    propietat_original VARCHAR(200),
    api INTEGER,
    propietat INTEGER,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    propietat_ultima_actualitzacio TIMESTAMP
);

CREATE TABLE comissions (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE nivells_participacio (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE origens_afiliacio (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE tipus_sseguiment (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE seccions_sindicals (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    codis_postals VARCHAR(400)
);

CREATE TABLE afiliades (
    id SERIAL PRIMARY KEY,
    cif VARCHAR(20) NOT NULL UNIQUE,
    persona INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    data_alta TIMESTAMP NOT NULL,
    data_baixa TIMESTAMP,
    origen_afiliacio INTEGER,
    nivell_participacio INTEGER,
    comissio INTEGER,
    forma_pagament VARCHAR(1),
    compte_corrent VARCHAR(24),
    quota NUMERIC(5, 2),
    regim VARCHAR(1),
    regim_altres VARCHAR(50),
    pis INTEGER,
    data_inici_contracte TIMESTAMP,
    durada_contracte NUMERIC(2, 0),
    renda_contracte NUMERIC(6, 2),
    num_habitants NUMERIC(2, 0),
    ingressos_mensuals NUMERIC(7, 2),
    collectiu INTEGER,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    contracte_indefinit SMALLINT,
    durada_contracte_prorrogues NUMERIC(1, 0),
    comentaris TEXT,
    adreca_no_normalitzada SMALLINT,
    adreca_no_normalitzada_text VARCHAR(400),
    frequencia_pagament VARCHAR(1),
    seccio_sindical INTEGER NOT NULL,
    data_seguiment TIMESTAMP,
    tipus_seguiment INTEGER,
    observacions_estat TEXT
);

CREATE TABLE afiliada_historic_regims (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    regim VARCHAR(1),
    regim_altres VARCHAR(50),
    pis INTEGER,
    adreca_no_normalitzada SMALLINT,
    adreca_no_normalitzada_text VARCHAR(400),
    data_inici_contracte TIMESTAMP,
    contracte_indefinit SMALLINT,
    durada_contracte NUMERIC(2, 0),
    durada_contracte_prorrogues NUMERIC(1, 0),
    renda_contracte NUMERIC(6, 2),
    num_habitants NUMERIC(2, 0),
    ingressos_mensuals NUMERIC(7, 2),
    data_fi_regim TIMESTAMP NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL
);

CREATE TABLE no_afiliades (
    id SERIAL PRIMARY KEY,
    persona INTEGER NOT NULL,
    regim VARCHAR(1),
    regim_altres VARCHAR(50),
    pis INTEGER,
    data_inici_contracte TIMESTAMP,
    durada_contracte NUMERIC(2, 0),
    renda_contracte NUMERIC(6, 2),
    num_habitants NUMERIC(2, 0),
    ingressos_mensuals NUMERIC(7, 2),
    collectiu INTEGER NOT NULL,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    data_alta TIMESTAMP,
    doble_afiliada SMALLINT DEFAULT 0,
    tipus_id VARCHAR(1) NOT NULL DEFAULT 'C',
    cif VARCHAR(20) UNIQUE,
    pais VARCHAR(20),
    forma_pagament VARCHAR(1),
    frequencia_pagament VARCHAR(1),
    compte_corrent VARCHAR(24),
    quota NUMERIC(5, 2)
);

CREATE TABLE simpatitzants (
    id SERIAL PRIMARY KEY,
    cif VARCHAR(20) NOT NULL UNIQUE,
    persona INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    data_alta TIMESTAMP NOT NULL,
    data_baixa TIMESTAMP,
    observacions_estat TEXT,
    origen_afiliacio INTEGER,
    seccio_sindical INTEGER NOT NULL,
    nivell_participacio INTEGER,
    comissio INTEGER,
    regim VARCHAR(1),
    regim_altres VARCHAR(50),
    pis INTEGER,
    data_inici_contracte TIMESTAMP,
    contracte_indefinit SMALLINT,
    durada_contracte NUMERIC(2, 0),
    durada_contracte_prorrogues NUMERIC(1, 0),
    renda_contracte NUMERIC(6, 2),
    num_habitants NUMERIC(2, 0),
    ingressos_mensuals NUMERIC(7, 2),
    collectiu INTEGER,
    comentaris TEXT,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE simpatitzant_historic_regims (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    regim VARCHAR(1),
    regim_altres VARCHAR(50),
    pis INTEGER,
    data_inici_contracte TIMESTAMP,
    contracte_indefinit SMALLINT,
    durada_contracte NUMERIC(2, 0),
    durada_contracte_prorrogues NUMERIC(1, 0),
    renda_contracte NUMERIC(6, 2),
    num_habitants NUMERIC(2, 0),
    ingressos_mensuals NUMERIC(7, 2),
    data_fi_regim TIMESTAMP NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL
);

CREATE TABLE causes_conflicte (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE resolucions_conflicte (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    nom VARCHAR(50) NOT NULL,
    resultat VARCHAR(1) NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    UNIQUE (parent_id, nom)
);

CREATE TABLE conflictes (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    ambit VARCHAR(1) NOT NULL,
    afiliada_afectada INTEGER,
    bloc_afectat INTEGER,
    entramat_afectat INTEGER,
    delegada INTEGER,
    causa INTEGER NOT NULL,
    data_obertura TIMESTAMP NOT NULL,
    data_darrera_assemblea TIMESTAMP,
    data_hivernacio TIMESTAMP,
    data_tancament TIMESTAMP,
    data_proper_desnonament TIMESTAMP,
    demanda SMALLINT,
    registre_propietat SMALLINT,
    assemblea SMALLINT,
    carta_enviada SMALLINT,
    embustiada SMALLINT,
    accions SMALLINT,
    accions_descripcio VARCHAR(400),
    resolucio INTEGER,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    agrupacio_blocs_afectada INTEGER,
    no_afiliada_afectada INTEGER,
    oficina_habitatge SMALLINT,
    serveis_socials SMALLINT,
    justicia_gratuita SMALLINT,
    taula_emergencia SMALLINT,
    padro_municipal SMALLINT,
    informe_exclusio_residencial SMALLINT,
    afiliades_delegades TEXT,
    trucada_propietat SMALLINT,
    simpatitzant_afectada INTEGER,
    informe_vulnerabilitat SMALLINT,
    reunions_negociacio SMALLINT
);

CREATE TABLE negociacions_conflicte (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    data TIMESTAMP NOT NULL,
    estat TEXT NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    tasques TEXT
);

CREATE TABLE afiliades_delegades_conflicte (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (parent_id, child_id)
);

CREATE TABLE changes_log (
    id SERIAL PRIMARY KEY,
    object VARCHAR(200) NOT NULL,
    object_id INTEGER NOT NULL,
    child_table VARCHAR(50),
    child_table_id INTEGER,
    operation VARCHAR(1),
    timestamp TIMESTAMP NOT NULL,
    "user" INTEGER NOT NULL,
    changes TEXT NOT NULL
);

CREATE TABLE collectius (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    descripcio TEXT,
    email VARCHAR(150) NOT NULL,
    telefon VARCHAR(50),
    persona_contacte VARCHAR(200),
    telefon_persona_contacte VARCHAR(50),
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    cobraments SMALLINT DEFAULT 0,
    assessoraments SMALLINT DEFAULT 0,
    quota NUMERIC(5, 2),
    num_serie VARCHAR(8),
    domiciliacions SMALLINT DEFAULT 0
);

CREATE TABLE colaboradores_collectiu (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (parent_id, child_id)
);

CREATE TABLE assessoraments (
    id SERIAL PRIMARY KEY,
    afiliada INTEGER,
    tipus INTEGER NOT NULL,
    tecnica INTEGER,
    data_assessorament TIMESTAMP,
    descripcio TEXT,
    comentaris TEXT,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(50) NOT NULL,
    data_contacte TIMESTAMP,
    data_finalitzacio TIMESTAMP,
    resultat INTEGER,
    tipus_beneficiaria VARCHAR(1) NOT NULL DEFAULT 'A',
    no_afiliada INTEGER
);

CREATE TABLE resultats_assessoraments (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE tipus_assessoraments (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE tecniques (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(200) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL,
    telefon VARCHAR(50),
    especialitat INTEGER NOT NULL,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE especialitats (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE assessorament_documents (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    document INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL
);

CREATE TABLE medias (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(400) NOT NULL,
    hash VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    is_image SMALLINT,
    is_public SMALLINT,
    file_size NUMERIC(12, 0) NOT NULL,
    image_width NUMERIC(5, 0),
    image_height NUMERIC(5, 0),
    mime_type VARCHAR(100) NOT NULL,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    image_quality INTEGER DEFAULT 1
);

CREATE TABLE domiciliacions (
    id SERIAL PRIMARY KEY,
    data_emissio TIMESTAMP,
    fitxer INTEGER,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE directius (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    descripcio TEXT,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE directius_empresa (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (parent_id, child_id)
);

CREATE TABLE entramats (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    descripcio TEXT,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE pisos_entramat (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (parent_id, child_id)
);

CREATE TABLE sollicituds (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    genere VARCHAR(1),
    nom VARCHAR(100),
    cognoms VARCHAR(100),
    email VARCHAR(150),
    telefon VARCHAR(50),
    butlleti SMALLINT,
    cif VARCHAR(20),
    data_alta TIMESTAMP,
    origen_afiliacio INTEGER,
    forma_pagament VARCHAR(1),
    compte_corrent VARCHAR(24),
    quota NUMERIC(5, 2),
    regim VARCHAR(1),
    regim_altres VARCHAR(50),
    google_id_original TEXT,
    adreca_original VARCHAR(400),
    municipi_original VARCHAR(200),
    codi_postal_original VARCHAR(5),
    google_id TEXT,
    adreca VARCHAR(400),
    nom_via VARCHAR(200),
    numero VARCHAR(20),
    municipi INTEGER,
    codi_postal VARCHAR(5),
    escala VARCHAR(10),
    pis VARCHAR(50),
    porta VARCHAR(10),
    complement VARCHAR(50),
    any_construccio NUMERIC(4, 0),
    ascensor VARCHAR(1),
    parquing VARCHAR(1),
    estat_pis INTEGER,
    superficie NUMERIC(3, 0),
    cedula_habitabilitat VARCHAR(1),
    certificat_energetic VARCHAR(1),
    cif_api_original VARCHAR(20),
    nom_api_original VARCHAR(100),
    api INTEGER,
    cif_propietat_original VARCHAR(20),
    nom_propietat_original VARCHAR(100),
    propietat INTEGER,
    pis_data_inici_contracte TIMESTAMP,
    pis_durada_contracte NUMERIC(2, 0),
    pis_renda_contracte NUMERIC(6, 2),
    habitacio_renda_contracte NUMERIC(6, 2),
    pis_num_habitants NUMERIC(2, 0),
    habitacio_num_habitants NUMERIC(2, 0),
    pis_ingressos_mensuals NUMERIC(7, 2),
    habitacio_ingressos_mensuals NUMERIC(7, 2),
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    pis_contracte_indefinit SMALLINT,
    pis_durada_contracte_prorrogues NUMERIC(1, 0),
    comentaris TEXT,
    adreca_no_normalitzada SMALLINT,
    adreca_no_normalitzada_text TEXT,
    frequencia_pagament VARCHAR(1),
    seccio_sindical INTEGER,
    no_rebre_info SMALLINT,
    propietat_vertical VARCHAR(1)
);

CREATE TABLE import_templates (
    id SERIAL PRIMARY KEY,
    import VARCHAR(50) NOT NULL,
    name VARCHAR(50) NOT NULL,
    content TEXT
);

CREATE TABLE options (
    id SERIAL PRIMARY KEY,
    section VARCHAR(50) NOT NULL,
    option_key VARCHAR(200),
    option_value VARCHAR(500),
    UNIQUE (section, option_key)
);

CREATE TABLE resultats_assessoraments (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE serveis_juridics (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    afiliada INTEGER NOT NULL,
    tipus INTEGER NOT NULL,
    tecnica INTEGER,
    data_servei TIMESTAMP,
    preu NUMERIC(5, 2),
    descripcio TEXT,
    comentaris TEXT,
    resultat VARCHAR(1),
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE servei_juridic_documents (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    document INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL
);

CREATE TABLE tipus_serveis_juridics (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    owner_user INTEGER NOT NULL,
    owner_group INTEGER NOT NULL,
    create_user INTEGER NOT NULL,
    update_user INTEGER NOT NULL,
    delete_user INTEGER,
    create_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_timestamp TIMESTAMP NOT NULL,
    delete_timestamp TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Add other tables as needed following the same patterns...

-- Foreign Keys and Indexes should be added here according to your relations,
-- Using the following syntax (example for 'afiliades'):
ALTER TABLE afiliades
ADD CONSTRAINT fk_afiliades_persona_persones FOREIGN KEY (persona) REFERENCES persones (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- (Continue for all foreign key relationships as per your original schema...)

-- Example View definition (adapt columns as needed)
CREATE OR REPLACE VIEW vw_afiliades AS
SELECT
    pe.genere,
    pe.nom,
    pe.cognoms,
    pe.email,
    pe.telefon,
    CASE
        WHEN pe.butlleti IS NULL
        OR pe.butlleti = 0 THEN 'n'
        ELSE 's'
    END AS butlleti,
    a.cif,
    CASE
        WHEN a.adreca_no_normalitzada IS NULL
        OR a.adreca_no_normalitzada = 0 THEN 's'
        ELSE 'n'
    END AS adreca_normalitzada,
    CASE
        WHEN a.adreca_no_normalitzada = 1 THEN a.adreca_no_normalitzada_text
        ELSE p.adreca
    END AS adreca,
    b.codi_postal,
    m.nom AS municipi,
    pr.nom AS provincia,
    a.data_alta,
    a.status AS estat,
    a.data_baixa,
    a.regim,
    CASE
        WHEN a.regim = 'P' THEN 'Propietat'
        WHEN a.regim = 'L' THEN 'Lloguer'
        WHEN a.regim = 'H' THEN 'Habitació'
        WHEN a.regim = 'A' THEN a.regim_altres
    END AS regim_descripcio,
    co.nom AS collectiu,
    c.nom AS comissio,
    a.forma_pagament,
    a.frequencia_pagament,
    a.quota,
    np.nom AS nivell_participacio,
    of.nom AS origen_afiliacio,
    ehp.nom AS estat_pis,
    p.num_habitacions,
    p.cedula_habitabilitat,
    p.certificat_energetic,
    p.superficie AS superficie_pis,
    b.any_construccio,
    b.ascensor,
    b.num_habitatges,
    b.num_locals,
    b.parquing,
    b.propietat_vertical,
    b.superficie AS superficie_bloc,
    ehb.nom AS estat_bloc,
    CASE
        WHEN p.propietat IS NOT NULL THEN epp.nom
        WHEN b.propietat IS NOT NULL THEN epb.nom
        WHEN ag.propietat IS NOT NULL THEN epa.nom
        ELSE NULL
    END AS propietat,
    CASE
        WHEN p.api IS NOT NULL THEN eap.nom
        WHEN b.api IS NOT NULL THEN eab.nom
        ELSE NULL
    END AS api
FROM
    afiliades a
    LEFT JOIN persones pe ON a.persona = pe.id
    LEFT JOIN comissions c ON a.comissio = c.id
    LEFT JOIN collectius co ON a.collectiu = co.id
    LEFT JOIN nivells_participacio np ON a.nivell_participacio = np.id
    LEFT JOIN origens_afiliacio of ON a.origen_afiliacio = of.id
    LEFT JOIN pisos p ON a.pis = p.id
    LEFT JOIN blocs b ON p.bloc = b.id
    LEFT JOIN blocs_agrupacio_blocs bag ON b.id = bag.bloc
    LEFT JOIN agrupacions_blocs ag ON bag.parent_id = ag.id
    LEFT JOIN estats_habitatge ehp ON p.estat = ehp.id
    LEFT JOIN estats_habitatge ehb ON b.estat = ehb.id
    LEFT JOIN municipis m ON b.municipi = m.id
    LEFT JOIN provincies pr ON m.provincia = pr.id
    LEFT JOIN empreses epp ON p.propietat = epp.id
    LEFT JOIN empreses epb ON b.propietat = epb.id
    LEFT JOIN empreses epa ON ag.propietat = epa.id
    LEFT JOIN empreses eap ON p.api = eap.id
    LEFT JOIN empreses eab ON b.api = eab.id;

-- ==========================
-- FOREIGN KEYS AND INDEXES
-- ==========================

-- users
ALTER TABLE users
ADD CONSTRAINT fk_users_default_group_groups FOREIGN KEY (default_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- user_groups & user_roles
ALTER TABLE user_groups
ADD CONSTRAINT fk_user_groups_parent_id_users FOREIGN KEY (parent_id) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_user_groups_child_id_groups FOREIGN KEY (child_id) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_user_groups_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE user_roles
ADD CONSTRAINT fk_user_roles_parent_id_users FOREIGN KEY (parent_id) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_user_roles_child_id_roles FOREIGN KEY (child_id) REFERENCES roles (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_user_roles_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- user_page_options
-- No FKs (all string-based).

-- roles, role_permissions
ALTER TABLE roles
ADD CONSTRAINT fk_roles_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_roles_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_roles_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_roles_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_roles_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE role_permissions
ADD CONSTRAINT fk_role_permissions_parent_id_roles FOREIGN KEY (parent_id) REFERENCES roles (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_role_permissions_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_role_permissions_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- provincies, municipis
ALTER TABLE municipis
ADD CONSTRAINT fk_municipis_provincia_provincies FOREIGN KEY (provincia) REFERENCES provincies (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_municipis_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_municipis_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_municipis_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_municipis_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_municipis_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE provincies
ADD CONSTRAINT fk_provincies_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_provincies_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_provincies_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_provincies_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_provincies_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- estats_habitatge
ALTER TABLE estats_habitatge
ADD CONSTRAINT fk_estats_habitatge_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_estats_habitatge_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_estats_habitatge_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_estats_habitatge_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_estats_habitatge_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- empreses
ALTER TABLE empreses
ADD CONSTRAINT fk_empreses_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_empreses_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_empreses_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_empreses_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_empreses_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_empreses_municipi_municipis FOREIGN KEY (municipi) REFERENCES municipis (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_empreses_entramat_entramats FOREIGN KEY (entramat) REFERENCES entramats (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- pisos
ALTER TABLE pisos
ADD CONSTRAINT fk_pisos_bloc_blocs FOREIGN KEY (bloc) REFERENCES blocs (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_pisos_estat_estats_habitatge FOREIGN KEY (estat) REFERENCES estats_habitatge (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_pisos_api_empreses FOREIGN KEY (api) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_pisos_propietat_empreses FOREIGN KEY (propietat) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_pisos_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_pisos_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_pisos_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_pisos_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_pisos_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- blocs
ALTER TABLE blocs
ADD CONSTRAINT fk_blocs_municipi_municipis FOREIGN KEY (municipi) REFERENCES municipis (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_estat_estats_habitatge FOREIGN KEY (estat) REFERENCES estats_habitatge (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_api_empreses FOREIGN KEY (api) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_propietat_empreses FOREIGN KEY (propietat) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- agrupacions_blocs
ALTER TABLE agrupacions_blocs
ADD CONSTRAINT fk_agrupacions_blocs_propietat_empreses FOREIGN KEY (propietat) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_agrupacions_blocs_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_agrupacions_blocs_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_agrupacions_blocs_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_agrupacions_blocs_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_agrupacions_blocs_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_agrupacions_blocs_api_empreses FOREIGN KEY (api) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- blocs_agrupacio_blocs
ALTER TABLE blocs_agrupacio_blocs
ADD CONSTRAINT fk_blocs_agrupacio_blocs_parent_id_agrupacions_blocs FOREIGN KEY (parent_id) REFERENCES agrupacions_blocs (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_agrupacio_blocs_bloc_blocs FOREIGN KEY (bloc) REFERENCES blocs (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_agrupacio_blocs_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_agrupacio_blocs_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- blocs_entramat
ALTER TABLE blocs_entramat
ADD CONSTRAINT fk_blocs_entramat_parent_id_entramats FOREIGN KEY (parent_id) REFERENCES entramats (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_entramat_child_id_blocs FOREIGN KEY (child_id) REFERENCES blocs (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_entramat_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- blocs_importats
ALTER TABLE blocs_importats
ADD CONSTRAINT fk_blocs_importats_api_empreses FOREIGN KEY (api) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_importats_propietat_empreses FOREIGN KEY (propietat) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_importats_municipi_municipis FOREIGN KEY (municipi) REFERENCES municipis (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_importats_estat_estats_habitatge FOREIGN KEY (estat) REFERENCES estats_habitatge (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_importats_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_importats_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_importats_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_importats_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_blocs_importats_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- afiliades
ALTER TABLE afiliades
ADD CONSTRAINT fk_afiliades_persona_persones FOREIGN KEY (persona) REFERENCES persones (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_origen_afiliacio_origens_afiliacio FOREIGN KEY (origen_afiliacio) REFERENCES origens_afiliacio (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_nivell_participacio_nivells_participacio FOREIGN KEY (nivell_participacio) REFERENCES nivells_participacio (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_comissio_comissions FOREIGN KEY (comissio) REFERENCES comissions (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_pis_pisos FOREIGN KEY (pis) REFERENCES pisos (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_collectiu_collectius FOREIGN KEY (collectiu) REFERENCES collectius (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_seccio_sindical_seccions_sindicals FOREIGN KEY (seccio_sindical) REFERENCES seccions_sindicals (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_tipus_seguiment_tipus_sseguiment FOREIGN KEY (tipus_seguiment) REFERENCES tipus_sseguiment (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- afiliada_historic_regims
ALTER TABLE afiliada_historic_regims
ADD CONSTRAINT fk_afiliada_historic_regims_parent_id_afiliades FOREIGN KEY (parent_id) REFERENCES afiliades (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliada_historic_regims_pis_pisos FOREIGN KEY (pis) REFERENCES pisos (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliada_historic_regims_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliada_historic_regims_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- simpatitzants
ALTER TABLE simpatitzants
ADD CONSTRAINT fk_simpatitzants_persona_persones FOREIGN KEY (persona) REFERENCES persones (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_origen_afiliacio_origens_afiliacio FOREIGN KEY (origen_afiliacio) REFERENCES origens_afiliacio (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_seccio_sindical_seccions_sindicals FOREIGN KEY (seccio_sindical) REFERENCES seccions_sindicals (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_nivell_participacio_nivells_participacio FOREIGN KEY (nivell_participacio) REFERENCES nivells_participacio (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_comissio_comissions FOREIGN KEY (comissio) REFERENCES comissions (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_pis_pisos FOREIGN KEY (pis) REFERENCES pisos (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_collectiu_collectius FOREIGN KEY (collectiu) REFERENCES collectius (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzants_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- simpatitzant_historic_regims
ALTER TABLE simpatitzant_historic_regims
ADD CONSTRAINT fk_simpatitzant_historic_regims_parent_id_simpatitzants FOREIGN KEY (parent_id) REFERENCES simpatitzants (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzant_historic_regims_pis_pisos FOREIGN KEY (pis) REFERENCES pisos (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzant_historic_regims_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_simpatitzant_historic_regims_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- causes_conflicte
ALTER TABLE causes_conflicte
ADD CONSTRAINT fk_causes_conflicte_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_causes_conflicte_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_causes_conflicte_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_causes_conflicte_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_causes_conflicte_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- resolucions_conflicte
ALTER TABLE resolucions_conflicte
ADD CONSTRAINT fk_resolucions_conflicte_parent_id_causes_conflicte FOREIGN KEY (parent_id) REFERENCES causes_conflicte (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_resolucions_conflicte_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_resolucions_conflicte_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- conflictes
ALTER TABLE conflictes
ADD CONSTRAINT fk_conflictes_afiliada_afectada_afiliades FOREIGN KEY (afiliada_afectada) REFERENCES afiliades (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_bloc_afectat_blocs FOREIGN KEY (bloc_afectat) REFERENCES blocs (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_entramat_afectat_entramats FOREIGN KEY (entramat_afectat) REFERENCES entramats (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_delegada_users FOREIGN KEY (delegada) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_resolucio_resolucions_conflicte FOREIGN KEY (resolucio) REFERENCES resolucions_conflicte (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_causa_causes_conflicte FOREIGN KEY (causa) REFERENCES causes_conflicte (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_agrupacio_blocs_afectada_agrupacions_blocs FOREIGN KEY (agrupacio_blocs_afectada) REFERENCES agrupacions_blocs (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_no_afiliada_afectada_no_afiliades FOREIGN KEY (no_afiliada_afectada) REFERENCES no_afiliades (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_conflictes_simpatitzant_afectada_simpatitzants FOREIGN KEY (simpatitzant_afectada) REFERENCES simpatitzants (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- negociacions_conflicte
ALTER TABLE negociacions_conflicte
ADD CONSTRAINT fk_negociacions_conflicte_parent_id_conflictes FOREIGN KEY (parent_id) REFERENCES conflictes (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_negociacions_conflicte_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_negociacions_conflicte_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- afiliades_delegades_conflicte
ALTER TABLE afiliades_delegades_conflicte
ADD CONSTRAINT fk_afiliades_delegades_conflicte_parent_id_conflictes FOREIGN KEY (parent_id) REFERENCES conflictes (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_delegades_conflicte_child_id_afiliades FOREIGN KEY (child_id) REFERENCES afiliades (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_afiliades_delegades_conflicte_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- changes_log
ALTER TABLE changes_log
ADD CONSTRAINT fk_changes_log_user_users FOREIGN KEY ("user") REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- colaboradores_collectiu
ALTER TABLE colaboradores_collectiu
ADD CONSTRAINT fk_collaboradores_collectiu_parent_id_collectius FOREIGN KEY (parent_id) REFERENCES collectius (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_collaboradores_collectiu_child_id_users FOREIGN KEY (child_id) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_collaboradores_collectiu_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- assessoraments
ALTER TABLE assessoraments
ADD CONSTRAINT fk_assessoraments_afiliada_afiliades FOREIGN KEY (afiliada) REFERENCES afiliades (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessoraments_tipus_tipus_assessoraments FOREIGN KEY (tipus) REFERENCES tipus_assessoraments (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessoraments_tecnica_tecniques FOREIGN KEY (tecnica) REFERENCES tecniques (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessoraments_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessoraments_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessoraments_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessoraments_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessoraments_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessoraments_resultat_resultats_assessoraments FOREIGN KEY (resultat) REFERENCES resultats_assessoraments (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessoraments_no_afiliada_no_afiliades FOREIGN KEY (no_afiliada) REFERENCES no_afiliades (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- resultats_assessoraments
ALTER TABLE resultats_assessoraments
ADD CONSTRAINT fk_resultats_assessoraments_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_resultats_assessoraments_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_resultats_assessoraments_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_resultats_assessoraments_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_resultats_assessoraments_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- tipus_assessoraments
ALTER TABLE tipus_assessoraments
ADD CONSTRAINT fk_tipus_assessoraments_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_assessoraments_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_assessoraments_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_assessoraments_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_assessoraments_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- tecniques
ALTER TABLE tecniques
ADD CONSTRAINT fk_tecniques_especialitat_especialitats FOREIGN KEY (especialitat) REFERENCES especialitats (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tecniques_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tecniques_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tecniques_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tecniques_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tecniques_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- especialitats
ALTER TABLE especialitats
ADD CONSTRAINT fk_especialitats_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_especialitats_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_especialitats_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_especialitats_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_especialitats_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- assessorament_documents
ALTER TABLE assessorament_documents
ADD CONSTRAINT fk_assessorament_documents_parent_id_assessoraments FOREIGN KEY (parent_id) REFERENCES assessoraments (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessorament_documents_document_medias FOREIGN KEY (document) REFERENCES medias (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessorament_documents_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_assessorament_documents_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- medias
ALTER TABLE medias
ADD CONSTRAINT fk_medias_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_medias_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_medias_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_medias_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_medias_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- domiciliacions
ALTER TABLE domiciliacions
ADD CONSTRAINT fk_domiciliacions_fitxer_medias FOREIGN KEY (fitxer) REFERENCES medias (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_domiciliacions_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_domiciliacions_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_domiciliacions_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_domiciliacions_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_domiciliacions_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- directius_empresa
ALTER TABLE directius_empresa
ADD CONSTRAINT fk_directius_empresa_parent_id_empreses FOREIGN KEY (parent_id) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_directius_empresa_child_id_directius FOREIGN KEY (child_id) REFERENCES directius (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_directius_empresa_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- directius
ALTER TABLE directius
ADD CONSTRAINT fk_directius_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_directius_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_directius_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_directius_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_directius_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- entramats
ALTER TABLE entramats
ADD CONSTRAINT fk_entramats_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_entramats_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_entramats_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_entramats_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_entramats_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- pisos_entramat
ALTER TABLE pisos_entramat
ADD CONSTRAINT fk_pisos_entramat_parent_id_entramats FOREIGN KEY (parent_id) REFERENCES entramats (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_pisos_entramat_child_id_pisos FOREIGN KEY (child_id) REFERENCES pisos (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_pisos_entramat_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- sollicituds
ALTER TABLE sollicituds
ADD CONSTRAINT fk_sollicituds_origen_afiliacio_origens_afiliacio FOREIGN KEY (origen_afiliacio) REFERENCES origens_afiliacio (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_sollicituds_municipi_municipis FOREIGN KEY (municipi) REFERENCES municipis (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_sollicituds_estat_pis_estats_habitatge FOREIGN KEY (estat_pis) REFERENCES estats_habitatge (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_sollicituds_api_empreses FOREIGN KEY (api) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_sollicituds_propietat_empreses FOREIGN KEY (propietat) REFERENCES empreses (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_sollicituds_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_sollicituds_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_sollicituds_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_sollicituds_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_sollicituds_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_sollicituds_seccio_sindical_seccions_sindicals FOREIGN KEY (seccio_sindical) REFERENCES seccions_sindicals (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- servei_juridic_documents
ALTER TABLE servei_juridic_documents
ADD CONSTRAINT fk_servei_juridic_documents_parent_id_serveis_juridics FOREIGN KEY (parent_id) REFERENCES serveis_juridics (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_servei_juridic_documents_document_medias FOREIGN KEY (document) REFERENCES medias (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_servei_juridic_documents_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_servei_juridic_documents_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- serveis_juridics
ALTER TABLE serveis_juridics
ADD CONSTRAINT fk_serveis_juridics_afiliada_afiliades FOREIGN KEY (afiliada) REFERENCES afiliades (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_serveis_juridics_tipus_tipus_serveis_juridics FOREIGN KEY (tipus) REFERENCES tipus_serveis_juridics (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_serveis_juridics_tecnica_tecniques FOREIGN KEY (tecnica) REFERENCES tecniques (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_serveis_juridics_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_serveis_juridics_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_serveis_juridics_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_serveis_juridics_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_serveis_juridics_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- tipus_serveis_juridics
ALTER TABLE tipus_serveis_juridics
ADD CONSTRAINT fk_tipus_serveis_juridics_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_serveis_juridics_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_serveis_juridics_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_serveis_juridics_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_serveis_juridics_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- tipus_sseguiment
ALTER TABLE tipus_sseguiment
ADD CONSTRAINT fk_tipus_sseguiment_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_sseguiment_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_sseguiment_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_sseguiment_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_tipus_sseguiment_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- seccions_sindicals
ALTER TABLE seccions_sindicals
ADD CONSTRAINT fk_seccions_sindicals_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_seccions_sindicals_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_seccions_sindicals_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_seccions_sindicals_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_seccions_sindicals_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- origens_afiliacio
ALTER TABLE origens_afiliacio
ADD CONSTRAINT fk_origens_afiliacio_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_origens_afiliacio_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_origens_afiliacio_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_origens_afiliacio_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_origens_afiliacio_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- collectius
ALTER TABLE collectius
ADD CONSTRAINT fk_collectius_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_collectius_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_collectius_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_collectius_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_collectius_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- options
-- Already has a unique(section, option_key) constraint.

-- import_templates
-- No FKs.

-- patterns, changes_log
ALTER TABLE patterns
ADD CONSTRAINT fk_patterns_owner_user_users FOREIGN KEY (owner_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_patterns_owner_group_groups FOREIGN KEY (owner_group) REFERENCES "groups" (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_patterns_create_user_users FOREIGN KEY (create_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_patterns_update_user_users FOREIGN KEY (update_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
ADD CONSTRAINT fk_patterns_delete_user_users FOREIGN KEY (delete_user) REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE changes_log
ADD CONSTRAINT fk_changes_log_user_users FOREIGN KEY ("user") REFERENCES users (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ==========================
-- END FOREIGN KEYS AND INDEXES
-- ==========================