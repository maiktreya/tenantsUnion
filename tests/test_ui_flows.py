# tests/test_ui_flows.py
"""
The primary, corrected end-to-end UI test suite for the application.
This version uses a reliable threading model to run the NiceGUI server
and provides a clean, robust pattern for browser-based testing with Selenium.
"""
import pytest
import time
import respx
from httpx import Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import threading
import sys
from pathlib import Path
import requests

# Add project paths to allow the test server to import the application
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build" / "niceGUI"))

pytestmark = pytest.mark.asyncio


class SeleniumUITester:
    """A simple and robust UI tester using Selenium with Chrome."""

    def __init__(self, base_url, headless=True):
        self.base_url = base_url
        self.driver = None
        self.wait = None
        self.headless = headless
        self._setup_driver()

    def _setup_driver(self):
        """Initializes the Chrome driver with appropriate options."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            print(f"Chrome driver initialized (headless={self.headless})")
        except Exception as e:
            pytest.fail(f"Failed to initialize Chrome driver: {e}")

    def open(self, path):
        """Navigates to a specific path on the test server."""
        url = f"{self.base_url}{path}"
        print(f"Navigating to: {url}")
        self.driver.get(url)
        time.sleep(1)  # Allow a moment for the page to render
        return self

    def find_and_type(self, selector, text):
        """Finds an input field by its placeholder text or selector and types into it."""
        strategies = [
            (By.XPATH, f"//input[@placeholder='{selector}']"),
            (By.CSS_SELECTOR, selector),
        ]
        for by, value in strategies:
            try:
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
                element.clear()
                element.send_keys(text)
                print(f"Typed '{text}' into field found by {by.name}: {value}")
                return self
            except (TimeoutException, NoSuchElementException):
                continue
        pytest.fail(f"Could not find input field: {selector}")

    def click(self, selector):
        """Finds and clicks an element, trying by visible text first."""
        strategies = [
            (By.XPATH, f"//button[contains(text(), '{selector}')]"),
            (By.XPATH, f"//*[contains(text(), '{selector}')]"),
            (By.CSS_SELECTOR, selector),
        ]
        for by, value in strategies:
            try:
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
                element.click()
                print(f"Clicked element found by {by.name}: {value}")
                time.sleep(0.5)
                return self
            except (TimeoutException, NoSuchElementException):
                continue
        pytest.fail(f"Could not find clickable element: {selector}")

    def assert_text_present(self, text, timeout=5):
        """Asserts that specific text is visible on the page."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '{text}')]")
                )
            )
            print(f"Found expected text: {text}")
        except TimeoutException:
            pytest.fail(f"Expected text not found within {timeout}s: {text}")

    def assert_text_absent(self, text):
        """Asserts that specific text is NOT visible on the page."""
        try:
            self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
            pytest.fail(f"Text should not be present but was found: {text}")
        except NoSuchElementException:
            print(f"Confirmed text is absent: {text}")

    def get_url(self):
        return self.driver.current_url

    def close(self):
        if self.driver:
            self.driver.quit()
            print("Browser closed.")


@pytest.fixture(scope="session")
def app_server():
    """Starts the NiceGUI app in a separate thread for the entire test session."""
    port = 8899
    base_url = f"http://localhost:{port}"

    def run_nicegui_app():
        try:
            from main import main_page_entry
            from nicegui import ui

            # *** THIS IS THE FIX ***
            # Provide a storage_secret to enable app.storage.user
            ui.run(
                port=port,
                show=False,
                reload=False,
                host="127.0.0.1",
                storage_secret="my_test_secret_key",
            )

        except ImportError as e:
            pytest.fail(f"Failed to import and run the main NiceGUI application: {e}")
        except Exception as e:
            print(f"An error occurred while running the NiceGUI app: {e}")

    server_thread = threading.Thread(target=run_nicegui_app, daemon=True)
    server_thread.start()

    # Wait for the server to become available
    for _ in range(30):
        try:
            response = requests.get(base_url, timeout=1)
            if response.status_code in [
                200,
                404,
                500,
            ]:  # 500 is ok, means server is up but hit an error
                print(f"Server is up and running at {base_url}")
                yield base_url
                return
        except requests.RequestException:
            time.sleep(1)

    pytest.fail("The NiceGUI test server failed to start within 30 seconds.")


@pytest.fixture
def ui_tester(app_server):
    """Provides a clean Selenium UI tester instance for each test."""
    tester = SeleniumUITester(app_server, headless=True)
    yield tester
    tester.close()


# --- Actual UI Tests ---


@respx.mock
async def test_successful_login_and_navigation(
    ui_tester: SeleniumUITester, mock_api_url: str
):
    """Tests the full login flow and navigation to a protected page."""
    # Mock API responses for user 'sumate'
    respx.get(f"{mock_api_url}/usuarios").mock(
        return_value=Response(200, json=[{"id": 1, "alias": "sumate"}])
    )
    respx.get(f"{mock_api_url}/usuario_credenciales").mock(
        return_value=Response(
            200,
            json=[
                {
                    "password_hash": "$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6"
                }
            ],
        )
    )
    respx.get(f"{mock_api_url}/usuario_roles").mock(
        return_value=Response(200, json=[{"role_id": 1}])
    )
    respx.get(f"{mock_api_url}/roles").mock(
        return_value=Response(200, json=[{"id": 1, "nombre": "admin"}])
    )

    # 1. Navigate to login page
    ui_tester.open("/login")

    # 2. Fill in credentials and log in
    ui_tester.find_and_type("Username", "sumate")
    ui_tester.find_and_type("Password", "12345678")
    ui_tester.click("Log in")

    # 3. Verify successful login and presence of home page content
    ui_tester.assert_text_present("Bienvenido al Sistema de Gestión")
    ui_tester.assert_text_present("User: sumate (admin)")

    # 4. Navigate to a protected page and verify it loads
    ui_tester.click("Admin BBDD")
    ui_tester.assert_text_present("Administración de Tablas y Registros BBDD")


@respx.mock
async def test_failed_login_shows_error(ui_tester: SeleniumUITester, mock_api_url: str):
    """Tests that an incorrect password displays an error message."""
    respx.get(f"{mock_api_url}/usuarios").mock(
        return_value=Response(200, json=[{"id": 1, "alias": "sumate"}])
    )
    respx.get(f"{mock_api_url}/usuario_credenciales").mock(
        return_value=Response(
            200,
            json=[
                {
                    "password_hash": "$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6"
                }
            ],
        )
    )

    ui_tester.open("/login")
    ui_tester.find_and_type("Username", "sumate")
    ui_tester.find_and_type("Password", "wrong_password")
    ui_tester.click("Log in")

    # Verify error message is shown and we are still on the login page
    ui_tester.assert_text_present("Wrong username or password")
    assert "login" in ui_tester.get_url()
