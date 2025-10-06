import time
import platform
import os
import shutil
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService

def run_command(command):
    """Executes a shell command and prints its output."""
    try:
        print(f"Executing: {' '.join(command)}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stdout:
            print(stdout.decode())
        if stderr:
            print(f"Error: {stderr.decode()}")
        if process.returncode != 0:
            print(f"Command failed with exit code {process.returncode}")
        return process.returncode == 0
    except Exception as e:
        print(f"Failed to execute command: {e}")
        return False

def setup_system():
    """Ensures necessary system packages are installed."""
    print("--- Ensuring system dependencies are met ---")
    if not run_command(["sudo", "apt-get", "update"]):
        return False
    if not run_command(["sudo", "apt-get", "install", "-y", "chromium-browser", "chromium-chromedriver"]):
        return False
    print("✅ System dependencies are up to date.")
    return True

def clear_webdriver_cache():
    """
    Finds and safely removes the default webdriver-manager cache directory (~/.wdm)
    to clean up any incorrect driver downloads.
    """
    print("\n--- Cleaning up old webdriver-manager cache ---")
    try:
        cache_path = os.path.join(os.path.expanduser('~'), '.wdm')
        if os.path.exists(cache_path):
            print(f"Found and removing incorrect cache directory: {cache_path}")
            shutil.rmtree(cache_path)
            print("✅ Cache cleared successfully.")
        else:
            print("No old cache found (already clean).")
    except Exception as e:
        print(f"⚠️  Could not remove cache directory: {e}")

def setup_driver(headless: bool = True):
    """
    Configures a robust Selenium WebDriver by using the system-installed
    chromedriver, which is guaranteed to be compatible with the system's architecture.
    """
    print("\n--- Setting up Chrome WebDriver ---")
    print(f"System Architecture: {platform.machine()}")

    # This is the standard, correct path for the driver installed via apt on Ubuntu
    DRIVER_PATH = "/usr/bin/chromedriver" 
    
    if not os.path.exists(DRIVER_PATH):
        print(f"❌ ERROR: Chromedriver not found at '{DRIVER_PATH}'.")
        print("   Attempting to install it now...")
        if not setup_system():
            print("   Automatic installation failed. Please run 'sudo apt-get install -y chromium-chromedriver' manually.")
            return None
    
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    
    # Essential options for stability in server/headless environments
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # Explicitly point Selenium's service to the correct driver path
        service = ChromeService(executable_path=DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ WebDriver initialized successfully using the system's driver.")
        return driver
    except Exception as e:
        print(f"❌ An unexpected error occurred during WebDriver initialization: {e}")
        raise

# --- Main Execution Block ---
if __name__ == "__main__":
    # The script now handles all steps internally.
    clear_webdriver_cache()
    
    web_driver = None
    try:
        web_driver = setup_driver(headless=True)
        
        print("\n--- Running Test Navigation ---")
        web_driver.get("http://example.com")
        
        time.sleep(1) # Allow page to load
        
        print(f"Page Title: {web_driver.title}")
        print("\n✅ Script completed successfully!")
        
    except Exception:
        print("\n--- SCRIPT FAILED ---")

    finally:
        if web_driver:
            print("\nClosing WebDriver.")
            web_driver.quit()

