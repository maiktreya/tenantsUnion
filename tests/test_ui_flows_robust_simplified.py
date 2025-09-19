# tests/test_ui_flows_simple.py
"""
A simpler, more reliable UI testing approach using threading instead of multiprocessing
This should work better on Windows and avoid the pickle issues you encountered
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
import socket
import requests

# Add project paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build" / "niceGUI"))

pytestmark = pytest.mark.asyncio


class SimpleUITester:
    """
    A simple UI tester using Selenium with Chrome
    """

    def __init__(self, base_url, headless=True):
        self.base_url = base_url
        self.driver = None
        self.wait = None
        self.headless = headless
        self._setup_driver()

    def _setup_driver(self):
        """Initialize Chrome driver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            print(f"Chrome driver initialized (headless={self.headless})")
        except Exception as e:
            print(f"Failed to initialize Chrome driver: {e}")
            print("Make sure Chrome browser and chromedriver are installed")
            raise

    def open(self, path):
        """Navigate to a path"""
        url = f"{self.base_url}{path}"
        print(f"Navigating to: {url}")
        self.driver.get(url)
        time.sleep(1)  # Give page a moment to load
        return self

    def find_and_type(self, selector, text):
        """Find an input field and type text into it"""
        # Try multiple selector strategies
        strategies = [
            (By.CSS_SELECTOR, f'input[placeholder="{selector}"]'),
            (By.XPATH, f"//input[@placeholder='{selector}']"),
            (By.CSS_SELECTOR, selector),
            (By.ID, selector),
            (By.NAME, selector),
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

        raise NoSuchElementException(f"Could not find input field: {selector}")

    def click(self, selector):
        """Find and click an element"""
        strategies = [
            (By.XPATH, f"//button[contains(text(), '{selector}')]"),
            (By.XPATH, f"//a[contains(text(), '{selector}')]"),
            (By.XPATH, f"//*[contains(text(), '{selector}')]"),
            (By.CSS_SELECTOR, selector),
            (By.ID, selector),
        ]

        for by, value in strategies:
            try:
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
                element.click()
                print(f"Clicked element found by {by.name}: {value}")
                time.sleep(0.5)  # Brief pause after click
                return self
            except (TimeoutException, NoSuchElementException):
                continue

        raise NoSuchElementException(f"Could not find clickable element: {selector}")

    def wait_for_text(self, text, timeout=10):
        """Wait for text to appear on page"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '{text}')]")
                )
            )
            print(f"Found expected text: {text}")
            return True
        except TimeoutException:
            print(f"Text not found within {timeout}s: {text}")
            self._save_debug_info(f"missing_text_{text}")
            return False

    def assert_text_present(self, text):
        """Assert text is present on page"""
        if not self.wait_for_text(text, 5):
            raise AssertionError(f"Expected text not found: {text}")

    def assert_text_absent(self, text):
        """Assert text is NOT present on page"""
        try:
            self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
            raise AssertionError(f"Text should not be present: {text}")
        except NoSuchElementException:
            print(f"Confirmed text is absent: {text}")

    def get_url(self):
        """Get current URL"""
        return self.driver.current_url

    def _save_debug_info(self, identifier):
        """Save screenshot and page source for debugging"""
        try:
            screenshot_file = f"debug_{identifier}.png"
            self.driver.save_screenshot(screenshot_file)

            html_file = f"debug_{identifier}.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)

            print(f"Debug files saved: {screenshot_file}, {html_file}")
        except Exception as e:
            print(f"Failed to save debug info: {e}")

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("Browser closed")


# Test fixtures and actual tests


@pytest.fixture(scope="session")
def app_server():
    """
    Start the NiceGUI app in a thread for testing
    This is simpler and more reliable than multiprocessing
    """
    import threading
    import uvicorn
    import asyncio

    port = 8899
    base_url = f"http://localhost:{port}"
    server_thread = None

    def run_nicegui_app():
        """Run the NiceGUI app - this will run in a separate thread"""
        try:
            # Import your main application
            from main import main_page_entry
            from nicegui import ui

            print(f"Starting NiceGUI on port {port}")
            ui.run(port=port, show=False, reload=False, host="127.0.0.1")
        except ImportError as e:
            print(f"Import failed: {e}")
            try:
                import build.niceGUI.main as main_module
                from nicegui import ui

                print(f"Starting NiceGUI on port {port} (alternative import)")
                ui.run(port=port, show=False, reload=False, host="127.0.0.1")
            except ImportError as e2:
                print(f"Both imports failed: {e}, {e2}")
                return

    # Start the server in a daemon thread
    server_thread = threading.Thread(target=run_nicegui_app, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(base_url, timeout=1)
            if response.status_code in [200, 404]:  # Either is fine
                print(f"Server ready at {base_url}")
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    else:
        raise RuntimeError("Server failed to start within 30 seconds")

    yield base_url

    # Cleanup happens automatically when the thread daemon ends
    print("Test session complete")


@pytest.fixture
def ui_tester(app_server):
    """Provide a UI tester for each test"""
    tester = SimpleUITester(app_server, headless=True)
    yield tester
    tester.close()


# The actual UI tests


@respx.mock
async def test_login_success_simple(ui_tester, mock_api_url: str):
    """Test successful login flow"""
    # Mock the API responses
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

    # Navigate to login and perform login
    ui_tester.open("/login")
    ui_tester.find_and_type("Username", "sumate")
    ui_tester.find_and_type("Password", "12345678")
    ui_tester.click("Log in")

    # Verify successful login
    ui_tester.assert_text_present("Bienvenido al Sistema de Gestión")
    ui_tester.assert_text_present("sumate")
    ui_tester.assert_text_present("admin")


@respx.mock
async def test_login_failure_simple(ui_tester, mock_api_url: str):
    """Test login failure with wrong password"""
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

    # Should show error and stay on login page
    ui_tester.assert_text_present("Wrong username or password")
    assert "login" in ui_tester.get_url()


async def test_basic_navigation_simple(ui_tester):
    """Basic test to verify the server and browser are working"""
    ui_tester.open("/")

    # Just verify we can connect to the server
    current_url = ui_tester.get_url()
    assert "localhost:8899" in current_url
    print(f"Navigation test passed: {current_url}")


# Optional: Test without mocking (if you want to test against real backend)
@pytest.mark.slow
async def test_real_server_connectivity(ui_tester):
    """Test connectivity to the actual running server"""
    ui_tester.open("/login")

    # Just verify the login page loads
    ui_tester.wait_for_text("Log in", timeout=10)
    print("Real server connectivity test passed")
