import time
import platform
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import get_cache_manager

def clear_webdriver_cache():
    """Clears the webdriver-manager cache to force redownload."""
    try:
        cache_path = get_cache_manager().get_root_dir()
        if os.path.exists(cache_path):
            print(f"Clearing WebDriver cache at: {cache_path}")
            shutil.rmtree(cache_path)
            print("✅ Cache cleared successfully.")
    except Exception as e:
        print(f"⚠️  Could not clear cache: {e}")


def setup_driver(headless: bool = True):
    """
    Configures and returns a Selenium Chrome WebDriver.
    """
    print("Setting up Chrome WebDriver...")
    
    # Log system architecture for debugging
    print(f"System Architecture: {platform.machine()}")

    # 1. Set Chrome Options
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    
    # Common options for stability
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 2. Setup WebDriver Service using webdriver-manager
    try:
        service = ChromeService(ChromeDriverManager().install())
        
        # 3. Initialize the WebDriver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ WebDriver initialized successfully.")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize WebDriver: {e}")
        raise

# --- Example Usage ---
if __name__ == "__main__":
    # **Run this first if you get the error**
    clear_webdriver_cache()

    web_driver = None  # Initialize to None
    try:
        # Now, try setting up the driver again
        web_driver = setup_driver(headless=True)
        
        print("\nNavigating to example.com...")
        web_driver.get("http://example.com")
        
        time.sleep(2)
        
        print(f"Page Title: {web_driver.title}")
        
    except Exception as e:
        print(f"\nAn error occurred during script execution: {e}")
        print("This might happen if the correct chromedriver for your system architecture (e.g., ARM64) is not available.")

    finally:
        if web_driver:
            print("\nClosing WebDriver.")
            web_driver.quit()

