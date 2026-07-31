-- =====================================================================
-- 1. BASE PERMISSIONS (Re-applying to be safe)
-- =====================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'web_anon') THEN
        CREATE ROLE web_anon nologin;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'web_user') THEN
        CREATE ROLE web_user nologin;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA sindicato_inq TO web_anon, web_user;
GRANT ALL ON ALL TABLES IN SCHEMA sindicato_inq TO web_user;
GRANT SELECT ON ALL TABLES IN SCHEMA sindicato_inq TO web_anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sindicato_inq TO web_user;

-- =====================================================================
-- 1b. PUBLIC SIGNUP GRANTS (formulario /join)
-- =====================================================================
-- web_anon needs table-level INSERT and UPDATE on afiliadas to support the
-- anonymous self-signup form (build/niceGUI/views/public_form.py). SELECT
-- is already covered by the global grant in section 1 and is gated at the
-- row level by the anon_read_signup policy (see section 3b), which hides
-- real members and exposes only the 'Bienvenida' pre-affiliation bucket.
-- INSERT and UPDATE are NOT covered by the global grant (SELECT-only), so
-- they must be granted explicitly here for the form's create and re-submit
-- / correction paths to work (the UPDATE branch previously returned 42501).
GRANT INSERT, UPDATE ON sindicato_inq.afiliadas TO web_anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sindicato_inq TO web_anon;

-- N.B. These role memberships are LOAD-BEARING for PostgREST, NOT redundant:
-- PostgREST connects as app_user and, per request, issues SET ROLE to the
-- JWT 'role' claim (web_user) or to web_anon (unsigned requests). SET ROLE
-- requires app_user to be a member of the target role — remove these and
-- every authenticated and anonymous API call will fail with permission denied.
GRANT web_anon TO app_user;
GRANT web_user TO app_user;

-- =====================================================================
-- 2. LOGIN ENDPOINT — rpc_login (SECURITY DEFINER) + usuarios / usuario_credenciales RLS
-- =====================================================================
-- The previous workaround DISABLED RLS on `usuarios` so the unauthenticated
-- login flow could SELECT it — which also let anonymous clients enumerate
-- every alias/email (and the global SELECT grant also reached
-- `usuario_credenciales`, leaking every bcrypt hash). That is now closed:
--
--   * Login goes through SECURITY DEFINER function `rpc_login` (defined in
--     02-init-plpgsql_functions.sql — created BEFORE this script runs, per
--     docker-entrypoint alphabetical ordering). It verifies bcrypt
--     server-side via pgcrypto's crypt() and returns
--     (user_id, alias, roles[]) on success, or empty on any failure.
--   * web_anon has EXECUTE on rpc_login, so unauthenticated callers can
--     continue to log in via POST /rpc/rpc_login. It has no other access
--     to the credentials table.
--   * web_user access is RESTORED at the row level by the self-row
--     policies below (each user can SELECT/UPDATE only their own
--     `usuarios` row and own `usuario_credenciales` row), preserving the
--     user_profile.py / user_management.py flows.
--   * admin retains full access via the admin_all FOR ALL policies
--     (used by UserManagementView for CRUD on users and credentials).

GRANT EXECUTE ON FUNCTION sindicato_inq.rpc_login(TEXT, TEXT) TO web_anon, web_user;

-- Revoke web_anon's per-table SELECT on these two sensitive tables
-- (this overrides the global `GRANT SELECT ON ALL TABLES ... TO web_anon`
-- in section 1 above for these two tables only).
REVOKE SELECT ON sindicato_inq.usuarios FROM web_anon;
REVOKE SELECT ON sindicato_inq.usuario_credenciales FROM web_anon;

ALTER TABLE sindicato_inq.usuarios            ENABLE ROW LEVEL SECURITY;
ALTER TABLE sindicato_inq.usuario_credenciales ENABLE ROW LEVEL SECURITY;

