# tests/test_ui_flows.py
"""
End-to-end UI test suite for the application.
"""
import os  # <<< FINAL FIX: Import the 'os' module
import threading
import time

import pytest
import requests
import respx
from httpx import Response
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

pytestmark = pytest.mark.asyncio

# The application running in the test server is configured to call this API URL.
REAL_API_URL = "http://localhost:3001"


class SeleniumUITester:
    """UI tester using Selenium with Chrome, tuned for NiceGUI components."""

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
        time.sleep(1)
        return self

    def find_and_type(self, label_text, text):
        """Finds an input field by its visible label and types into it."""
        strategies = [
            (
                By.XPATH,
                f"//label[normalize-space(text())='{label_text}']/following::input[1]",
            ),
            (
                By.XPATH,
                f"//div[contains(@class,'q-field')]//*[text()='{label_text}']/ancestor::div[contains(@class,'q-field')]//input",
            ),
        ]
        for by, value in strategies:
            try:
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
                element.clear()
                element.send_keys(text)
                print(f"Typed '{text}' into field found by {by}: {value}")
                return self
            except (TimeoutException, NoSuchElementException):
                continue
        pytest.fail(f"Could not find input field with label: {label_text}")

    def click(self, selector):
        """Finds and clicks an element, trying by visible text first."""
        strategies = [
            (By.XPATH, f"//button[contains(., '{selector}')]"),
            (By.XPATH, f"//*[contains(text(), '{selector}')]"),
            (By.CSS_SELECTOR, selector),
        ]
        for by, value in strategies:
            try:
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
                element.click()
                print(f"Clicked element found by {by}: {value}")
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
            # We must set the API URL for the app running in the test thread
            os.environ["POSTGREST_API_URL"] = REAL_API_URL
            from main import main_page_entry
            from nicegui import ui

            ui.run(
                port=port,
                show=False,
                reload=False,
                host="127.0.0.1",
                storage_secret="my_test_secret_key",
            )
        except Exception as e:
            print(f"An error occurred while running the NiceGUI app: {e}")

    server_thread = threading.Thread(target=run_nicegui_app, daemon=True)
    server_thread.start()
    for _ in range(30):
        try:
            response = requests.get(base_url, timeout=1)
            if response.status_code in [200, 404, 500]:
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
async def test_successful_login_and_navigation(ui_tester: SeleniumUITester):
    """Tests the full login flow and navigation to a protected page."""
    # Mock the REAL_API_URL that the application uses
    respx.get(f"{REAL_API_URL}/usuarios?alias=eq.sumate").mock(
        return_value=Response(200, json=[{"id": 1, "alias": "sumate"}])
    )
    respx.get(f"{REAL_API_URL}/usuario_credenciales?usuario_id=eq.1").mock(
        return_value=Response(
            200,
            json=[
                {
                    "password_hash": "$2b$12$met2aIuPW5YLXdsDmx8VwucCKhFxxt6d0EqA3N1P3OS0Y4N3UofP6"
                }
            ],
        )
    )
    respx.get(f"{REAL_API_URL}/usuario_roles?usuario_id=eq.1").mock(
        return_value=Response(200, json=[{"role_id": 1}])
    )
    respx.get(f"{REAL_API_URL}/roles?id=in.(1)").mock(
        return_value=Response(200, json=[{"id": 1, "nombre": "admin"}])
    )

    ui_tester.open("/login")
    ui_tester.find_and_type("Username", "sumate")
    ui_tester.find_and_type("Password", "12345678")
    ui_tester.click("Log in")

    ui_tester.assert_text_present("Bienvenido al Sistema de Gestión")
    ui_tester.assert_text_present("User: sumate (admin)")

    ui_tester.click("Admin BBDD")
    ui_tester.assert_text_present("Administración de Tablas y Registros BBDD")


@respx.mock
async def test_failed_login_shows_error(ui_tester: SeleniumUITester):
    """Tests that an incorrect password displays an error message."""
    # Mock the REAL_API_URL that the application uses
    respx.get(f"{REAL_API_URL}/usuarios?alias=eq.sumate").mock(
        return_value=Response(200, json=[{"id": 1, "alias": "sumate"}])
    )
    respx.get(f"{REAL_API_URL}/usuario_credenciales?usuario_id=eq.1").mock(
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

    ui_tester.assert_text_present("Wrong username or password")
    assert "login" in ui_tester.get_url()
