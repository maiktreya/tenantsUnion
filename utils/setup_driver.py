import time
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService

def setup_driver(headless: bool = True):
    """
    Configures and returns a Selenium Chrome WebDriver using the
    system-installed chromedriver.
    """
    print("Setting up Chrome WebDriver from system path...")
    print(f"System Architecture: {platform.machine()}")

    # The standard path where `apt` installs the chromedriver
    DRIVER_PATH = "/usr/bin/chromedriver" 
    
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # Point the service directly to the installed driver
        service = ChromeService(executable_path=DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ WebDriver initialized successfully using system driver.")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize WebDriver: {e}")
        print(f"   Ensure you have installed the driver with: sudo apt-get install -y chromium-chromedriver")
        raise

# --- Main Execution ---
if __name__ == "__main__":
    web_driver = None
    try:
        web_driver = setup_driver(headless=True)
        
        print("\nNavigating to example.com...")
        web_driver.get("http://example.com")
        
        time.sleep(1)
        
        print(f"Page Title: {web_driver.title}")
        print("\n✅ Script completed successfully!")
        
    except Exception as e:
        print("\n--- SCRIPT FAILED ---")

    finally:
        if web_driver:
            print("\nClosing WebDriver.")
            web_driver.quit()