-- usuarios: admin (FOR ALL) — used by UserManagementView's CRUD on users.
DROP POLICY IF EXISTS admin_all ON sindicato_inq.usuarios;
CREATE POLICY admin_all ON sindicato_inq.usuarios
    FOR ALL TO web_user
    USING (current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'admin')
    WITH CHECK (current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'admin');

-- usuarios: self (SELECT) — used by user_profile.py to populate "Mi Perfil".
-- `sub` is the JWT subject, set to the numeric user id after the login
-- refactor (see build/niceGUI/auth/token_utils.py).
DROP POLICY IF EXISTS self_read ON sindicato_inq.usuarios;
CREATE POLICY self_read ON sindicato_inq.usuarios
    FOR SELECT TO web_user
    USING (id = NULLIF(current_setting('request.jwt.claims', true)::jsonb ->> 'sub', '')::int);

-- usuarios: self (UPDATE) — used by user_profile.py to save name/email
-- changes. WITH CHECK (id = sub) prevents privilege escalation by editing
-- the row's primary key.
DROP POLICY IF EXISTS self_update ON sindicato_inq.usuarios;
CREATE POLICY self_update ON sindicato_inq.usuarios
    FOR UPDATE TO web_user
    USING (id = NULLIF(current_setting('request.jwt.claims', true)::jsonb ->> 'sub', '')::int)
    WITH CHECK (id = NULLIF(current_setting('request.jwt.claims', true)::jsonb ->> 'sub', '')::int);

-- usuario_credenciales: admin (FOR ALL) — admin sets/updates any user's hash.
DROP POLICY IF EXISTS admin_all ON sindicato_inq.usuario_credenciales;
CREATE POLICY admin_all ON sindicato_inq.usuario_credenciales
    FOR ALL TO web_user
    USING (current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'admin')
    WITH CHECK (current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'admin');

-- usuario_credenciales: self (SELECT) — used by user_profile.py to read
-- the current hash for verification before a password change.
DROP POLICY IF EXISTS self_read ON sindicato_inq.usuario_credenciales;
CREATE POLICY self_read ON sindicato_inq.usuario_credenciales
    FOR SELECT TO web_user
    USING (usuario_id = NULLIF(current_setting('request.jwt.claims', true)::jsonb ->> 'sub', '')::int);

-- usuario_credenciales: self (UPDATE) — used by user_profile.py to write
-- a new hash after current-password verification.
DROP POLICY IF EXISTS self_update ON sindicato_inq.usuario_credenciales;
CREATE POLICY self_update ON sindicato_inq.usuario_credenciales
    FOR UPDATE TO web_user
    USING (usuario_id = NULLIF(current_setting('request.jwt.claims', true)::jsonb ->> 'sub', '')::int)
    WITH CHECK (usuario_id = NULLIF(current_setting('request.jwt.claims', true)::jsonb ->> 'sub', '')::int);

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
      -- 1. Mantenemos la seguridad RLS activa (El cortafuegos se enciende para ambas)
      EXECUTE format('ALTER TABLE sindicato_inq.%I ENABLE ROW LEVEL SECURITY', t);

      -- 2. Admin (ALL) - Permitimos acceso total al administrador en ambas tablas
      EXECUTE format('DROP POLICY IF EXISTS admin_all ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY admin_all ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'')', t, t);
       
      -- 3. Control específico por tabla
      IF t = 'afiliadas' THEN
          -- afiliadas is fully managed here (Block A) to avoid the previous
          -- duplication, where Block B re-enabled RLS and added a second,
          -- functionally-identical admin policy (admin_gen) plus actas_read.
          -- All afiliadas policies are consolidated in this branch:

          -- Gestor: SELECT only (gestor never writes afiliadas)
          EXECUTE format('DROP POLICY IF EXISTS gestor_read ON sindicato_inq.%I', t);
          EXECUTE format('CREATE POLICY gestor_read ON sindicato_inq.%I FOR SELECT TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''gestor'')', t, t);

          -- Actas: SELECT only, needed to resolve afiliada identity inside the
          -- conflicts module (actas never writes afiliadas). Previously created
          -- by Block B; moved here so afiliadas could be dropped from Block B.
          EXECUTE format('DROP POLICY IF EXISTS actas_read ON sindicato_inq.%I', t);
          EXECUTE format('CREATE POLICY actas_read ON sindicato_inq.%I FOR SELECT TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''actas'')', t, t);

          -- Drop the legacy admin_gen that Block B used to create on afiliadas
          -- (functionally identical to admin_all above). Cleans up databases
          -- that already ran the pre-dedup version of this script.
          EXECUTE format('DROP POLICY IF EXISTS admin_gen ON sindicato_inq.%I', t);
      ELSE
          -- facturacion: deny gestor by default (RLS enabled, no policy for gestor).
          EXECUTE format('DROP POLICY IF EXISTS gestor_read ON sindicato_inq.%I', t);
      END IF;
  END LOOP;
