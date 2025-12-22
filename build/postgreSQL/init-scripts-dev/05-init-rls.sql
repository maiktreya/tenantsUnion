-- =====================================================================
-- 1. BASE PERMISSIONS (Re-applying to be safe)
-- =====================================================================
GRANT USAGE ON SCHEMA sindicato_inq TO web_anon, web_user;
GRANT ALL ON ALL TABLES IN SCHEMA sindicato_inq TO web_user;
GRANT SELECT ON ALL TABLES IN SCHEMA sindicato_inq TO web_anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sindicato_inq TO web_user;

GRANT web_anon TO app_user;
GRANT web_user TO app_user;

-- =====================================================================
-- 2. EMERGENCY FIX: RESTORE LOGIN
-- =====================================================================
-- We explicitly DISABLE security on 'usuarios' so the login function can 
-- read it again without being blocked.
ALTER TABLE sindicato_inq.usuarios DISABLE ROW LEVEL SECURITY;

-- =====================================================================
-- 3. POLICIES (Fixed Logic, applied only where safe)
-- =====================================================================

-- BLOCK A: Sensitive Tables (Afiliadas, Facturacion)
DO $$  
DECLARE
  t text;
  tables text[] := ARRAY['afiliadas', 'facturacion'];
BEGIN
  FOREACH t IN ARRAY tables
  LOOP
      -- You WANTED security here, so we enable it.
      EXECUTE format('ALTER TABLE sindicato_inq.%I ENABLE ROW LEVEL SECURITY', t);

      -- Admin (ALL)
      EXECUTE format('DROP POLICY IF EXISTS admin_all ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY admin_all ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'')', t, t);
     
      -- Gestor (READ ONLY)
      EXECUTE format('DROP POLICY IF EXISTS gestor_read ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY gestor_read ON sindicato_inq.%I FOR SELECT TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''gestor'')', t, t);
  END LOOP;
END
$$;

-- BLOCK B: General Data (Pisos, Bloques, etc)
-- Note: We EXCLUDED 'usuarios' from this list to prevent the login crash.
DO $$  
DECLARE
  t text;
  tables text[] := ARRAY['afiliadas', 'pisos', 'bloques', 'empresas', 'entramado_empresas'];
BEGIN
  FOREACH t IN ARRAY tables
  LOOP
       -- Enable RLS so the policies actually work
      EXECUTE format('ALTER TABLE sindicato_inq.%I ENABLE ROW LEVEL SECURITY', t);

      -- Admin (ALL) - Ensure Admin is never locked out
      EXECUTE format('DROP POLICY IF EXISTS admin_gen ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY admin_gen ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'')', t, t);

      -- Actas (READ ONLY) - Fixed name to 'actas_read' so it doesn't overwrite
      EXECUTE format('DROP POLICY IF EXISTS actas_read ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY actas_read ON sindicato_inq.%I FOR SELECT TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''actas'')', t, t);
  END LOOP;
END
$$;

-- BLOCK C: Conflicts (Full Access for Actas & Gestor)
DO $$  
DECLARE
  t text;
  tables text[] := ARRAY['conflictos', 'diario_conflictos'];
BEGIN
  FOREACH t IN ARRAY tables
  LOOP
      EXECUTE format('ALTER TABLE sindicato_inq.%I ENABLE ROW LEVEL SECURITY', t);

      -- Admin (ALL)
      EXECUTE format('DROP POLICY IF EXISTS admin_conf ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY admin_conf ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'')', t, t);

      -- Actas (FULL) - Fixed name to 'actas_full' to avoid collision
      EXECUTE format('DROP POLICY IF EXISTS actas_full ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY actas_full ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''actas'')', t, t);

      -- Gestor (FULL) - Fixed name to 'gestor_full' to avoid collision
      EXECUTE format('DROP POLICY IF EXISTS gestor_full ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY gestor_full ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''gestor'')', t, t);
  END LOOP;
END
$$;