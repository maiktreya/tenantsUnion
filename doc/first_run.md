# Local Development Environment Setup (dev_run)

This guide explains how to run the application on your local machine for development and testing. This setup uses artificial data to protect privacy and exposes the application directly, without the production Nginx reverse proxy.

## 1. Environment Setup

Before running the application, configure your `.env` file for a development environment (copy `.env.example` to `.env` and adjust as needed). The dev profile does **not** read a custom `INIT_SCRIPTS_PATH` variable — the dev data seed is wired directly into `docker-compose-dev.yaml`, which bind-mounts `build/postgreSQL/init-scripts-dev/05-init-artificial_data.sql` on top of the empty production stub at `/docker-entrypoint-initdb.d/05-init-artificial_data.sql`.

What each relevant variable does:

- `DEV_MODE`: when non-empty, the `nicegui-app` volume is mounted `rw` so you can hot-reload Python source from the host; when blank it falls back to the more secure `ro` mount.
- `POSTGRES_USER` / `POSTGRES_DB` / `POSTGRES_DB_SCHEMA`: must match the values expected by `04-init-user_roles.sql` and the PostgREST URI in `docker-compose.yaml`.
- `PGRST_JWT_SECRET` / `NICEGUI_STORAGE_SECRET`: must be set to strong random values (the defaults baked into source are placeholders and will refuse to boot in hardened deployments).

## 2. Exposing ports externally

