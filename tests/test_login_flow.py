import pytest
import httpx
import time
from docker.models.containers import Container
from api.client import APIClient

# Marks all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

# =====================================================================
# This is an INTEGRATION TEST. It requires Docker to be running.
# It will:
# 1. Spin up the `db` and `server` (PostgREST) containers.
# 2. Wait for them to be healthy.
# 3. Run tests against the live API, which talks to the live database.
# 4. Tear down the containers after the tests are finished.
# =====================================================================


# Fixture to get the host IP for the Docker network
# This is needed so the tests running on the host can connect to the container
@pytest.fixture(scope="module")
def docker_host_ip(docker_services):
    return docker_services.get_container("db").attrs["NetworkSettings"]["IPAddress"]


# Fixture to provide a configured APIClient for integration tests
@pytest.fixture(scope="module")
def integration_api_client(docker_ip, docker_services):
    """
    Provides an APIClient instance configured to talk to the live, containerized
    PostgREST service.
    """
    # Get the mapped port for the PostgREST server
    port = docker_services.port_for("server", 3000)
    base_url = f"http://{docker_ip}:{port}"
    # Wait until the service is responsive
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.5, check=lambda: is_service_ready(base_url)
    )
    return APIClient(base_url=base_url)


# Helper function to check if the PostgREST service is ready
def is_service_ready(url: str) -> bool:
    try:
        response = httpx.get(url)
        # PostgREST returns 200 on the root URL when connected
        return response.status_code == 200
    except httpx.ConnectError:
        return False


# Main test class for integration tests
class TestApiDatabaseIntegration:

    async def test_api_is_live(self, integration_api_client: APIClient):
        """
        A simple smoke test to ensure the API is up and responding.
        """
        assert integration_api_client.client is None  # Should start lazy
        client = integration_api_client._ensure_client()
        response = await client.get(integration_api_client.base_url)
        assert response.status_code == 200

    async def test_crud_workflow_for_nodos(self, integration_api_client: APIClient):
        """
        Tests a full Create, Read, Update, Delete (CRUD) workflow.
        This confirms that the database and API are working together correctly.
        """
        # --- 1. CREATE ---
        new_nodo_data = {
            "nombre": "Test Nodo Integration",
            "descripcion": "A nodo created during an integration test",
        }
        created_nodo = await integration_api_client.create_record(
            "nodos", new_nodo_data
        )

        assert created_nodo is not None
        assert created_nodo["nombre"] == new_nodo_data["nombre"]
        nodo_id = created_nodo["id"]
        assert isinstance(nodo_id, int)

        # --- 2. READ (Get by ID) ---
        # Allow a moment for the DB to be consistent
        await asyncio.sleep(0.1)
        read_nodos = await integration_api_client.get_records(
            "nodos", filters={"id": f"eq.{nodo_id}"}
        )

        assert len(read_nodos) == 1
        read_nodo = read_nodos[0]
        assert read_nodo["descripcion"] == new_nodo_data["descripcion"]

        # --- 3. UPDATE ---
        update_data = {"descripcion": "Updated description"}
        updated_nodo = await integration_api_client.update_record(
            "nodos", nodo_id, update_data
        )

        assert updated_nodo is not None
        assert updated_nodo["descripcion"] == "Updated description"

        # --- 4. VERIFY UPDATE ---
        await asyncio.sleep(0.1)
        verified_nodos = await integration_api_client.get_records(
            "nodos", filters={"id": f"eq.{nodo_id}"}
        )
        assert verified_nodos[0]["descripcion"] == "Updated description"

        # --- 5. DELETE ---
        delete_success = await integration_api_client.delete_record("nodos", nodo_id)
        assert delete_success is True

        # --- 6. VERIFY DELETE ---
        await asyncio.sleep(0.1)
        deleted_check = await integration_api_client.get_records(
            "nodos", filters={"id": f"eq.{nodo_id}"}
        )
        assert len(deleted_check) == 0


# Need to import asyncio for the sleep call
import asyncio
