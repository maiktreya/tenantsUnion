-----------------------------------------------------------------
-- Row Level Security (RLS). Create the Roles & Policies

-- 1. Create Roles  
-- 2. Grant Permissions to Schema
-- 3. Grant Permissions to Tables (The "Broad" Check)
-- 4. Switch the Authenticator (The Login User)

-----------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'web_anon') THEN
    CREATE ROLE web_anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'web_user') THEN
    CREATE ROLE web_user NOLOGIN;
  END IF;
END
$$;

-- 2. Grant Permissions to Schema
GRANT USAGE ON SCHEMA sindicato_inq TO web_anon, web_user;

-- 3. Grant Permissions to Tables (The "Broad" Check)
-- Allow web_user to touch tables; specific restrictions happen in Policies later.
GRANT ALL ON ALL TABLES IN SCHEMA sindicato_inq TO web_user;
GRANT SELECT ON ALL TABLES IN SCHEMA sindicato_inq TO web_anon; -- Optional: public read?
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sindicato_inq TO web_user;

-- 4. Switch the Authenticator (The Login User)
-- Ensure the user defined in your docker-compose POSTGRES_USER has permission to switch to these roles.
GRANT web_anon TO app_user; -- Assuming 'postgres' is your connection user
GRANT web_user TO app_user;


-- ===================================================================== 
-- Secure target tables with RLS
-- ===================================================================== 

ALTER TABLE sindicato_inq.afiliadas ENABLE ROW LEVEL SECURITY;
ALTER TABLE sindicato_inq.facturacion ENABLE ROW LEVEL SECURITY;
ALTER TABLE sindicato_inq.usuario_credenciales ENABLE ROW LEVEL SECURITY;

-- Policy 1: Admins can do ANYTHING
DROP POLICY IF EXISTS admin_all ON sindicato_inq.*;
CREATE POLICY admin_all ON sindicato_inq.*
    FOR ALL
    TO web_user
    USING (
        current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'admin'
    );

-- Policy 2: Gestors can READ everything but only UPDATE specific fields?
DROP POLICY IF EXISTS gestor_read ON sindicato_inq.*;
CREATE POLICY gestor_read ON sindicato_inq.*
    FOR SELECT
    TO web_user
    USING (
        current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'gestor'
    );

-- Policies 3 & 4: Policies associated to less privileged role "actas"
DROP POLICY IF EXISTS toma_actas ON sindicato_inq.*;
CREATE POLICY toma_actas ON sindicato_inq.afiliadas, 
                            sindicato_inq.pisos, 
                            sindicato_inq.bloques, 
                            sindicato_inq.usuarios, 
                            sindicato_inq.empresas, 
                            sindicato_inq.entramado_empresas
    FOR SELECT
    TO web_user
    USING (
        current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'actas'
    );

DROP POLICY IF EXISTS toma_actas ON sindicato_inq.afiliadas;
CREATE POLICY toma_actas ON sindicato_inq.conflictos, sindicato_inq.diario_conflictos
    FOR ALL
    TO web_user
    USING (
        current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'actas'
    );