You have to force-overlay `docker-compose-dev.yaml` over `docker-compose.yaml` to get ports **5432 (PostgreSQL)**, **3001 (PostgREST — mapped to the container's internal 3000)** and **8081 (NiceGUI)** externally exposed (bear in mind nginx, in production, provides additional security layers).

## 3. Default Seed Credentials (CRITICAL SECURITY STEP)

The repo ships with three pre-hashed development users defined in `build/postgreSQL/init-scripts/04-init-user_roles.sql`. They are inserted automatically the first time the `db` container initializes an empty data directory — **no manual hash generation is required for local dev**.

| Alias | Role | Notes |
| --- | --- | --- |
| `sumate` | `admin` | Full CRUD on every table, user management, system administration. |
| `gestor` | `gestor` | Conflicts management, afiliadas importer, read-only views. |
| `actas` | `actas` | Conflicts module only. |

The bcrypt hashes for these accounts are committed in plain sight inside `04-init-user_roles.sql` (`$2b$12$…`). They are **intentionally public** so anyone can boot the dev stack, and they must **never** reach a production deployment. Change them before exposing any instance to the internet.

### Rotating the dev credentials (optional, recommended before any shared demo)

If you want to replace the committed hashes with your own, regenerate them locally and patch the `INSERT INTO usuario_credenciales` block in `build/postgreSQL/init-scripts/04-init-user_roles.sql`:

```bash
pip install passlib bcrypt
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt'], deprecated='auto').hash('YourNewStrongPassword!'))"
```

Paste the resulting `$2b$12$…` string into the SQL file, then tear down and recreate the `db` container so the init scripts re-run on an empty data dir (see Section 8). Do **not** commit a real production hash — by convention this file holds only throwaway dev credentials.

### For production

Production instances must not rely on `04-init-user_roles.sql` at all. Either:

1. Mount a replacement `04-init-user_roles.sql` with real admin hashes via a host-side secret, or
2. Bootstrap the first admin through a one-off `psql` session after first boot, then rotate immediately from the **Mi Perfil** (My Profile) page.

## 4. Running the Application

With the `.env` file configured and credentials set up, you can start the application using the Frontend profile. This profile includes the database, the API, and the NiceGUI application, but excludes the Nginx and Certbot services.

Execute the following command from the root of the project:

```bash
 # for the standard fully dockerized dev environment
 docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d

 # if you have a local python environment with the requirements installed you could run the frontend directly from source
 docker compose -f docker-compose.yaml -f docker-compose-dev.yaml up -d && python build/niceGUI/main.py

 # for allowing an environment with a local postgreSQL instance with hot reload and monitor logs
 docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d --renew-anon-volumes && docker logs --follow tenantsunion-db-1
```

This command will:

- Build the necessary Docker images if they don't exist.

- Start the **db**, **server**, and **nicegui-app** services in the background (`-d`), exposing DB/PostgREST/Frontend ports as described in Section 2.

- The `db` service will automatically run the scripts under `build/postgreSQL/init-scripts/` (with the `05` artificial-data stub overridden by `docker-compose-dev.yaml`), creating the schema and populating it with the seed users and artificial data.

## 5. Accessing the Application layers

Once the containers are running, you can access the application directly in your web browser at:

```
http://localhost:8081
```

### First-Time Login

1. Use one of the seed aliases (`sumate`, `gestor`, or `actas`) — see the table in Section 3.
2. Use the corresponding password committed in `build/postgreSQL/init-scripts/04-init-user_roles.sql`. Because the bcrypt hashes are public, ask a teammate or inspect the SQL file for the current dev password.
3. After successful login, change your password via **Mi Perfil** (My Profile) if you plan to share the instance.

The PostgREST API is available on your local network at (example endpoint to the `afiliadas` table):

```
http://localhost:3001/afiliadas
```

Note that the container internally listens on `3000`; `docker-compose-dev.yaml` remaps it to `3001` on the host so it does not collide with other local services.

And also locally available, you can access the PostgreSQL instance at:

```
postgresql://app_user:password@localhost:5432/mydb
```

The schema lives in the `sindicato_inq` schema. `search_path` is **not** a valid libpq query parameter, so set it after connecting with `SET search_path TO sindicato_inq, public;` (or pass `options=-c search_path=sindicato_inq` in your client's options field).

## 6. Available Roles and Permissions

Three role-based access levels are available for testing, mapped to the seed users in Section 3:

- **admin** (seed: `sumate`): Full access to all tables and functions, user management, system administration.
- **gestor** (seed: `gestor`): Access to conflicts management, afiliadas importer, and read-only views module.
- **actas** (seed: `actas`): Access limited to the conflicts module only.

Each role has Row-Level Security (RLS) policies enforced at the database level (see `build/postgreSQL/init-scripts/06-init-rls.sql`) to ensure data segregation.

## 7. Session Management and Security

- **Session Duration:** Authenticated sessions expire after **3 hours**, enforced both client-side (`app.storage.user.lifetime`) and server-side via `AuthMiddleware` in `build/niceGUI/main.py`.
- **Brute-Force Guard:** `build/niceGUI/auth/login.py` keeps an in-process counter per username. After **5 consecutive failed attempts** the account is locked for **15 minutes**. There is **no per-IP rate limit** — the guard is keyed on the submitted username only and resets on process restart, so it is a defense against casual guessing, not distributed attacks. For multi-worker / multi-container deployments, move this state into a shared store (Redis or a `login_attempts` table).
- **Password Hashing:** All credentials are stored as bcrypt hashes via `passlib` (`CryptContext(schemes=["bcrypt"])`). `passlib`'s bcrypt default is **12 rounds** (the `$2b$12$…` prefixes in `04-init-user_roles.sql` confirm this). The code does not override the round count.
- **JWT Tokens:** Authentication uses HS256 JWTs minted by `auth/token_utils.py` with a 3-hour expiration, mirroring the session lifetime. The same `PGRST_JWT_SECRET` must be set on both the NiceGUI container and the PostgREST container.

## 8. Forcing stop and cleaning

From your project's root run the following to stop & remove all the containers and images afterwards:

```bash
docker compose --profile Frontend down -v && docker system prune -a --volumes -f
```

Caveat: the `db` service uses a **bind mount** to `./storage` (not a named Docker volume), so `down -v` will **not** delete the PostgreSQL data directory. To force a full re-initialization of the schema and seed scripts on next `up`, also remove the bind-mounted folder:

```bash
docker compose --profile Frontend down
Remove-Item -Recurse -Force ./storage   # PowerShell
# or: rm -rf ./storage                   # bash / WSL
```

Without this step, the `docker-entrypoint-initdb.d` scripts will **not** re-run on the next `up`, because PostgreSQL only executes them when the data directory is empty.

---

## 🔒 Security Best Practices for Development

- ✅ Treat the credentials in `04-init-user_roles.sql` as throwaway — they are public by design.
- ✅ Never commit real production password hashes to the repository.
- ✅ Rotate the dev credentials (see Section 3) before sharing a demo instance with external collaborators.
- ✅ Use `.gitignore` to exclude any local credential files you generate (e.g. `dev_credentials.json`).
- ✅ Rotate credentials regularly for production deployments.
- ✅ Use strong, unique passwords (minimum 12 characters with mixed case, numbers, and symbols).
- ❌ Never reuse the committed dev hashes in production.
- ❌ Don't expose the dev stack (port `8081` / `3001` / `5432`) to the public internet — it lacks the Nginx + Certbot + UFW hardening that the `Secured` profile provides.
