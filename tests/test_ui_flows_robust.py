# tests/test_ui_flows_robust.py

import pytest
import asyncio
import threading
import time
import respx
from httpx import Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import subprocess
import sys
from pathlib import Path
import os
import tempfile
import socket

# Add the project root to the Python path to allow imports from the app source
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytestmark = pytest.mark.asyncio


def run_nicegui_server(port):
    """
    Global function to run NiceGUI server - must be at module level for Windows multiprocessing
    """
    import sys
    from pathlib import Path

    # Add project paths
    sys.path.insert(
        0, str(Path(__file__).resolve().parent.parent / "build" / "niceGUI")
    )

    try:
        from main import main_page_entry
        from nicegui import ui

        ui.run(port=port, show=False, reload=False)
    except ImportError:
        try:
            import build.niceGUI.main as main_module
            from nicegui import ui

            ui.run(port=port, show=False, reload=False)
        except ImportError as e:
            print(f"Failed to import main application: {e}")
            sys.exit(1)


class NiceGUITestServer:
    """
    A test server that runs your NiceGUI app using subprocess instead of multiprocessing
    This approach works better on Windows and avoids pickle issues
    """

    def __init__(self, port=8899):
        self.port = port
        self.process = None
        self.base_url = f"http://localhost:{port}"

    def _find_free_port(self):
        """Find a free port to use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.listen(1)
            return s.getsockname()[1]

    def start(self):
        """Start the NiceGUI server using subprocess"""
        # Find a free port if the default is busy
        original_port = self.port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", self.port))
        except OSError:
            self.port = self._find_free_port()
            self.base_url = f"http://localhost:{self.port}"
            print(f"Port {original_port} busy, using {self.port} instead")

        # Create a script to run the server
        script_content = f"""
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build" / "niceGUI"))

try:
    from main import main_page_entry
    from nicegui import ui
    print("Starting NiceGUI server on port {self.port}")
    ui.run(port={self.port}, show=False, reload=False, host="127.0.0.1")
except ImportError as e1:
    try:
        import build.niceGUI.main as main_module
        from nicegui import ui
        print("Starting NiceGUI server on port {self.port} (alternative import)")
        ui.run(port={self.port}, show=False, reload=False, host="127.0.0.1")
    except ImportError as e2:
        print(f"Failed to import main application: {{e1}}, {{e2}}")
        sys.exit(1)
"""

        # Write the script to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script_content)
            self.script_path = f.name

        # Start the server as a subprocess
        self.process = subprocess.Popen(
            [sys.executable, self.script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Wait for server to start
        import requests

        for i in range(30):  # Wait up to 30 seconds
            if self.process.poll() is not None:
                # Process has terminated
                output = (
                    self.process.stdout.read() if self.process.stdout else "No output"
                )
                raise RuntimeError(f"Server process terminated early. Output: {output}")

            try:
                response = requests.get(self.base_url, timeout=1)
                if response.status_code in [
                    200,
                    404,
                ]:  # 404 is fine, means server is up
                    print(f"NiceGUI test server started on {self.base_url}")
                    return True
            except requests.exceptions.RequestException:
                pass

            time.sleep(1)

        # If we get here, the server didn't start
        output = ""
        if self.process.stdout:
            output = self.process.stdout.read()
        raise RuntimeError(
            f"Failed to start NiceGUI test server. Server output: {output}"
        )

    def stop(self):
        """Stop the test server"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        # Clean up the temporary script
        if hasattr(self, "script_path") and os.path.exists(self.script_path):
            os.unlink(self.script_path)

        print("NiceGUI test server stopped")


