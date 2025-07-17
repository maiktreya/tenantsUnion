-- PostgreSQL version of the modernized schema for Sindicato Tenants Union
-- Version 2.0 - Simplified and optimized design

-- Create the schema
CREATE SCHEMA IF NOT EXISTS sindicato;

SET search_path TO sindicato;

-- =============================================
-- CORE INFRASTRUCTURE TABLES
-- =============================================

-- Simplified user management
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(150) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20) CHECK (phone ~ '^\+?[0-9\s\-\(\)]+$'),
    default_group_id INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(150) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(150) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles (id) ON DELETE CASCADE,
    permission VARCHAR(50) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    level VARCHAR(1),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (
        role_id,
        permission,
        operation
    )
);

CREATE TABLE user_groups (
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES groups (id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id)
);

CREATE TABLE user_roles (
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles (id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- =============================================
-- UNIFIED AUDIT SYSTEM
-- =============================================

CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    operation VARCHAR(10) NOT NULL CHECK (
        operation IN ('INSERT', 'UPDATE', 'DELETE')
    ),
    user_id INTEGER REFERENCES users (id),
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_audit_log_table_record ON audit_log (table_name, record_id);

CREATE INDEX idx_audit_log_user_time ON audit_log (user_id, changed_at);

CREATE INDEX idx_audit_log_changed_at ON audit_log (changed_at);

-- =============================================
-- LOCATION MANAGEMENT
-- =============================================

CREATE TABLE provinces (
    id SERIAL PRIMARY KEY,
    code VARCHAR(2) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE municipalities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    province_id INTEGER NOT NULL REFERENCES provinces (id),
    UNIQUE (name, province_id)
);

CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    street_name VARCHAR(200),
    street_number VARCHAR(20),
    floor VARCHAR(10),
    door VARCHAR(10),
    complement VARCHAR(50),
    postal_code VARCHAR(10),
    municipality_id INTEGER REFERENCES municipalities (id),
    google_place_id VARCHAR(100),
    full_address TEXT NOT NULL,
    coordinates POINT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_addresses_municipality ON addresses (municipality_id);

CREATE INDEX idx_addresses_postal_code ON addresses (postal_code);

CREATE INDEX idx_addresses_coordinates ON addresses USING GIST (coordinates);

-- =============================================
-- CONSOLIDATED LOOKUP SYSTEM
-- =============================================

CREATE TABLE lookup_categories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE lookup_values (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES lookup_categories (id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    name_es VARCHAR(200),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB,
    UNIQUE (category_id, code)
);

CREATE INDEX idx_lookup_values_category_active ON lookup_values (category_id, is_active);

-- Insert standard lookup categories
INSERT INTO
    lookup_categories (code, name)
VALUES (
        'housing_status',
        'Estats Habitatge'
    ),
    (
        'member_origin',
        'Origens Afiliació'
    ),
    (
        'participation_level',
        'Nivells Participació'
    ),
    (
        'conflict_cause',
        'Causes Conflicte'
    ),
    (
        'conflict_resolution',
        'Resolucions Conflicte'
    ),
    (
        'follow_up_type',
        'Tipus Seguiment'
    ),
    (
        'advisory_type',
        'Tipus Assessoraments'
    ),
    (
        'advisory_result',
        'Resultats Assessoraments'
    ),
    (
        'legal_service_type',
        'Tipus Serveis Jurídics'
    ),
    ('specialty', 'Especialitats');

-- =============================================
-- PERSON AND MEMBER MANAGEMENT
-- =============================================

CREATE TABLE persons (
    id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) UNIQUE CHECK (tax_id ~ '^[A-Z0-9]{8,20}$'),
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'X')),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    email VARCHAR(150),
    phone VARCHAR(20) CHECK (phone ~ '^\+?[0-9\s\-\(\)]+$'),
    wants_newsletter BOOLEAN DEFAULT FALSE,
    wants_communications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_persons_email ON persons (email);

CREATE INDEX idx_persons_tax_id ON persons (tax_id);

CREATE TABLE collectives (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    email VARCHAR(150) NOT NULL,
    phone VARCHAR(20),
    contact_person VARCHAR(200),
    contact_phone VARCHAR(20),
    allows_payments BOOLEAN DEFAULT FALSE,
    allows_advisories BOOLEAN DEFAULT FALSE,
    allows_direct_debit BOOLEAN DEFAULT FALSE,
    default_fee DECIMAL(10, 2),
    serial_prefix VARCHAR(8),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Unified members table (replacing afiliades, no_afiliades, simpatitzants)
CREATE TABLE members (
    id SERIAL PRIMARY KEY,
    person_id INTEGER NOT NULL REFERENCES persons(id),
    collective_id INTEGER REFERENCES collectives(id),
    member_type VARCHAR(20) NOT NULL CHECK (member_type IN ('affiliate', 'non_affiliate', 'sympathizer')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'inactive', 'suspended', 'cancelled')),

-- Membership dates
joined_at DATE NOT NULL, left_at DATE,

-- Origin and participation
origin_id INTEGER REFERENCES lookup_values (id),
participation_level_id INTEGER REFERENCES lookup_values (id),
union_section_id INTEGER REFERENCES union_sections (id),
commission_id INTEGER REFERENCES commissions (id),

-- Payment information (only for affiliates)
payment_method CHAR(1) CHECK (
    payment_method IN ('B', 'E', 'T')
), -- Bank, Cash, Transfer
payment_frequency CHAR(1) CHECK (
    payment_frequency IN ('M', 'T', 'S', 'A')
), -- Monthly, Trimestral, Semestral, Annual
bank_account VARCHAR(24) CHECK (
    bank_account ~ '^[A-Z]{2}[0-9]{22}$'
), -- IBAN format
fee_amount DECIMAL(10, 2),

-- Follow-up
last_followup_date DATE,
followup_type_id INTEGER REFERENCES lookup_values (id),

-- Additional info


notes TEXT,
    internal_comments TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_member_payment CHECK (
        (member_type = 'affiliate' AND payment_method IS NOT NULL) OR
        (member_type != 'affiliate' AND payment_method IS NULL)
    )
);

CREATE INDEX idx_members_person ON members (person_id);

CREATE INDEX idx_members_type_status ON members (member_type, status);

CREATE INDEX idx_members_collective ON members (collective_id);

CREATE INDEX idx_members_joined_at ON members (joined_at);

-- =============================================
-- HOUSING AND PROPERTY MANAGEMENT
-- =============================================

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    tax_id VARCHAR(20) UNIQUE CHECK (tax_id ~ '^[A-Z0-9]{8,20}$'),
    name VARCHAR(200) NOT NULL,
    is_api BOOLEAN DEFAULT FALSE,
    website VARCHAR(200),
    email VARCHAR(150),
    phone VARCHAR(20),
    address_id INTEGER REFERENCES addresses (id),
    network_id INTEGER REFERENCES property_networks (id),
    description TEXT,
    info_url VARCHAR(200),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_companies_network ON companies (network_id);

CREATE INDEX idx_companies_tax_id ON companies (tax_id);

CREATE TABLE property_networks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    address_id INTEGER NOT NULL REFERENCES addresses(id),

-- Building characteristics
status_id INTEGER REFERENCES lookup_values (id),
construction_year INTEGER CHECK (
    construction_year BETWEEN 1800 AND EXTRACT(
        YEAR
        FROM CURRENT_DATE
    )
),
total_homes INTEGER CHECK (total_homes >= 0),
total_shops INTEGER CHECK (total_shops >= 0),
has_vertical_property BOOLEAN,
has_elevator BOOLEAN,
has_parking BOOLEAN,
is_empty BOOLEAN DEFAULT FALSE,
empty_since DATE,
surface_m2 INTEGER CHECK (surface_m2 > 0),

-- Ownership
owner_company_id INTEGER REFERENCES companies (id),
api_company_id INTEGER REFERENCES companies (id),
ownership_last_updated DATE,

-- HPO (social housing) info


is_hpo BOOLEAN DEFAULT FALSE,
    hpo_end_date DATE,

    observations TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_buildings_address ON buildings (address_id);

CREATE INDEX idx_buildings_owner ON buildings (owner_company_id);

CREATE INDEX idx_buildings_api ON buildings (api_company_id);

CREATE TABLE building_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    owner_company_id INTEGER NOT NULL REFERENCES companies (id),
    api_company_id INTEGER REFERENCES companies (id),
    ownership_last_updated DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE building_group_members (
    building_group_id INTEGER NOT NULL REFERENCES building_groups (id) ON DELETE CASCADE,
    building_id INTEGER NOT NULL REFERENCES buildings (id) ON DELETE CASCADE,
    PRIMARY KEY (
        building_group_id,
        building_id
    )
);

CREATE TABLE housing_units (
    id SERIAL PRIMARY KEY,
    building_id INTEGER NOT NULL REFERENCES buildings(id),
    address_id INTEGER NOT NULL REFERENCES addresses(id),

-- Unit identification
floor VARCHAR(10), door VARCHAR(10),

-- Characteristics
status_id INTEGER REFERENCES lookup_values (id),
surface_m2 INTEGER CHECK (surface_m2 > 0),
bedrooms INTEGER CHECK (bedrooms >= 0),
has_habitability_cert BOOLEAN,
has_energy_cert BOOLEAN,
is_empty BOOLEAN DEFAULT FALSE,
empty_since DATE,

-- Ownership (if different from building)


owner_company_id INTEGER REFERENCES companies(id),
    api_company_id INTEGER REFERENCES companies(id),
    ownership_last_updated DATE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_housing_units_building ON housing_units (building_id);

CREATE INDEX idx_housing_units_owner ON housing_units (owner_company_id);

-- =============================================
-- RENTAL CONTRACTS AND REGIMES
-- =============================================

CREATE TABLE rental_contracts (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id),
    housing_unit_id INTEGER REFERENCES housing_units(id),

-- Contract type
regime CHAR(1) NOT NULL CHECK (
    regime IN ('P', 'L', 'H', 'A')
), -- Property, Rent, Room, Other
regime_other VARCHAR(50),

-- If not normalized address
is_normalized_address BOOLEAN DEFAULT TRUE, custom_address TEXT,

-- Contract details
start_date DATE NOT NULL,
is_indefinite BOOLEAN DEFAULT FALSE,
duration_months INTEGER CHECK (duration_months > 0),
extensions INTEGER DEFAULT 0,
monthly_rent DECIMAL(10, 2) CHECK (monthly_rent >= 0),

-- Household info
inhabitants INTEGER CHECK (inhabitants > 0),
monthly_income DECIMAL(10, 2) CHECK (monthly_income >= 0),

-- Status


is_active BOOLEAN DEFAULT TRUE,
    end_date DATE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_contract_dates CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT chk_regime_other CHECK (
        (regime = 'A' AND regime_other IS NOT NULL) OR
        (regime != 'A' AND regime_other IS NULL)
    )
);

CREATE INDEX idx_rental_contracts_member ON rental_contracts (member_id);

CREATE INDEX idx_rental_contracts_housing ON rental_contracts (housing_unit_id);

CREATE INDEX idx_rental_contracts_active ON rental_contracts (is_active);

-- =============================================
-- UNION ORGANIZATION
-- =============================================

CREATE TABLE union_sections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    postal_codes TEXT[], -- Array of postal codes
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE commissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- CONFLICTS MANAGEMENT
-- =============================================

CREATE TABLE conflicts (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) NOT NULL CHECK (status IN ('open', 'hibernating', 'closed')),
    scope CHAR(1) NOT NULL CHECK (scope IN ('I', 'C', 'B')), -- Individual, Collective, Building

-- Affected entities (only one should be set based on scope)
affected_member_id INTEGER REFERENCES members (id),
affected_building_id INTEGER REFERENCES buildings (id),
affected_building_group_id INTEGER REFERENCES building_groups (id),
affected_network_id INTEGER REFERENCES property_networks (id),

-- Conflict details
cause_id INTEGER NOT NULL REFERENCES lookup_values (id),
delegate_user_id INTEGER REFERENCES users (id),

-- Important dates
opened_at DATE NOT NULL,
last_assembly_at DATE,
hibernated_at DATE,
closed_at DATE,
next_eviction_at DATE,

-- Actions taken (using JSONB for flexibility)
actions_taken JSONB DEFAULT '{}',

-- Resolution


resolution_id INTEGER REFERENCES lookup_values(id),
    resolution_result CHAR(1) CHECK (resolution_result IN ('W', 'L', 'P')), -- Win, Loss, Partial

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_conflict_scope CHECK (
        (scope = 'I' AND affected_member_id IS NOT NULL) OR
        (scope = 'C' AND affected_building_id IS NOT NULL) OR
        (scope = 'B' AND (affected_building_group_id IS NOT NULL OR affected_network_id IS NOT NULL))
    )
);