END
$$;
ALTER VIEW sindicato_inq.v_facturacion SET (security_invoker = true);

-- =====================================================================
-- 2b. VIEW HARDENING (security_invoker)
-- =====================================================================
-- Views run with the privileges/RLS of the INVOKER when security_invoker =
-- true. Without it, a view executes as its owner (app_user, the table
-- owner), which BYPASSES RLS — so any role with table-level SELECT
-- (including web_anon via the global grant in section 1) could read every
-- column the view joins, defeating all per-table RLS. v_facturacion was
-- already hardened; the three member-PII views below were not, leaking
-- afiliada contact info, addresses, and conflict details to anonymous
-- callers via direct PostgREST GET requests.
ALTER VIEW sindicato_inq.v_afiliadas_detalle SET (security_invoker = true);
ALTER VIEW sindicato_inq.v_conflictos_detalle SET (security_invoker = true);
ALTER VIEW sindicato_inq.v_conflictos_enhanced SET (security_invoker = true);

-- =====================================================================
-- 3b. PUBLIC SIGNUP POLICIES (formulario /join)
-- =====================================================================
-- The anonymous join form (build/niceGUI/views/public_form.py) performs a
-- SELECT-then-UPDATE-or-INSERT on afiliadas, all as web_anon:
--   1. SELECT by CIF to detect a previous submission,
--   2. UPDATE the existing pre-afiliada, or
--   3. INSERT a brand-new pre-afiliada.
-- All three operations are constrained to the 'Bienvenida' pre-affiliation
-- bucket (estado = 'Bienvenida'). Once an admin promotes a record to 'Alta'
-- or 'Baja', it leaves the anonymous-readable set and can no longer be
-- touched from /join — re-submissions are cleanly refused instead of
-- silently overwriting a real member. This also blocks forging of fully-
-- joined members (estado='Alta', afiliacion='Importado', arbitrary fees…)
-- via direct API calls that bypass the form, since WITH CHECK rejects any
-- row not in the 'Bienvenida' bucket.
--
-- Residual: anonymous clients CAN still enumerate the 'Bienvenida' bucket
-- (names/CIF/email/phone of pending signups — NOT addresses, which live in
-- pisos and are RLS-blocked for web_anon). This is the minimum exposure
-- required to make the self-service UPDATE work without a SECURITY DEFINER
-- RPC (audit item 3, deferred). Admins should promote signups promptly to
-- shrink this bucket.

-- SELECT: anon can only see pre-afiliadas still awaiting promotion.
DROP POLICY IF EXISTS anon_read_signup ON sindicato_inq.afiliadas;
CREATE POLICY anon_read_signup ON sindicato_inq.afiliadas
    FOR SELECT TO web_anon
    USING (estado = 'Bienvenida');

