"""
tests/test_rls_privilege_escalation.py

Live-database security regression test for Row-Level Security on
`usuario_roles` (build/postgreSQL/init-scripts/06-init-rls.sql, "Block F").

WHY THIS TEST EXISTS
---------------------
`usuario_roles` is the usuario_id -> role_id join table that determines who
is admin. It was, for a while, the one table with no RLS policy at all,
which meant any authenticated `web_user` (gestor, actas, anyone) could:

    PATCH /usuario_roles?usuario_id=eq.<their_own_id>
    {"role_id": <the admin role's id>}

...and self-promote to admin on their *next* login, since `rpc_login` reads
`usuario_roles` as SECURITY DEFINER (RLS-exempt) and faithfully returns
whatever role is on the row. This test proves that path is closed, and
that closing it did NOT break the login flow.

METHODOLOGY
-----------
This talks to Postgres directly (not through PostgREST/NiceGUI), and
reproduces exactly what PostgREST does per-request:

    SELECT set_config('role', '<web_anon|web_user>', true);       -- SET LOCAL ROLE
    SELECT set_config('request.jwt.claims', '<jwt payload>', true);

`set_config(..., true)` is the parameterized, `SET LOCAL`-equivalent form
(the third argument makes it transaction-local), so it composes safely
with bind parameters instead of string-interpolating into a raw `SET`
statement. This is also how PostgREST itself applies the JWT claims GUC.

Every test runs inside its own transaction that is rolled back at the end
(see `rls_scope` below) — nothing seeded here is ever committed, so this
is safe to run against a shared dev database and leaves zero residue even
on failure.

REQUIREMENTS & SKIPPING
------------------------
This module needs a live Postgres instance with the full schema (01-06
init scripts) already applied — e.g. the `db` service from
`docker-compose-dev.yaml` (see doc/first_run.md). If it can't connect,
every test in this module is SKIPPED (not failed), the same way
`test_ui_flows.py` skips gracefully when Chrome isn't available.

Connection parameters, in priority order:
    1. Env vars: PGRLS_HOST, PGRLS_PORT, PGRLS_USER, PGRLS_PASSWORD, PGRLS_DB
    2. The project's `.env` file (POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB)
    3. Defaults matching `.env.example` (app_user / pass / mydb @ localhost:5432)

Run just this module with:
    pytest tests/test_rls_privilege_escalation.py -v
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

import pytest

try:
    import psycopg
except ImportError:  # pragma: no cover - exercised only when the dep is missing
    psycopg = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Passlib/bcrypt hash for the literal password "pytestpass123". Its value
# doesn't matter beyond "rpc_login can verify it" — no test here depends on
# what the password actually is, only that a correct vs. incorrect password
# behaves as expected.
_TEST_PASSWORD = "pytestpass123"
_TEST_HASH = "$2b$12$NsvzkdNimcvB7R4wlmuNi.Zz8PS5NSMnMGLVthSa9wYYQGUrGxofW"


def _read_dotenv(path: Path) -> dict:
    """Minimal `.env` parser: KEY=VALUE per line. Ignores comments/blank
    lines and skips shell-substitution values like `UID=$(id -u)` that only
    make sense inside `docker compose`, not a plain Python process."""
    values = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if val.startswith("$("):
            continue
        values[key] = val
    return values


def _connection_params() -> dict:
    dotenv = _read_dotenv(ENV_FILE)
    return {
        "host": os.environ.get("PGRLS_HOST", "localhost"),
        "port": int(os.environ.get("PGRLS_PORT", "5432")),
        "user": os.environ.get("PGRLS_USER", dotenv.get("POSTGRES_USER", "app_user")),
        "password": os.environ.get(
            "PGRLS_PASSWORD", dotenv.get("POSTGRES_PASSWORD", "pass")
        ),
        "dbname": os.environ.get("PGRLS_DB", dotenv.get("POSTGRES_DB", "mydb")),
        "connect_timeout": 3,
    }


@pytest.fixture(scope="module")
def pg_conn():
    """
    A raw connection to the live Postgres instance, as the app's own
    connecting role (`app_user`). Used only to seed/inspect fixtures and to
    flip role/JWT context exactly as PostgREST does per-request.

    Skips the whole module if the database isn't reachable, so the fast
    unit suite (respx-mocked tests) is unaffected when no DB is running.
    """
    if psycopg is None:
        pytest.skip("psycopg is not installed - see tests/requirements.txt")

    params = _connection_params()
    try:
        conn = psycopg.connect(**params)
    except Exception as exc:
        pytest.skip(
            f"Live Postgres not reachable at {params['host']}:{params['port']} "
            f"({exc}). This module needs the dev DB running - see doc/first_run.md."
        )
    conn.autocommit = False
    yield conn
    conn.close()


@dataclass
class RlsScope:
    conn: "psycopg.Connection"
    role_ids: dict  # {"admin": 1, "gestor": 2}
    user_ids: dict  # {"admin": 7, "gestor": 8}

    def as_role(self, pg_role: str, jwt_claims: dict | None = None):
        """Switch the current transaction's effective role + JWT claims,
        mirroring PostgREST's per-request `SET LOCAL ROLE` / claims dance."""
        assert pg_role in ("web_anon", "web_user"), pg_role
        cur = self.conn.cursor()
        cur.execute("SELECT set_config('role', %s, true)", (pg_role,))
        if jwt_claims is not None:
            cur.execute(
                "SELECT set_config('request.jwt.claims', %s, true)",
                (json.dumps(jwt_claims),),
            )
        return cur

    def as_superuser(self):
        """Reset back to the connecting role (app_user), which is RLS-exempt
        (table owner / superuser) - used only to assert ground truth."""
        cur = self.conn.cursor()
        cur.execute("RESET ROLE")
        return cur


