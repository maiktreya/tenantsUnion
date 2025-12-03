# tests/test_ui_flows.py
import os
import threading
import time
import sys
from pathlib import Path
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

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skip(
        reason="Integration tests requiring full app server setup with Selenium - run separately with: pytest -m 'not skip'"
    ),
]
REAL_API_URL = "http://localhost:3001"


class SeleniumUITester:
    def __init__(self, base_url, headless=True):
        self.base_url = base_url
        self.driver = None
        self.wait = None
        self.headless = headless
        self._setup_driver()

    def _setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            pytest.fail(f"Failed to initialize Chrome driver: {e}")

    def open(self, path):
        url = f"{self.base_url}{path}"
        self.driver.get(url)
        time.sleep(1)
        return self

    def find_and_type(self, label_text, text):
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
                return self
            except (TimeoutException, NoSuchElementException):
                continue
        pytest.fail(f"Could not find input field with label: {label_text}")

    def click(self, selector):
        strategies = [
            (By.XPATH, f"//button[contains(., '{selector}')]"),
            (By.XPATH, f"//*[contains(text(), '{selector}')]"),
            (By.CSS_SELECTOR, selector),
        ]
        for by, value in strategies:
            try:
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
                element.click()
                time.sleep(0.5)
                return self
            except (TimeoutException, NoSuchElementException):
                continue
        pytest.fail(f"Could not find clickable element: {selector}")

    def assert_text_present(self, text, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '{text}')]")
                )
            )
        except TimeoutException:
            pytest.fail(f"Expected text not found within {timeout}s: {text}")

    def get_url(self):
        return self.driver.current_url

    def close(self):
        if self.driver:
            self.driver.quit()


@pytest.fixture(scope="session")
def app_server():
    port = 8899
    base_url = f"http://localhost:{port}"

    def run_nicegui_app():
        try:
            os.environ["POSTGREST_API_URL"] = REAL_API_URL

            # Add the build/niceGUI directory to the path for imports
            app_path = Path(__file__).parent.parent / "build" / "niceGUI"
            if str(app_path) not in sys.path:
                sys.path.insert(0, str(app_path))

            print(f"DEBUG: App path: {app_path}")
            print(f"DEBUG: App path exists: {app_path.exists()}")

            # Robust import to handle re-execution in tests
            if "main" in sys.modules:
                from nicegui import ui

                print("✓ Using already-imported UI module")
            else:
                try:
                    from main import main_page_entry
                    from nicegui import ui

                    print("✓ Successfully imported main and UI")
                except ImportError as import_err:
                    print(f"❌ Failed to import main: {import_err}")
                    import traceback

                    traceback.print_exc()
                    raise

            try:
                print(f"Starting NiceGUI server on port {port}...")
                ui.run(
                    port=port,
                    show=False,
                    reload=False,
                    host="127.0.0.1",
                    storage_secret="my_test_secret_key",
                )
            except Exception as e:
                # Handle potential middleware re-addition error if app wasn't fully cleared
                if "Cannot add middleware" in str(e):
                    print("⚠ Middleware already added (expected in tests)")
                else:
                    print(f"❌ Error running UI: {e}")
                    import traceback

                    traceback.print_exc()
                    raise

        except Exception as e:
            import traceback

            print(f"❌ An error occurred while running the NiceGUI app: {e}")
            traceback.print_exc()

    server_thread = threading.Thread(target=run_nicegui_app, daemon=True)
    server_thread.start()

    print("Waiting for NiceGUI server to start...")

    for attempt in range(60):  # Increase timeout to 60 seconds
        try:
            response = requests.get(base_url, timeout=1)
            if response.status_code in [200, 404, 500]:
                print(f"✓ Server is running at {base_url}")
                yield base_url
                return
        except requests.RequestException as e:
            if attempt % 10 == 0:
                print(f"  Attempt {attempt}: {type(e).__name__}")
            time.sleep(1)

    pytest.fail(
        f"The NiceGUI test server failed to start within 60 seconds at {base_url}"
    )


@pytest.fixture
def ui_tester(app_server):
    tester = SeleniumUITester(app_server, headless=True)
    yield tester
    tester.close()


# --- TESTS ---


@respx.mock
async def test_successful_login_and_navigation(ui_tester: SeleniumUITester):
    respx.get(f"{REAL_API_URL}/usuarios?alias=eq.sumate").mock(
        return_value=Response(200, json=[{"id": 1, "alias": "sumate"}])
    )
    # Correct hash for 'inquidb2025'
    respx.get(f"{REAL_API_URL}/usuario_credenciales?usuario_id=eq.1").mock(
        return_value=Response(
            200,
            json=[
                {
                    "password_hash": "$2b$12$gVMWfDAGD3K7cG0IgaAmxOLsa9hBDN2FK3iFU96R7JZ7d6t.tzrBC"
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
    ui_tester.find_and_type("Password", "inquidb2025")  # New Password
    ui_tester.click("Log in")

    ui_tester.assert_text_present("Bienvenido al Sistema de Gestión")
    ui_tester.assert_text_present("User: sumate (admin)")
    ui_tester.click("Admin BBDD")
    ui_tester.assert_text_present("Administración de Tablas y Registros BBDD")


@respx.mock
async def test_failed_login_shows_error(ui_tester: SeleniumUITester):
    respx.get(f"{REAL_API_URL}/usuarios?alias=eq.sumate").mock(
        return_value=Response(200, json=[{"id": 1, "alias": "sumate"}])
    )
    # Correct hash so 'wrong_password' fails properly
    respx.get(f"{REAL_API_URL}/usuario_credenciales?usuario_id=eq.1").mock(
        return_value=Response(
            200,
            json=[
                {
                    "password_hash": "$2b$12$gVMWfDAGD3K7cG0IgaAmxOLsa9hBDN2FK3iFU96R7JZ7d6t.tzrBC"
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