-- INSERT: only pre-affiliation rows.
DROP POLICY IF EXISTS anon_insert_afiliadas ON sindicato_inq.afiliadas;
CREATE POLICY anon_insert_afiliadas ON sindicato_inq.afiliadas
    FOR INSERT TO web_anon
    WITH CHECK (estado = 'Bienvenida');

-- UPDATE: only pre-affiliation rows, and the updated row must STAY in the
-- pre-affiliation bucket (cannot self-promote to 'Alta').
DROP POLICY IF EXISTS anon_update_afiliadas_signup ON sindicato_inq.afiliadas;
CREATE POLICY anon_update_afiliadas_signup ON sindicato_inq.afiliadas
    FOR UPDATE TO web_anon
    USING (estado = 'Bienvenida')
    WITH CHECK (estado = 'Bienvenida');

-- BLOCK B: General Data (Pisos, Bloques, etc)
-- Note: 'usuarios' is excluded (RLS DISABLED — see section 2) to keep the
-- login flow working. 'afiliadas' is excluded here too: it is fully managed
-- in Block A (admin_all + gestor_read + actas_read + signup policies) to
-- avoid the previous duplication where this block re-enabled RLS and added
-- a redundant admin_gen. The Block B tables below are the "general" lookup
-- tables (housing stock / corporate structure) shared by gestor and actas.
DO $$  
DECLARE
  t text;
  tables text[] := ARRAY['pisos', 'bloques', 'empresas', 'entramado_empresas'];
