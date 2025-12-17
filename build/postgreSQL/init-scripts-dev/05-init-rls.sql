-- 1. Create the Roles
CREATE ROLE web_anon NOLOGIN;
CREATE ROLE web_user NOLOGIN;

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


-- Example: Secure the 'afiliadas' table
ALTER TABLE sindicato_inq.afiliadas ENABLE ROW LEVEL SECURITY;

-- Policy 1: Admins can do ANYTHING
CREATE POLICY admin_all ON sindicato_inq.afiliadas
    FOR ALL
    TO web_user
    USING (
        current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'admin'
    );

-- Policy 2: Gestors can READ everything but only UPDATE specific fields?
-- (Postgres RLS is row-level, not column-level, but simple READ is easy)
CREATE POLICY gestor_read ON sindicato_inq.afiliadas
    FOR SELECT
    TO web_user
    USING (
        current_setting('request.jwt.claims', true)::jsonb -> 'roles' ? 'gestor'
    );

-- Policy 3: Allow users to see only their OWN row (if they are a 'tecnica' linked to a user)
-- Assuming you add a 'linked_user_id' to afiliadas or match via email
-- CREATE POLICY my_own_row ON ...