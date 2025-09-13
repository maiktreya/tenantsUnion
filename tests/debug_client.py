# tests/debug_client.py
# Adjust the path to import from the project's source code
import sys
from pathlib import Path

# Add the project root to the Python path to allow imports from 'build'
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
import logging
from ..build.niceGUI.api.client import APIClient  # Import the original client
from ..build.niceGUI.api.validate import (
    TableValidator,
    validate_response,
)  # Import the original client

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
            # This is where the magic happens:
            # Log the detailed error instead of showing a UI notification.
            detailed_error = e.response.json().get("message", e.response.text)
            log.error(
                f"\n--- API ERROR IN TEST ---\n"
                f"Request: {e.request.method} {e.request.url}\n"
                f"Status: {e.response.status_code}\n"
                f"Response: {detailed_error}\n"
                f"-------------------------"
            )
            # Return the same empty list as the original to ensure
            # the test fails due to incorrect data, not a crashed client.
            return []
        except Exception as e:
            log.error(f"A non-HTTP exception occurred in the test client: {e}")
            return []

    # You can override create_record, update_record, etc., in the same way
    # if you need detailed logging for those operations as well.
