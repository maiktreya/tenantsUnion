import time
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
# This import is required to specify the browser type
from webdriver_manager.core.os_manager import ChromeType

def setup_driver(headless: bool = True):
    """
    Configures Selenium WebDriver using webdriver-manager, correctly targeting
    the CHROMIUM browser for aarch64 compatibility.
    """
    print("Setting up WebDriver for aarch64 using the Chromium driver...")
    print(f"System Architecture: {platform.machine()}")

    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # --- THE CORRECT CONFIGURATION ---
        # Explicitly tell webdriver-manager to use the CHROMIUM driver
        # which is compatible with your aarch64 architecture.
        service = ChromeService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ WebDriver initialized successfully.")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize WebDriver: {e}")
        print("   Please ensure 'chromium-browser' is installed: `sudo apt-get install -y chromium-browser`")
        raise

# --- Main Execution ---
if __name__ == "__main__":
    web_driver = None
    try:
        web_driver = setup_driver(headless=True)
        print("\nNavigating to a test page...")
        web_driver.get("http://example.com")
        time.sleep(1)
        print(f"Page Title: {web_driver.title}")
        print("\n✅ Script completed successfully!")
        
    except Exception:
        print("\n--- SCRIPT FAILED ---")

    finally:
        if web_driver:
            print("\nClosing WebDriver.")
            web_driver.quit()