BEGIN
  FOREACH t IN ARRAY tables
  LOOP
       -- Enable RLS so the policies actually work
      EXECUTE format('ALTER TABLE sindicato_inq.%I ENABLE ROW LEVEL SECURITY', t);

      -- Admin (ALL) - Ensure Admin is never locked out.
      -- WITH CHECK (audit item #3c): admin's writes must also satisfy the
      -- same predicate so admin can't INSERT a row that would then be
      -- invisible to its own policy (closes an indirect FK-existence side
      -- channel for the general-data tables too).
      EXECUTE format('DROP POLICY IF EXISTS admin_gen ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY admin_gen ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'') WITH CHECK (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'')', t, t);

      -- Actas (READ ONLY)
      EXECUTE format('DROP POLICY IF EXISTS actas_read ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY actas_read ON sindicato_inq.%I FOR SELECT TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''actas'')', t, t);

      -- Gestor (READ ONLY) - needed so the member-PII views (v_afiliadas_detalle,
      -- v_conflictos_detalle, v_conflictos_enhanced) keep working for gestor
      -- once they are flipped to security_invoker=true (see section 2b).
      -- Without this, the pisos/bloques/empresas JOINs inside those views would
      -- be silently filtered to zero rows for gestor, hiding the address /
      -- propiedad / entramado columns in the UI. gestor already saw this data
      -- indirectly via the (previously RLS-bypassing) views; this policy makes
      -- the access explicit and RLS-enforced.
      EXECUTE format('DROP POLICY IF EXISTS gestor_read ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY gestor_read ON sindicato_inq.%I FOR SELECT TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''gestor'')', t, t);
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

      -- Admin (ALL) - WITH CHECK (audit item #3c) prevents admin from
      -- writing rows that would then be invisible to them (keeps the
      -- FOR ALL symmetric and closes the indirect FK-enumeration side
      -- channel where admin inserts a conflictos row pointing at an
      -- arbitrary afiliada_id).
      EXECUTE format('DROP POLICY IF EXISTS admin_conf ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY admin_conf ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'') WITH CHECK (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'')', t, t);

      -- Actas (FULL) - WITH CHECK for the same reason as admin_conf.
      EXECUTE format('DROP POLICY IF EXISTS actas_full ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY actas_full ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''actas'') WITH CHECK (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''actas'')', t, t);

      -- Gestor (FULL) - WITH CHECK for the same reason as admin_conf.
      EXECUTE format('DROP POLICY IF EXISTS gestor_full ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY gestor_full ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''gestor'') WITH CHECK (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''gestor'')', t, t);
  END LOOP;
END
$$;

-- =====================================================================
-- BLOCK D: Asesorias (audit item #3b)
-- =====================================================================
-- `asesorias` was previously missing from Blocks A/B/C — it had no RLS
-- and no admin-gated policy, so it inherited:
--   * GRANT SELECT ... TO web_anon  -> legal-advice cases (fecha_asesoria,
--     tipo_beneficiaria, resultado, afiliada_id) were anonymously readable.
--   * GRANT ALL ... TO web_user      -> any gestor/actas JWT could INSERT /
--     UPDATE / DELETE advisory records.
-- Now enabled with the same shape as Block C: admin full, actas/gestor full
-- (the asesorías module is worked by both roles — same as conflictos). All
-- FOR ALL policies carry WITH CHECK so writes can't target invisible rows.
DO $$
DECLARE
  t text;
  tables text[] := ARRAY['asesorias'];
BEGIN
  FOREACH t IN ARRAY tables
  LOOP
      EXECUTE format('ALTER TABLE sindicato_inq.%I ENABLE ROW LEVEL SECURITY', t);

      EXECUTE format('DROP POLICY IF EXISTS admin_conf ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY admin_conf ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'') WITH CHECK (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'')', t, t);

      EXECUTE format('DROP POLICY IF EXISTS actas_full ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY actas_full ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''actas'') WITH CHECK (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''actas'')', t, t);

      EXECUTE format('DROP POLICY IF EXISTS gestor_full ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY gestor_full ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''gestor'') WITH CHECK (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''gestor'')', t, t);
  END LOOP;
END
$$;

-- =====================================================================
-- BLOCK E: Reference / lookup tables (audit item #3d)
-- =====================================================================
-- Structural / lookup tables that previously had NO RLS and inherited the
-- global `GRANT ALL ... TO web_user`. That let any non-admin JWT
-- (gestor, actas) INSERT / UPDATE / DELETE roles, nodos, agrupaciones,
-- nodos_cp_mapping, and the new `provincias` table added in this same
-- workstream. They should be append-only reference data managed only by
-- admin (or maintained via ETL/db scripts).
--
-- NOTE: `usuario_roles` (the usuario_id → role_id join table) is
-- deliberately NOT in this block — it is the privilege graph, not
-- non-sensitive reference data, and gets its own Block F below with
-- stricter policies (admin-only writes, self-only reads, no anon).
--
-- The intent is read-only for everyone except admin. Implementation:
--   * ENABLE RLS so the table's existing grants are filtered by policy.
--   * admin_gen FOR ALL WITH CHECK (admin) — admin retains CRUD.
--   * reader FOR SELECT TO web_user — any authenticated user can read.
--   * reader_anon FOR SELECT TO web_anon — preserves the previous
--     anonymous-readable posture for non-sensitive lookup data. Without
--     this policy, ENABLE RLS would silently default-deny web_anon
--     (anonymous reads would stop working even though the global GRANT
--     SELECT is still in place — RLS overrides grants). Drop this
--     policy if you want to hide the lookups from anonymous callers.
--   * DML for non-admin is blocked by ABSENCE of a write policy (RLS
--     default-deny on writes), so no REVOKE is needed — the global
--     `GRANT ALL` is overridden by RLS: even though web_user can
--     technically `INSERT`, no INSERT policy matches, so the row write
--     is rejected.
DO $$
DECLARE
  t text;
  tables text[] := ARRAY['nodos', 'roles', 'agrupacion_bloques',
                          'nodos_cp_mapping', 'provincias'];
BEGIN
  FOREACH t IN ARRAY tables
  LOOP
      EXECUTE format('ALTER TABLE sindicato_inq.%I ENABLE ROW LEVEL SECURITY', t);

      -- Admin (ALL) with WITH CHECK so admin can't write a row that
      -- would then be invisible to this same policy.
      EXECUTE format('DROP POLICY IF EXISTS admin_gen ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY admin_gen ON sindicato_inq.%I FOR ALL TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'') WITH CHECK (current_setting(''request.jwt.claims'', true)::jsonb -> ''roles'' ? ''admin'')', t, t);

      -- Reader (SELECT) — any authenticated user. The roles claim check
      -- is intentionally permissive (the jwt has any 'roles' entry); we
      -- just need a policy so RLS doesn't default-deny the SELECT that
      -- the global grant already allows.
      EXECUTE format('DROP POLICY IF EXISTS reader ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY reader ON sindicato_inq.%I FOR SELECT TO web_user USING (current_setting(''request.jwt.claims'', true)::jsonb ? ''roles'')', t, t);

      -- Reader for anonymous callers — preserves the prior behaviour
      -- (lookups were anonymously readable before this RLS was enabled).
      -- REQUIRED: without it, ENABLE RLS would silently remove anonymous
      -- read access despite the global GRANT SELECT remaining in place.
      EXECUTE format('DROP POLICY IF EXISTS reader_anon ON sindicato_inq.%I', t);
      EXECUTE format('CREATE POLICY reader_anon ON sindicato_inq.%I FOR SELECT TO web_anon USING (true)', t, t);
  END LOOP;
END
$$;

-- =====================================================================
-- BLOCK F: usuario_roles (privilege-escalation prevention)
-- =====================================================================
-- `usuario_roles` (the usuario_id → role_id join table that determines who
-- is admin) was the one table still missing from all RLS blocks. Unlike
-- the Block E lookup tables (`roles`, `nodos`, etc.), this is NOT
-- non-sensitive reference data — it is the privilege graph itself.
--
-- Without RLS, the global `GRANT ALL ... TO web_user` from section 1 was
-- fully live on this table. Any authenticated user (regardless of role)
-- could call:
--     PATCH /usuario_roles?usuario_id=eq.<their_own_id>
--     {"role_id": <admin role's id>}
-- The `roles` table is readable via the Block E `reader` policy, so
-- discovering the admin role's id is trivial. The next rpc_login call
-- reads usuario_roles as SECURITY DEFINER (RLS-exempt) and faithfully
-- returns the forged role — the user gets an admin JWT. That is a
-- straight self-service privilege escalation to admin, not just a PII
-- leak.
--
-- Policies:
--   * admin_all FOR ALL WITH CHECK — admin retains CRUD (covers
--     user_management.py's role-assignment dialogs).
--   * self_read FOR SELECT — a user can see their own role assignment
--     (consistent with the self-row pattern on usuarios /
--     usuario_credenciales), but NOT other users' assignments.
--   * NO web_anon policy — deliberately default-deny. There is no
--     legitimate reason for an anonymous caller to enumerate which user
--     IDs hold which role, so reader_anon from Block E is intentionally
--     NOT mirrored here.
--
-- Login is unaffected: `rpc_login` reads `usuario_roles` as SECURITY
-- DEFINER (executes as app_user, the table owner — RLS-exempt without
-- FORCE ROW LEVEL SECURITY, which is never set in this codebase).
ALTER TABLE sindicato_inq.usuario_roles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS admin_all ON sindicato_inq.usuario_roles;
CREATE POLICY admin_all ON sindicato_inq.usuario_roles
    FOR ALL TO web_user
    USING (current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'admin')
    WITH CHECK (current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'admin');

DROP POLICY IF EXISTS self_read ON sindicato_inq.usuario_roles;
CREATE POLICY self_read ON sindicato_inq.usuario_roles
    FOR SELECT TO web_user
    USING (usuario_id = NULLIF(current_setting('request.jwt.claims', true)::jsonb ->> 'sub', '')::int);