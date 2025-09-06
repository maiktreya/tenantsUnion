# Testing Suite for Sindicato de Inquilinas App
This directory contains the automated tests for the application. The goal is to ensure code quality, prevent regressions, and validate functionality across all layers of the architecture.

## 🚀 How to Run Tests
Prerequisites
Docker and Docker Compose must be installed.

Python 3.10+ with pip is required.

Installation
Install Python dependencies:
From the root of the project, install the required packages for testing:

```bash
pip install -r tests/requirements.txt
```

Running the Suite
A convenience script is provided to run all tests.

Execute the test runner script:
This script will automatically handle starting and stopping the required Docker containers for integration tests.

```bash
chmod +x tests/run_tests.sh
./tests/run_tests.sh
```

Alternatively, you can run pytest directly:

```bash
pytest
```

## 🗂️ Test Structure

The testing suite is organized into three main categories:

### 1. Unit Tests (tests/unit/)

Purpose: To test individual components (functions, classes) in isolation. These tests are fast and do not require external services like a database.

Examples:


- **test_api_client.py**: Tests the APIClient's methods for making HTTP requests, mocking the API endpoints.
- **test_state_management.py**: Tests the logic within state classes for filtering, sorting, and pagination.
test_auth.py: Tests authentication helper functions like password verification.
- **test_dialogs.py**: Tests the dialogs module, including the RecordDialog class. This includes testing the save_record method with mocked API responses.

### 2. Integration Tests (tests/integration/)

Purpose: To test the interaction between different components of the system. These tests are slower as they require spinning up live services.

Example:


- **test_database_api.py**: This is a crucial test that starts the PostgreSQL and PostgREST services using Docker. It inserts data directly into the database, then uses the real APIClient to verify that the data can be correctly retrieved through the live API. This validates the entire backend stack.


### 3. End-to-End (E2E) Tests (tests/e2e/)

Purpose: To simulate real user interactions with the application's user interface. These tests run a headless browser to interact with the NiceGUI frontend.

Example:

- **test_login_flow.py**: Simulates a user navigating to the login page, entering credentials, and verifying that they are redirected to the home page upon successful login. This tests the complete authentication flow from the UI to the backend logic.



---

#### 📦 Key Libraries Used


- **Pytest**: The core testing framework.
- **Pytest-Asyncio**: For testing asynchronous code.
- **RESPX**: For mocking HTTP requests in unit tests.
- **Pytest-Docker**: For managing Docker containers within integration tests.
- **NiceGUI Testing Tools**: For E2E testing of the user interface.