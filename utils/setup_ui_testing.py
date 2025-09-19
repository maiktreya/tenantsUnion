# tests/setup_ui_testing.py
"""
Setup script for robust UI testing with Selenium.
Run this script to install and configure everything needed for UI testing.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_requirements():
    """Install the enhanced requirements for robust testing"""
    requirements_file = Path(__file__).parent / "requirements_robust.txt"

    if requirements_file.exists():
        print("Installing enhanced testing requirements...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        )
    else:
        print("Installing core requirements...")
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "pytest",
                "pytest-asyncio",
                "respx",
                "selenium>=4.0.0",
                "webdriver-manager",
                "requests",
                "nicegui",
            ]
        )


def setup_chrome_driver():
    """Set up Chrome driver using webdriver-manager"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        print("Setting up Chrome driver...")
        service = Service(ChromeDriverManager().install())

        # Test that Chrome driver works
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        driver.quit()

        print("Chrome driver setup successful!")
        return True

    except Exception as e:
        print(f"Chrome driver setup failed: {e}")
        print("You may need to install Chrome browser first.")
        return False


def create_test_config():
    """Create a pytest configuration for UI tests"""
    pytest_ini_content = """
[tool:pytest]
# Configuration for robust UI testing

# Markers for different test types
markers =
    ui: UI tests that require browser automation
    slow: Slow tests that take more time
    integration: Integration tests

# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Async support
asyncio_mode = auto

# Output options
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --capture=no

# Timeout for tests (useful for UI tests that might hang)
timeout = 300

# Parallel execution (install pytest-xdist for this)
# -n auto
"""

    config_file = Path(__file__).parent.parent / "pytest_ui.ini"
    with open(config_file, "w") as f:
        f.write(pytest_ini_content)

    print(f"Created pytest config: {config_file}")


def run_infrastructure_test():
    """Run a basic test to verify the setup works"""
    print("Running infrastructure test...")

    # Create a minimal test
    test_code = '''
import pytest
import sys
from pathlib import Path

# Add your project to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build" / "niceGUI"))

def test_imports():
    """Test that all required imports work"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import requests
        print("All imports successful!")
        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False

if __name__ == "__main__":
    test_imports()
'''

    test_file = Path(__file__).parent / "test_infrastructure_check.py"
    with open(test_file, "w") as f:
        f.write(test_code)

    try:
        subprocess.check_call([sys.executable, str(test_file)])
        print("Infrastructure test passed!")
        return True
    except subprocess.CalledProcessError:
        print("Infrastructure test failed!")
        return False
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


def main():
    """Main setup function"""
    print("Setting up robust UI testing environment...")
    print("=" * 50)

    success = True

    try:
        install_requirements()
        print("✓ Requirements installed")
    except Exception as e:
        print(f"✗ Requirements installation failed: {e}")
        success = False

    if setup_chrome_driver():
        print("✓ Chrome driver configured")
    else:
        print("✗ Chrome driver setup failed")
        success = False

    try:
        create_test_config()
        print("✓ Test configuration created")
    except Exception as e:
        print(f"✗ Config creation failed: {e}")
        success = False

    if run_infrastructure_test():
        print("✓ Infrastructure test passed")
    else:
        print("✗ Infrastructure test failed")
        success = False

    print("=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
        print("\nTo run the robust UI tests:")
        print("  pytest tests/test_ui_flows_robust.py -v")
        print("\nTo run specific UI tests:")
        print(
            "  pytest tests/test_ui_flows_robust.py::test_successful_login_and_logout_robust -v"
        )
        print("\nTo run with visible browser (for debugging):")
        print("  # Edit the ui_tester fixture to set headless=False")
    else:
        print("❌ Setup encountered some issues. Check the errors above.")
        print("\nCommon solutions:")
        print("1. Make sure Chrome browser is installed")
        print("2. Run: pip install --upgrade selenium webdriver-manager")
        print("3. Check your Python environment has the required packages")


if __name__ == "__main__":
    main()
