# Testing Guide

This document describes the automated test stack for the Sindicato de Inquilinas application and how to run it locally.

## Prerequisites

- Python 3.10 or newer with `pip`.
- Google Chrome or Chromium for the UI flow tests. The suite uses Selenium in headless mode.
- Recommended: create and activate a virtual environment before installing the test dependencies.

Install the testing dependencies from the project root:

```bash
pip install -r tests/requirements.txt
```

## Running the test suite

Run every test (unit, integration-style, and UI) with:

```bash
pytest --cov
```

Useful selections:

- Skip the Selenium UI suite while focusing on fast tests: `pytest -k "not ui_flows"`.
- Run only the end-to-end UI flows (which are `skip`-marked by default): `pytest -m "not skip" tests/test_ui_flows.py`.
- Run the schema alignment guard: `pytest tests/test_config_schema_alignment.py`.

## Test inventory

### Fast unit-style tests

These tests execute quickly and use fixtures plus `respx` to isolate network calls.

- `test_auth.py` exercises `APIClient` HTTP behaviour against mocked PostgREST responses (GET/PATCH/POST/DELETE, filter encoding, HTTP and network error paths). Despite its name, it does not test password hashing — that path is covered implicitly via the login flow in `test_ui_flows.py`.
- `test_filters.py` validates the `FilterPanel` component against sample records.
- `test_estate_management.py` validates the `BaseTableState` sorting/pagination helpers (including `_normalize_for_sorting`).
- `test_afiliadas_importer.py` covers the async relational importer workflow (`MultiTableImportService`): CSV parsing, per-table payload construction, cascading FK lineage, and the dry-run validation path. It does not exercise the `pg_trgm` fuzzy matching (that lives in a PostgREST RPC and is only hit on the live DB).
- `test_config_schema_alignment.py` parses `build/postgreSQL/init-scripts/01-init-schemaDBdef.sql` and `03-init-createViews.sql` with regex and asserts that every field/view declared in `TABLE_INFO` / `VIEW_INFO` exists in the DDL, keeping the config-driven UI in sync with the database schema.

### Live-database RLS regression tests

- `test_rls_privilege_escalation.py` connects **directly to Postgres** (not through PostgREST/NiceGUI) and replays PostgREST's own per-request `SET LOCAL ROLE` / `request.jwt.claims` behavior via `set_config(...)`. It exists specifically to guard `usuario_roles` (the `usuario_id -> role_id` privilege graph — see `06-init-rls.sql`, "Block F") against the self-promotion path: a non-admin JWT rewriting its own role assignment. It also asserts login (`rpc_login`) is unaffected by that RLS, since `rpc_login` runs `SECURITY DEFINER` as the table owner and is RLS-exempt.
  - Requires a live Postgres instance with the full `01`-`06` init scripts applied (e.g. the `db` service from `docker-compose-dev.yaml`). If it can't connect, every test in the module is **skipped**, not failed — same convention as the Selenium suite.
  - Connection defaults match `.env.example` (`app_user` / `mydb` @ `localhost:5432`); override with `PGRLS_HOST` / `PGRLS_PORT` / `PGRLS_USER` / `PGRLS_PASSWORD` / `PGRLS_DB` env vars if needed.
  - Every test runs inside a transaction that's rolled back on teardown, so it's safe to run against a shared dev database — no seeded fixture rows or mutations ever persist.
  - Run it on its own with: `pytest tests/test_rls_privilege_escalation.py -v`

### Integration and consistency checks

Fixtures defined in `tests/conftest.py` provide shared wiring:

- `DebugAPIClient` wraps the NiceGUI API client for easier assertions.
- Async fixtures expose ready-to-use mocked clients and reusable data factories.
- Utilities automatically add the NiceGUI build directory to `sys.path` so tests import the application modules without additional setup.

### End-to-end UI tests

`tests/test_ui_flows.py` spins up the NiceGUI app in-process, launches a headless Chrome session with Selenium, and mocks backend calls through `respx`.

Notes:

- The whole module carries a `pytest.mark.skip` by default (see `pytestmark` at the top of the file). Run them explicitly with `pytest -m "not skip" tests/test_ui_flows.py` (or `--runskip`).
- Chrome must be installed. Selenium 4.6+ ships with **Selenium Manager**, which auto-resolves the matching ChromeDriver — `webdriver-manager` is listed in `tests/requirements.txt` for legacy environments but is not invoked by the test code.
- The `app_server` fixture starts the UI on `http://localhost:8899`; all API calls inside the UI are intercepted and mocked.
- Keep the environment quiet while the Selenium tests run, because they expect port `8899` to be free.

## Troubleshooting

- If Selenium cannot start Chrome, install or update Chrome/Chromium. Selenium Manager (bundled in Selenium 4.6+) will pick up the matching driver automatically on next run; no manual driver download is needed.
- Stale caches in `.pytest_cache/` can be removed with `pytest --cache-clear` when changing schema or configuration files.

This guide stays in sync with the current test files under `tests/` and the SQL definitions in `build/postgreSQL/init-scripts/`.

> TRICK: To force hot-reload recreation of views in a running database, from the project root run:
> `docker exec -i tenantsunion-db-1 psql -U app_user -d mydb -v ON_ERROR_STOP=1 -f /docker-entrypoint-initdb.d/03-init-createViews.sql`