@pytest.fixture
def rls_scope(pg_conn):
    """
    Seeds two throwaway users (admin + gestor roles) and yields an
    `RlsScope`. Everything happens inside one transaction per test that is
    ALWAYS rolled back on teardown - no seeded data, and no upserts against
    pre-existing `roles` rows, ever persist.
    """
    cur = pg_conn.cursor()
    cur.execute("SET search_path TO sindicato_inq, public")

    role_ids = {}
    for name in ("admin", "gestor"):
        cur.execute(
            """
            INSERT INTO roles (nombre, descripcion)
            VALUES (%s, 'pytest-rls-fixture')
            ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre
            RETURNING id
            """,
            (name,),
        )
        role_ids[name] = cur.fetchone()[0]

    user_ids = {}
    for role, alias in (("admin", "pytest_rls_admin"), ("gestor", "pytest_rls_gestor")):
        cur.execute(
            """
            INSERT INTO usuarios (alias, nombre, apellidos, email, is_active)
            VALUES (%s, 'pytest', 'rls-fixture', %s, TRUE)
            ON CONFLICT (alias) DO UPDATE SET is_active = TRUE
            RETURNING id
            """,
            (alias, f"{alias}@pytest.local"),
        )
        uid = cur.fetchone()[0]
        user_ids[role] = uid

        cur.execute(
            """
            INSERT INTO usuario_credenciales (usuario_id, password_hash)
            VALUES (%s, %s)
            ON CONFLICT (usuario_id) DO UPDATE SET password_hash = EXCLUDED.password_hash
            """,
            (uid, _TEST_HASH),
        )
        cur.execute(
            """
            INSERT INTO usuario_roles (usuario_id, role_id)
            VALUES (%s, %s)
            ON CONFLICT (usuario_id) DO UPDATE SET role_id = EXCLUDED.role_id
            """,
            (uid, role_ids[role]),
        )

    yield RlsScope(conn=pg_conn, role_ids=role_ids, user_ids=user_ids)

    pg_conn.rollback()  # discard every fixture row and every test mutation


# =====================================================================
# 1. Login must be completely unaffected by RLS on usuario_roles
# =====================================================================


def test_login_succeeds_for_both_roles(rls_scope: RlsScope):
    """rpc_login runs SECURITY DEFINER as the table owner, so it must keep
    returning the right roles[] regardless of RLS on usuario_roles."""
    cur = rls_scope.as_role("web_anon")

    cur.execute(
        "SELECT * FROM sindicato_inq.rpc_login(%s, %s)",
        ("pytest_rls_admin", _TEST_PASSWORD),
    )
    row = cur.fetchone()
    assert row is not None, "admin login must succeed"
    _, alias, roles = row
    assert alias == "pytest_rls_admin"
    assert roles == ["admin"]

    cur.execute(
        "SELECT * FROM sindicato_inq.rpc_login(%s, %s)",
        ("pytest_rls_gestor", _TEST_PASSWORD),
    )
    row = cur.fetchone()
    assert row is not None, "gestor login must succeed"
    _, alias, roles = row
    assert alias == "pytest_rls_gestor"
    assert roles == ["gestor"]


