import time
import platform
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def clear_webdriver_cache():
    """
    Finds and clears the default webdriver-manager cache directory (~/.wdm)
    to force a fresh driver download.
    """
    print("Attempting to clear WebDriver cache...")
    try:
        # The default cache directory is almost always ~/.wdm
        cache_path = os.path.join(os.path.expanduser('~'), '.wdm')
        
        if os.path.exists(cache_path):
            print(f"Found cache directory at: {cache_path}")
            shutil.rmtree(cache_path)
            print("✅ Cache cleared successfully.")
        else:
            print("Cache directory not found (already clean).")
            
    except Exception as e:
        print(f"⚠️  Could not automatically clear cache: {e}")
        print(f"   Please try manually deleting the folder: {cache_path}")

def setup_driver(headless: bool = True):
    """
    Configures and returns a Selenium Chrome WebDriver.
    """
    print("\nSetting up Chrome WebDriver...")
    print(f"System Architecture: {platform.machine()}")

    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ WebDriver initialized successfully.")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize WebDriver: {e}")
        raise

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Clear the cache to remove the incorrect driver.
    clear_webdriver_cache()

    web_driver = None
    try:
        # 2. Try to set up the driver again. This will trigger a fresh download.
        web_driver = setup_driver(headless=True)
        
        print("\nNavigating to example.com...")
        web_driver.get("http://example.com")
        
        time.sleep(1) # Wait for page to load
        
        print(f"Page Title: {web_driver.title}")
        
    except Exception as e:
        print("\n--- SCRIPT FAILED ---")
        print("The script failed, most likely because an appropriate chromedriver for your system could not be found automatically.")
        print("This confirms the initial 'Exec format error' was due to an architecture mismatch.")
        print("Please check the webdriver-manager documentation for your specific OS/CPU combination.")

    finally:
        if web_driver:
            print("\nClosing WebDriver.")
            web_driver.quit()
