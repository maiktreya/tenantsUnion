import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver(headless: bool = True):
    """
    Configures and returns a Selenium Chrome WebDriver.

    Args:
        headless: If True, the browser will run in the background without a UI.
                  Set to False for debugging to see the browser actions.
    """
    print("Setting up Chrome WebDriver...")
    
    # 1. Set Chrome Options
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")  # Recommended headless mode
    
    # Common options for stability, especially in Docker/CI environments
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 2. Setup WebDriver Service using webdriver-manager
    # This automatically downloads/updates the correct driver for your installed Chrome version.
    service = ChromeService(ChromeDriverManager().install())
    
    # 3. Initialize the WebDriver
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ WebDriver initialized successfully.")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize WebDriver: {e}")
        # Consider adding more specific error handling if needed
        raise

# --- Example Usage ---
if __name__ == "__main__":
    # To see the browser window, run with headless=False
    # web_driver = setup_driver(headless=False)
    web_driver = setup_driver(headless=True)
    
    if web_driver:
        try:
            # 4. Use the driver to navigate to a page
            print("\nNavigating to example.com...")
            web_driver.get("http://example.com")
            
            # Wait a moment to see the result
            time.sleep(2)
            
            # 5. Get and print the page title to confirm it worked
            print(f"Page Title: {web_driver.title}")
            
        finally:
            # 6. Always close the driver to free up resources
            print("\nClosing WebDriver.")
            web_driver.quit()