def test_login_fails_cleanly_on_wrong_password(rls_scope: RlsScope):
    cur = rls_scope.as_role("web_anon")
    cur.execute(
        "SELECT * FROM sindicato_inq.rpc_login(%s, %s)",
        ("pytest_rls_gestor", "definitely-wrong"),
    )
    assert cur.fetchone() is None


# =====================================================================
# 2. The actual attack: self-promotion via a forged usuario_roles write
# =====================================================================


def test_gestor_cannot_self_promote_to_admin(rls_scope: RlsScope):
    """
    Reproduces: PATCH /usuario_roles?usuario_id=eq.<gestor_id>
                {"role_id": <admin_role_id>}
    sent with a real, non-forged gestor JWT. Must affect zero rows.
    """
    gestor_id = rls_scope.user_ids["gestor"]
    admin_role_id = rls_scope.role_ids["admin"]

    cur = rls_scope.as_role(
        "web_user",
        {"role": "web_user", "sub": str(gestor_id), "alias": "pytest_rls_gestor", "roles": ["gestor"]},
    )

    # Sanity check: gestor *can* discover the admin role's id via the
    # Block E `reader` policy on `roles` - that's intentional (non-sensitive
    # lookup data). What must NOT work is using it here.
    cur.execute("SELECT id FROM sindicato_inq.roles WHERE nombre = 'admin'")
    assert cur.fetchone()[0] == admin_role_id

    cur.execute(
        "UPDATE sindicato_inq.usuario_roles SET role_id = %s WHERE usuario_id = %s",
        (admin_role_id, gestor_id),
    )
    assert cur.rowcount == 0, "privilege escalation was NOT blocked!"

    # Confirm from a trusted vantage point (RLS-exempt) that the row is
    # genuinely untouched, not just invisible to the attacker's own query.
    cur = rls_scope.as_superuser()
    cur.execute(
        "SELECT role_id FROM sindicato_inq.usuario_roles WHERE usuario_id = %s",
        (gestor_id,),
    )
    assert cur.fetchone()[0] == rls_scope.role_ids["gestor"]


# =====================================================================
# 3. Read/write boundaries
# =====================================================================


def test_gestor_sees_only_own_role_row(rls_scope: RlsScope):
    gestor_id = rls_scope.user_ids["gestor"]
    cur = rls_scope.as_role(
        "web_user",
        {"role": "web_user", "sub": str(gestor_id), "alias": "pytest_rls_gestor", "roles": ["gestor"]},
    )
    cur.execute(
        "SELECT usuario_id FROM sindicato_inq.usuario_roles WHERE usuario_id IN (%s, %s)",
        (rls_scope.user_ids["admin"], gestor_id),
    )
    rows = cur.fetchall()
    assert rows == [(gestor_id,)], "gestor must not see admin's row_id assignment"


def test_admin_sees_and_can_write_all_rows(rls_scope: RlsScope):
    admin_id = rls_scope.user_ids["admin"]
    gestor_id = rls_scope.user_ids["gestor"]
    cur = rls_scope.as_role(
        "web_user",
        {"role": "web_user", "sub": str(admin_id), "alias": "pytest_rls_admin", "roles": ["admin"]},
    )
    cur.execute(
        "SELECT usuario_id FROM sindicato_inq.usuario_roles WHERE usuario_id IN (%s, %s) ORDER BY usuario_id",
        (admin_id, gestor_id),
    )
    assert cur.fetchall() == [(admin_id,), (gestor_id,)]

    # The legitimate path exercised by auth/user_management.py: admin
    # reassigning someone else's role.
    cur.execute(
        "UPDATE sindicato_inq.usuario_roles SET role_id = %s WHERE usuario_id = %s",
        (rls_scope.role_ids["gestor"], gestor_id),
    )
    assert cur.rowcount == 1


def test_anonymous_has_zero_visibility(rls_scope: RlsScope):
    cur = rls_scope.as_role("web_anon")
    cur.execute("SELECT * FROM sindicato_inq.usuario_roles")
    assert cur.fetchall() == []