CREATE INDEX idx_conflicts_status ON conflicts (status);

CREATE INDEX idx_conflicts_member ON conflicts (affected_member_id);

CREATE INDEX idx_conflicts_building ON conflicts (affected_building_id);

CREATE INDEX idx_conflicts_opened_at ON conflicts (opened_at);

CREATE TABLE conflict_delegates (
    conflict_id INTEGER NOT NULL REFERENCES conflicts (id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES members (id),
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (conflict_id, member_id)
);

CREATE TABLE conflict_negotiations (
    id SERIAL PRIMARY KEY,
    conflict_id INTEGER NOT NULL REFERENCES conflicts (id),
    negotiation_date DATE NOT NULL,
    status TEXT NOT NULL,
    tasks TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conflict_negotiations_conflict ON conflict_negotiations (conflict_id);

-- =============================================
-- ADVISORY AND LEGAL SERVICES
-- =============================================

CREATE TABLE technicians (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL,
    phone VARCHAR(20),
    specialty_id INTEGER NOT NULL REFERENCES lookup_values (id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE advisories (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    type_id INTEGER NOT NULL REFERENCES lookup_values(id),
    technician_id INTEGER REFERENCES technicians(id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),

-- Dates
contact_date DATE, advisory_date DATE, completion_date DATE,

-- Details


description TEXT,
    internal_comments TEXT,
    result_id INTEGER REFERENCES lookup_values(id),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_advisories_member ON advisories (member_id);

CREATE INDEX idx_advisories_technician ON advisories (technician_id);

CREATE INDEX idx_advisories_status ON advisories (status);

CREATE TABLE legal_services (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members (id),
    type_id INTEGER NOT NULL REFERENCES lookup_values (id),
    technician_id INTEGER REFERENCES technicians (id),
    status VARCHAR(20) NOT NULL CHECK (
        status IN (
            'pending',
            'in_progress',
            'completed',
            'cancelled'
        )
    ),
    service_date DATE,
    price DECIMAL(10, 2),
    description TEXT,
    internal_comments TEXT,
    result CHAR(1) CHECK (
        result IN ('W', 'L', 'P', 'O')
    ), -- Win, Loss, Partial, Other
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_legal_services_member ON legal_services (member_id);

CREATE INDEX idx_legal_services_technician ON legal_services (technician_id);

-- =============================================
-- DOCUMENT MANAGEMENT
-- =============================================

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(400) NOT NULL,
    file_hash VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size > 0),
    is_public BOOLEAN DEFAULT FALSE,

-- For images


is_image BOOLEAN DEFAULT FALSE,
    image_width INTEGER,
    image_height INTEGER,

    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_hash ON documents (file_hash);

CREATE INDEX idx_documents_uploaded_by ON documents (uploaded_by);

-- Polymorphic document associations
CREATE TABLE document_associations (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (
        document_id,
        entity_type,
        entity_id
    )
);

CREATE INDEX idx_document_associations_entity ON document_associations (entity_type, entity_id);

-- =============================================
-- FINANCIAL MANAGEMENT
-- =============================================

CREATE TABLE direct_debit_batches (
    id SERIAL PRIMARY KEY,
    issue_date DATE NOT NULL,
    file_document_id INTEGER REFERENCES documents (id),
    total_amount DECIMAL(12, 2),
    total_receipts INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE member_receipts (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members (id),
    batch_id INTEGER REFERENCES direct_debit_batches (id),
    amount DECIMAL(10, 2) NOT NULL,
    concept VARCHAR(200),
    due_date DATE NOT NULL,
    paid_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_member_receipts_member ON member_receipts (member_id);

CREATE INDEX idx_member_receipts_batch ON member_receipts (batch_id);

CREATE INDEX idx_member_receipts_status ON member_receipts (status);

-- =============================================
-- APPLICATION CONFIGURATION
-- =============================================

CREATE TABLE app_settings (
    id SERIAL PRIMARY KEY,
    section VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    description TEXT,
    UNIQUE (section, key)
);

CREATE TABLE user_preferences (
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    page_code VARCHAR(100) NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    PRIMARY KEY (
        user_id,
        page_code,
        preference_key
    )
);

-- =============================================
-- SUPPORT TABLES
-- =============================================

CREATE TABLE import_templates (
    id SERIAL PRIMARY KEY,
    import_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    content TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE application_forms (
    id SERIAL PRIMARY KEY,
    form_type VARCHAR(20) NOT NULL DEFAULT 'membership',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

-- All form data stored as JSONB for flexibility
form_data JSONB NOT NULL,

-- Processed results


processed_at TIMESTAMP,
    processed_by INTEGER REFERENCES users(id),
    processing_notes TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_application_forms_status ON application_forms (status);

CREATE INDEX idx_application_forms_type ON application_forms (form_type);

-- =============================================
-- VIEWS FOR BACKWARD COMPATIBILITY
-- =============================================

-- Create view to mimic old afiliades table structure
CREATE OR REPLACE VIEW vw_afiliades AS
SELECT
    m.id,
    p.tax_id AS cif,
    p.gender AS genere,
    p.first_name AS nom,
    p.last_name AS cognoms,
    p.email,
    p.phone AS telefon,
    p.wants_newsletter AS butlleti,
    m.status,
    m.joined_at AS data_alta,
    m.left_at AS data_baixa,
    lo.name AS origen_afiliacio,
    lp.name AS nivell_participacio,
    c.name AS comissio,
    m.payment_method AS forma_pagament,
    m.payment_frequency AS frequencia_pagament,
    m.bank_account AS compte_corrent,
    m.fee_amount AS quota,
    rc.regime AS regim,
    rc.regime_other AS regim_altres,
    CASE
        WHEN rc.is_normalized_address THEN a.full_address
        ELSE rc.custom_address
    END AS adreca,
    a.postal_code AS codi_postal,
    mun.name AS municipi,
    prov.name AS provincia,
    col.name AS collectiu,
    rc.start_date AS data_inici_contracte,
    rc.duration_months AS durada_contracte,
    rc.monthly_rent AS renda_contracte,
    rc.inhabitants AS num_habitants,
    rc.monthly_income AS ingressos_mensuals,
    us.name AS seccio_sindical
FROM
    members m
    JOIN persons p ON m.person_id = p.id
    LEFT JOIN lookup_values lo ON m.origin_id = lo.id
    LEFT JOIN lookup_values lp ON m.participation_level_id = lp.id
    LEFT JOIN commissions c ON m.commission_id = c.id
    LEFT JOIN rental_contracts rc ON rc.member_id = m.id
    AND rc.is_active = TRUE
    LEFT JOIN housing_units hu ON rc.housing_unit_id = hu.id
    LEFT JOIN addresses a ON COALESCE(hu.address_id, hu.building_id) = a.id
    LEFT JOIN municipalities mun ON a.municipality_id = mun.id
    LEFT JOIN provinces prov ON mun.province_id = prov.id
    LEFT JOIN collectives col ON m.collective_id = col.id
    LEFT JOIN union_sections us ON m.union_section_id = us.id
WHERE
    m.member_type = 'affiliate';

-- =============================================
-- AUDIT TRIGGER FUNCTION
-- =============================================

CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_user_id INTEGER;
    old_values JSONB;
    new_values JSONB;
BEGIN
    -- Get current user ID from session variable (set by application)
    audit_user_id := current_setting('app.current_user_id', TRUE)::INTEGER;

    IF TG_OP = 'DELETE' THEN
        old_values := to_jsonb(OLD);
        new_values := NULL;

        INSERT INTO audit_log (table_name, record_id, operation, user_id, old_values, new_values)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, audit_user_id, old_values, new_values);

        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        old_values := to_jsonb(OLD);
        new_values := to_jsonb(NEW);

        -- Only log if there are actual changes
        IF old_values != new_values THEN
            INSERT INTO audit_log (table_name, record_id, operation, user_id, old_values, new_values)
            VALUES (TG_TABLE_NAME, NEW.id, TG_OP, audit_user_id, old_values, new_values);
        END IF;

        -- Update the updated_at timestamp
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        new_values := to_jsonb(NEW);

        INSERT INTO audit_log (table_name, record_id, operation, user_id, old_values, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, audit_user_id, NULL, new_values);

        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- APPLY AUDIT TRIGGERS TO KEY TABLES
-- =============================================

-- List of tables that need audit trails
DO $$
DECLARE
    t text;
    tables text[] := ARRAY[
        'members', 'persons', 'rental_contracts', 'conflicts',
        'buildings', 'housing_units', 'companies', 'advisories',
        'legal_services', 'direct_debit_batches'
    ];
BEGIN
    FOREACH t IN ARRAY tables
    LOOP
        EXECUTE format('
            CREATE TRIGGER audit_trigger_%I
            AFTER INSERT OR UPDATE OR DELETE ON %I
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_function()',
            t, t);
    END LOOP;
END $$;

-- =============================================
-- USEFUL INDEXES FOR PERFORMANCE
-- =============================================

-- Full text search on persons
CREATE INDEX idx_persons_fulltext ON persons USING gin (
    to_tsvector (
        'spanish',
        first_name || ' ' || COALESCE(last_name, '')
    )
);

-- Partial indexes for active records
CREATE INDEX idx_members_active ON members (person_id)
WHERE
    status = 'active';

CREATE INDEX idx_buildings_empty ON buildings (id)
WHERE
    is_empty = TRUE;

CREATE INDEX idx_conflicts_open ON conflicts (id)
WHERE
    status = 'open';

-- =============================================
-- SAMPLE DATA MIGRATION HELPERS
-- =============================================

-- Helper function to migrate from old schema
CREATE OR REPLACE FUNCTION migrate_lookup_value(
    p_category_code VARCHAR,
    p_old_name VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    v_category_id INTEGER;
    v_value_id INTEGER;
BEGIN
    SELECT id INTO v_category_id FROM lookup_categories WHERE code = p_category_code;

    INSERT INTO lookup_values (category_id, code, name)
    VALUES (v_category_id, LOWER(REPLACE(p_old_name, ' ', '_')), p_old_name)
    ON CONFLICT (category_id, code) DO UPDATE SET name = EXCLUDED.name
    RETURNING id INTO v_value_id;

    RETURN v_value_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- PERMISSIONS AND ROW LEVEL SECURITY (RLS)
-- =============================================

-- Enable RLS on sensitive tables
ALTER TABLE members ENABLE ROW LEVEL SECURITY;

ALTER TABLE persons ENABLE ROW LEVEL SECURITY;

ALTER TABLE rental_contracts ENABLE ROW LEVEL SECURITY;

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (customize based on your needs)
CREATE POLICY members_view_policy ON members
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_groups ug
            WHERE ug.user_id = current_setting('app.current_user_id', TRUE)::INTEGER
            AND ug.group_id IN (1, 2, 3) -- Admin groups
        )
        OR id = current_setting('app.current_user_id', TRUE)::INTEGER
    );

-- =============================================
-- MAINTENANCE PROCEDURES
-- =============================================

-- Procedure to clean up old audit logs
CREATE OR REPLACE PROCEDURE cleanup_audit_logs(
    p_days_to_keep INTEGER DEFAULT 365
)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM audit_log
    WHERE changed_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep;

    RAISE NOTICE 'Cleaned up audit logs older than % days', p_days_to_keep;
END;
$$;

-- Function to get member statistics
CREATE OR REPLACE FUNCTION get_member_statistics()
RETURNS TABLE (
    member_type VARCHAR(20),
    status VARCHAR(20),
    count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT m.member_type, m.status, COUNT(*)
    FROM members m
    GROUP BY m.member_type, m.status
    ORDER BY m.member_type, m.status;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- FINAL CLEANUP AND OPTIMIZATION
-- =============================================

-- Update table statistics
ANALYZE;

-- Create extension for better text search if needed
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Add comment documentation
COMMENT ON SCHEMA sindicato IS 'Sindicato Tenants Union Database Schema v2.0';

COMMENT ON
TABLE members IS 'Unified table for all member types (affiliates, non-affiliates, sympathizers)';

COMMENT ON
TABLE audit_log IS 'Centralized audit trail for all database changes';

COMMENT ON
TABLE lookup_values IS 'Configurable lookup values replacing multiple type tables';