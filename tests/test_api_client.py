# tests/test_api_client.py

import pytest
import respx
from httpx import Response
from build.niceGUI.api.client import APIClient


@pytest.mark.asyncio
@respx.mock
async def test_get_records_success():
    """
    Tests the successful retrieval of records from the API.
    """
    # Arrange: Mock the API endpoint
    api_url = "http://localhost:3001"
    table_name = "afiliadas"
    mock_response = [{"id": 1, "nombre": "John Doe"}]

    respx.get(f"{api_url}/{table_name}").mock(
        return_value=Response(200, json=mock_response)
    )

    # Act: Call the method being tested
    api_client = APIClient(base_url=api_url)
    records = await api_client.get_records(table_name)

    # Assert: Check that the result is what we expect
    assert records == mock_response


@pytest.mark.asyncio
@respx.mock
async def test_get_records_http_error():
    """
    Tests how the client handles an HTTP error.
    """
    # Arrange
    api_url = "http://localhost:3001"
    table_name = "afiliadas"

    respx.get(f"{api_url}/{table_name}").mock(return_value=Response(500))

    # Act
    api_client = APIClient(base_url=api_url)
    records = await api_client.get_records(table_name)

    # Assert
    assert records == []