class RobustUITester:
    """
    A robust UI tester that uses Selenium to interact with the NiceGUI app
    """

    def __init__(self, base_url, headless=True):
        self.base_url = base_url
        self.driver = None
        self.wait = None
        self.headless = headless

    def start_browser(self):
        """Initialize the browser driver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def stop_browser(self):
        """Clean up the browser driver"""
        if self.driver:
            self.driver.quit()

    def open(self, path):
        """Navigate to a specific path"""
        url = f"{self.base_url}{path}"
        print(f"Opening: {url}")
        self.driver.get(url)
        return self

    def find_element(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Find an element with various fallback strategies"""
        strategies = [
            # Try CSS selector first
            (By.CSS_SELECTOR, selector),
            # Try by placeholder attribute
            (By.XPATH, f"//input[@placeholder='{selector}']"),
            # Try by button text
            (By.XPATH, f"//button[contains(text(), '{selector}')]"),
            # Try by any text content
            (By.XPATH, f"//*[contains(text(), '{selector}')]"),
            # Try by ID
            (By.ID, selector),
            # Try by name
            (By.NAME, selector),
        ]

        for by_method, value in strategies:
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((by_method, value))
                )
                print(f"Found element using {by_method.name}: {value}")
                return element
            except TimeoutException:
                continue

        # Final attempt with longer timeout using original selector
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            self.save_debug_info(f"failed_to_find_{selector}")
            raise NoSuchElementException(f"Could not find element: {selector}")

    def type_in_field(self, field_selector, text):
        """Type text into an input field"""
        element = self.find_element(field_selector)
        element.clear()
        element.send_keys(text)
        print(f"Typed '{text}' into field: {field_selector}")
        return self

    def click_element(self, selector):
        """Click an element"""
        element = self.find_element(selector)
        # Wait for element to be clickable
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(element))
        element.click()
        print(f"Clicked element: {selector}")
        return self

    def wait_for_text(self, text, timeout=10):
        """Wait for specific text to appear on the page"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '{text}')]")
                )
            )
            print(f"Found text: {text}")
            return True
        except TimeoutException:
            self.save_debug_info(f"waiting_for_text_{text}")
            return False

    def assert_text_present(self, text):
        """Assert that text is present on the page"""
        if not self.wait_for_text(text, timeout=5):
            raise AssertionError(f"Text not found: {text}")

    def assert_text_not_present(self, text):
        """Assert that text is NOT present on the page"""
        try:
            element = self.driver.find_element(
                By.XPATH, f"//*[contains(text(), '{text}')]"
            )
            if element.is_displayed():
                raise AssertionError(
                    f"Text should not be present but was found: {text}"
                )
        except NoSuchElementException:
            # Text not found - this is what we want
            pass

    def get_current_url(self):
        """Get the current URL"""
        return self.driver.current_url

    def save_debug_info(self, test_name):
        """Save screenshot and page source for debugging"""
        try:
            screenshot_path = f"test_debug_{test_name}.png"
            self.driver.save_screenshot(screenshot_path)

            html_path = f"test_debug_{test_name}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)

            print(f"Debug info saved: {screenshot_path}, {html_path}")
        except Exception as e:
            print(f"Failed to save debug info: {e}")


@pytest.fixture(scope="session")
def test_server():
    """Start and stop the NiceGUI test server for the entire test session"""
    server = NiceGUITestServer(port=8899)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def ui_tester(test_server):
    """Provide a UI tester instance for each test"""
    tester = RobustUITester(test_server.base_url, headless=True)
    tester.start_browser()
    yield tester
    tester.stop_browser()


# Actual UI tests using the robust approach


@respx.mock
async def test_successful_login_and_logout_robust(
    ui_tester: RobustUITester, mock_api_url: str
):
    """
    Test the complete login and logout flow using Selenium
    """
    # Mock API calls for the 'sumate' (admin) user
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

    # Navigate to login page
    ui_tester.open("/login")

    # Fill in login form
    ui_tester.type_in_field("Username", "sumate")
    ui_tester.type_in_field("Password", "12345678")

    # Submit login
    ui_tester.click_element("Log in")

    # Wait for redirect and verify home page
    ui_tester.wait_for_text("Bienvenido al Sistema de Gestión")
    ui_tester.assert_text_present("User: sumate (admin)")
    ui_tester.assert_text_present("Admin BBDD")

    # Test logout
    ui_tester.click_element("logout")
    ui_tester.wait_for_text("Log in")

    # Verify we're back at login page
    current_url = ui_tester.get_current_url()
    assert "login" in current_url


@respx.mock
async def test_failed_login_robust(ui_tester: RobustUITester, mock_api_url: str):
    """
    Test failed login with wrong password
    """
    # Mock API calls
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

    # Navigate to login page
    ui_tester.open("/login")

    # Fill in login form with wrong password
    ui_tester.type_in_field("Username", "sumate")
    ui_tester.type_in_field("Password", "wrong_password")

    # Submit login
    ui_tester.click_element("Log in")

    # Verify error message appears
    ui_tester.assert_text_present("Wrong username or password")

    # Verify we're still on login page
    current_url = ui_tester.get_current_url()
    assert "login" in current_url


@respx.mock
async def test_role_based_access_robust(ui_tester: RobustUITester, mock_api_url: str):
    """
    Test that users with limited roles see appropriate UI elements
    """
    # Mock API calls for 'actas' user
    respx.get(f"{mock_api_url}/usuarios").mock(
        return_value=Response(200, json=[{"id": 3, "alias": "actas"}])
    )
    respx.get(f"{mock_api_url}/usuario_credenciales").mock(
        return_value=Response(
            200,
            json=[
                {
                    "password_hash": "$2b$12$.2k0jdsNjg6J/lcZL1WBkej85pFdSTq2NWdFBjPgfZ7EXjAbjoSei"
                }
            ],
        )
    )
    respx.get(f"{mock_api_url}/usuario_roles").mock(
        return_value=Response(200, json=[{"role_id": 3}])
    )
    respx.get(f"{mock_api_url}/roles").mock(
        return_value=Response(200, json=[{"id": 3, "nombre": "actas"}])
    )

    # Login as actas user
    ui_tester.open("/login")
    ui_tester.type_in_field("Username", "actas")
    ui_tester.type_in_field("Password", "12345678")
    ui_tester.click_element("Log in")

    # Verify successful login
    ui_tester.assert_text_present("Bienvenido al Sistema de Gestión")
    ui_tester.assert_text_present("User: actas (actas)")

    # Verify role-based UI elements
    ui_tester.assert_text_present("Conflictos")  # Should see this
    ui_tester.assert_text_not_present("Admin BBDD")  # Should NOT see this
    ui_tester.assert_text_not_present("Vistas")  # Should NOT see this


# Additional utility test to verify the testing infrastructure works


async def test_ui_infrastructure(ui_tester: RobustUITester):
    """
    Test that our UI testing infrastructure is working properly
    """
    # Just try to open the main page and verify the server is responding
    ui_tester.open("/")

    # The page should load (even if it redirects to login)
    # We just want to verify the server is reachable
    current_url = ui_tester.get_current_url()
    assert "localhost:8899" in current_url
    print(f"UI infrastructure test passed. Current URL: {current_url}")


# Optional: Performance test


async def test_page_load_performance(ui_tester: RobustUITester):
    """
    Test that pages load within reasonable time limits
    """
    import time

    start_time = time.time()
    ui_tester.open("/login")
    ui_tester.wait_for_text("Log in", timeout=5)  # Wait for page to fully load
    load_time = time.time() - start_time

    print(f"Login page loaded in {load_time:.2f} seconds")
    assert load_time < 10, f"Page load time too slow: {load_time:.2f}s"
