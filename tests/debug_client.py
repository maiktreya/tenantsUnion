import httpx
import logging
from pathlib import Path
import sys

# Add the project root to the Python path to allow imports from the app source
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# --- ROBUST FIX ---
# Remove sys.path manipulation, as conftest.py now handles it.
# Change the fragile relative import to a clean, absolute one.
from build.niceGUI.api.client import (
    APIClient,
)  # Works because build/niceGUI is on the path

# --- END FIX ---

# Set up a logger for clear test output
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("DebugAPIClient")


class DebugAPIClient(APIClient):
    """
    A subclass of APIClient specifically for testing.
    It overrides error handling to log verbose details to the console
    instead of calling the UI's notify function.
    """

    async def get_records(self, *args, **kwargs):
        """Override get_records to provide detailed error logging."""
        try:
            # Call the original method from the parent class
            return await super().get_records(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            # Log the detailed error instead of showing a UI notification.
            detailed_error = e.response.json().get("message", e.response.text)
            log.error(
                f"\n--- API ERROR IN TEST ---\n"
                f"Request: {e.request.method} {e.request.url}\n"
                f"Status: {e.response.status_code}\n"
                f"Response: {detailed_error}\n"
                f"-------------------------"
            )
            return []
        except Exception as e:
            log.error(f"A non-HTTP exception occurred in the test client: {e}")
            return []

    # You can override create_record, update_record, etc., in the same way
    # if you need detailed logging for those operations as well.
