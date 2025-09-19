import pytest
import respx
from httpx import Response, ConnectError
from build.niceGUI.api.client import APIClient
from pathlib import Path
import sys

# Add the project root to the Python path to allow imports from the app source
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Marks all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@respx.mock
async def test_get_records_success(api_client: APIClient, mock_api_url: str):
    """
    Tests successful retrieval of records.
    Verifies the correct URL is called and the JSON response is parsed.
    """
    # Arrange
    table_name = "afiliadas"
    mock_response_data = [{"id": 1, "nombre": "Lucía García"}]
    # Mock the GET request
    respx.get(f"{mock_api_url}/{table_name}").mock(
        return_value=Response(200, json=mock_response_data)
    )

    # Act
    records = await api_client.get_records(table_name)

    # Assert
    assert records == mock_response_data


@respx.mock
async def test_get_records_with_filters(api_client: APIClient, mock_api_url: str):
    """
    Tests that filters are correctly encoded as query parameters in the URL.
    """
    # Arrange
    table_name = "usuarios"
    filters = {"rol": "eq.admin", "is_active": "is.true"}
    route = respx.get(f"{mock_api_url}/{table_name}", params=filters).mock(
        return_value=Response(200, json=[{"id": 1, "alias": "sumate"}])
    )

    # Act
    await api_client.get_records(table_name, filters=filters)

    # Assert
    assert route.called
    assert (
        str(route.calls.last.request.url)
        == f"{mock_api_url}/{table_name}?rol=eq.admin&is_active=is.true"
    )


@respx.mock
async def test_get_records_http_error(api_client: APIClient, mock_api_url: str):
    """
    Tests that the client gracefully handles an HTTP error (e.g., 500 Internal Server Error)
    and returns an empty list.
    """
    # Arrange
    table_name = "pisos"
    respx.get(f"{mock_api_url}/{table_name}").mock(return_value=Response(500))

    # Act
    records = await api_client.get_records(table_name)

    # Assert
    assert records == []


@respx.mock
async def test_create_record_success(api_client: APIClient, mock_api_url: str):
    """
    Tests successful creation of a new record.
    Verifies that the POST request is sent with the correct headers and body.
    """
    # Arrange
    table_name = "empresas"
    data_to_create = {"nombre": "Nueva Empresa SL", "cif_nif_nie": "B12345678"}
    mock_response_data = [{"id": 1, **data_to_create}]
    route = respx.post(f"{mock_api_url}/{table_name}").mock(
        return_value=Response(201, json=mock_response_data)
    )

    # Act
    # FIX: Unpack the (result, error) tuple returned by the method
    result, error = await api_client.create_record(table_name, data_to_create)

    # Assert
    assert route.called
    assert error is None  # Explicitly check that no error was returned
    assert result == mock_response_data[0]  # Assert against the result dictionary
    # Check that the Prefer header was sent to get the record back
    assert route.calls.last.request.headers["prefer"] == "return=representation"


@respx.mock
async def test_update_record_success(api_client: APIClient, mock_api_url: str):
    """
    Tests successful update of an existing record.
    Verifies the PATCH request and the query parameter for filtering.
    """
    # Arrange
    table_name = "bloques"
    record_id = 42
    data_to_update = {"estado": "En renovación"}
    route = respx.patch(f"{mock_api_url}/{table_name}?id=eq.{record_id}").mock(
        return_value=Response(200, json=[{"id": record_id, "estado": "En renovación"}])
    )

    # Act
    result = await api_client.update_record(table_name, record_id, data_to_update)

    # Assert
    assert route.called
    assert result["estado"] == "En renovación"
    assert result["id"] == record_id


@respx.mock
async def test_delete_record_success(api_client: APIClient, mock_api_url: str):
    """
    Tests successful deletion of a record.
    Verifies that the DELETE request is sent to the correct URL.
    """
    # Arrange
    table_name = "conflictos"
    record_id = 99
    route = respx.delete(f"{mock_api_url}/{table_name}?id=eq.{record_id}").mock(
        return_value=Response(204)  # No Content
    )

    # Act
    result = await api_client.delete_record(table_name, record_id)

    # Assert
    assert route.called
    assert result is True


@respx.mock
async def test_network_error_returns_empty(api_client: APIClient, mock_api_url: str):
    """
    Tests that network errors (like connection refused) are caught and handled gracefully.
    """
    # Arrange
    table_name = "nodos"
    respx.get(f"{mock_api_url}/{table_name}").mock(
        side_effect=ConnectError("Connection failed")
    )

    # Act
    records = await api_client.get_records(table_name)

    # Assert
    assert records == []
