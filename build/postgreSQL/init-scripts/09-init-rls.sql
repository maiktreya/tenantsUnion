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

-- Apply Admin and Gestor policies ONLY to the 2 specific tables declared
DO $$
DECLARE
    t text;
    tables text[] := ARRAY['afiliadas', 'facturacion'];
BEGIN
    FOREACH t IN ARRAY tables
    LOOP
        -- Enable RLS
        EXECUTE format('ALTER TABLE sindicato_inq.%I ENABLE ROW LEVEL SECURITY', t);

        -- Policy 1: Admins can do ANYTHING
        EXECUTE format('DROP POLICY IF EXISTS admin_all ON sindicato_inq.%I', t);
        EXECUTE format('CREATE POLICY admin_all ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'')', t, t);
        
        -- Policy 2: Gestors can READ everything
        EXECUTE format('DROP POLICY IF EXISTS gestor_read ON sindicato_inq.%I', t);
        EXECUTE format('CREATE POLICY gestor_read ON sindicato_inq.%I FOR SELECT TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''gestor'')', t, t);
    END LOOP;
END
$$;

-- Policy 3: "actas" role - SELECT specific tables
DO $$
DECLARE
    t text;
    tables text[] := ARRAY['afiliadas', 'pisos', 'bloques', 'usuarios', 'empresas', 'entramado_empresas'];
BEGIN
    FOREACH t IN ARRAY tables
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS toma_actas ON sindicato_inq.%I', t);
        EXECUTE format('CREATE POLICY toma_actas ON sindicato_inq.%I FOR SELECT TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''actas'')', t, t);
    END LOOP;
END
$$;

DO $$
DECLARE
    t text;
    tables text[] := ARRAY['conflictos', 'diario_conflictos'];
BEGIN
    FOREACH t IN ARRAY tables
    LOOP
        -- Policy 4: "actas" role - ALL permissions on conflict tables
        EXECUTE format('DROP POLICY IF EXISTS toma_actas ON sindicato_inq.%I', t);
        EXECUTE format('CREATE POLICY toma_actas ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''actas'')', t, t);

        -- Policy 5: "gestor" role - ALL permissions on conflict tables
        EXECUTE format('DROP POLICY IF EXISTS toma_actas ON sindicato_inq.%I', t);
        EXECUTE format('CREATE POLICY toma_actas ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''gestor'')', t, t);
    END LOOP;
END
$$;