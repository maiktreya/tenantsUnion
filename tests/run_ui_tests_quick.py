# tests/run_ui_tests_quick.py
"""
Quick runner for the simple UI tests.
This script will install dependencies and run the threading-based UI tests.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_requirements():
    """Install basic requirements for UI testing"""
    requirements = [
        "pytest",
        "pytest-asyncio",
        "respx",
        "selenium>=4.0.0",
        "requests",
        "nicegui",
    ]

    print("Installing requirements...")
    for req in requirements:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", req],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"✓ {req}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {req}")
            return False
    return True


def check_chrome():
    """Check if Chrome is available"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Try to create a driver instance
        driver = webdriver.Chrome(options=options)
        driver.quit()
        print("✓ Chrome browser and driver available")
        return True

    except Exception as e:
        print(f"✗ Chrome setup issue: {e}")
        print("\nTo fix this:")
        print("1. Install Google Chrome browser")
        print("2. Install chromedriver: pip install webdriver-manager")
        print("3. Or use: pip install chromedriver-autoinstaller")
        return False


def run_simple_tests():
    """Run the simple UI tests"""
    test_file = Path(__file__).parent / "test_ui_flows_simple.py"

    if not test_file.exists():
        print(f"✗ Test file not found: {test_file}")
        print("Make sure you have created the test_ui_flows_simple.py file")
        return False

    print(f"Running tests from: {test_file}")

    try:
        # Run specific tests with verbose output
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(test_file),
                "-v",
                "--tb=short",
                "-s",  # Don't capture output so we can see print statements
            ],
            check=True,
        )

        print("\n🎉 All UI tests passed!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code: {e.returncode}")
        return False


def run_basic_connectivity_test():
    """Run just the basic connectivity test to verify setup"""
    print("Running basic connectivity test...")

    test_code = '''
import pytest
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build" / "niceGUI"))

from test_ui_flows_simple import SimpleUITester
import threading
import time

def test_basic_setup():
    """Quick test to verify Chrome and basic setup works"""
    # Test Chrome driver
    tester = SimpleUITester("http://google.com", headless=True)
    try:
        tester.open("/")
        print("✓ Chrome driver works")
        url = tester.get_url()
        print(f"✓ Navigation works: {url}")
        return True
    except Exception as e:
        print(f"✗ Basic setup failed: {e}")
        return False
    finally:
        tester.close()

if __name__ == "__main__":
    success = test_basic_setup()
    sys.exit(0 if success else 1)
'''

    # Write and run the test
    test_file = Path(__file__).parent / "basic_setup_test.py"
    try:
        with open(test_file, "w") as f:
            f.write(test_code)

        result = subprocess.run(
            [sys.executable, str(test_file)], capture_output=True, text=True
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0

    finally:
        if test_file.exists():
            test_file.unlink()


def main():
    """Main function"""
    print("Quick UI Test Setup and Runner")
    print("=" * 40)

    # Step 1: Install requirements
    if not install_requirements():
        print("Failed to install requirements")
        return False

    # Step 2: Check Chrome
    if not check_chrome():
        print("Chrome setup failed")
        return False

    # Step 3: Run basic connectivity test
    if not run_basic_connectivity_test():
        print("Basic connectivity test failed")
        return False

    # Step 4: Ask user if they want to run full tests
    print("\n" + "=" * 40)
    choice = input("Run full UI tests? (y/n): ").lower().strip()

    if choice in ["y", "yes"]:
        return run_simple_tests()
    else:
        print("Setup complete! You can run the tests later with:")
        print("  pytest tests/test_ui_flows_simple.py -v")
        return True


if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup or tests failed. Check the output above for details.")
        sys.exit(1)
    else:
        print("\n✅ Setup complete!")
        sys.exit(0)
