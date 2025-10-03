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
pytest
```

Useful selections:

- Skip the Selenium UI suite while focusing on fast tests: `pytest -k "not ui_flows"`.
- Run only the end-to-end UI flows: `pytest tests/test_ui_flows.py`.
- Run the schema alignment guard: `pytest tests/test_config_schema_alignment.py`.

## Test inventory

### Fast unit-style tests

These tests execute quickly and use fixtures plus `respx` to isolate network calls.

- `test_auth.py` checks authentication helpers (password hashing and validation).
- `test_filters.py` and `test_estate_management.py` validate the NiceGUI table filtering, sorting, and pagination helpers.
- `test_database_api.py` exercises `APIClient` behaviour with mocked PostgREST responses.
- `test_afiliadas_importer.py` covers the async importer workflow, including fuzzy matching helpers.
- `test_config_schema_alignment.py` compares `TABLE_INFO` and `VIEW_INFO` against the SQL DDL under `build/postgreSQL/init-scripts-dev`, ensuring configuration stays in sync with the database schema.

### Integration and consistency checks

Fixtures defined in `tests/conftest.py` provide shared wiring:

- `DebugAPIClient` wraps the NiceGUI API client for easier assertions.
- Async fixtures expose ready-to-use mocked clients and reusable data factories.
- Utilities automatically add the NiceGUI build directory to `sys.path` so tests import the application modules without additional setup.

### End-to-end UI tests

`tests/test_ui_flows.py` spins up the NiceGUI app in-process, launches a headless Chrome session with Selenium, and mocks backend calls through `respx`.

Notes:

- Chrome must be installed; `webdriver-manager` downloads the matching driver automatically.
- The fixture `app_server` starts the UI on `http://localhost:8899`; all API calls inside the UI are intercepted and mocked.
- Keep the environment quiet while the Selenium tests run, because they expect the chosen port to be free.

## Troubleshooting

- If Selenium cannot start Chrome, install or update Chrome/Chromium and rerun `pip install -r tests/requirements.txt` to refresh the driver manager.
- Stale caches in `.pytest_cache/` can be removed with `pytest --cache-clear` when changing schema or configuration files.

This guide stays in sync with the current test files under `tests/` and the SQL definitions in `build/postgreSQL/init-scripts*`.

> TRICK: To push hot reload recreation of views in the production database, from inside the host machine project´s root folder run: docker exec -i tenantsunion-db-1 psql -U app_user -d mydb -v ON_ERROR_STOP=1 -f /docker-entrypoint-initdb.d/04-init-views.sql
