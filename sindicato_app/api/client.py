import httpx
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

class APIClient:
    """Centralized API client for all components"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')  # Remove trailing slash
        self.timeout = timeout
        self._client = None

    @asynccontextmanager
    async def session(self):
        """Context manager for API sessions"""
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            )
        try:
            yield self._client
        finally:
            pass  # Keep connection alive for reuse

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Union[List, Dict, None]:
        """GET request with error handling"""
        # Ensure endpoint starts with /
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'

        full_url = f"{self.base_url}{endpoint}"

        async with self.session() as client:
            try:
                print(f"API GET: {full_url} with params: {params}")  # Debug log
                response = await client.get(endpoint, params=params)
                response.raise_for_status()

                # Handle empty responses
                if response.status_code == 204 or not response.content:
                    return []

                data = response.json()
                print(f"API Response: {type(data)} with {len(data) if isinstance(data, list) else 'dict'} items")  # Debug log
                return data

            except httpx.HTTPStatusError as e:
                print(f"HTTP Error: {e.response.status_code} - {e.response.text}")  # Debug log
                raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"Request failed: {str(e)}")  # Debug log
                raise Exception(f"Request failed: {str(e)}")

    async def post(self, endpoint: str, data: Dict) -> Any:
        """POST request with error handling"""
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'

        async with self.session() as client:
            try:
                print(f"API POST: {self.base_url}{endpoint} with data: {data}")  # Debug log
                response = await client.post(endpoint, json=data)
                response.raise_for_status()

                if response.status_code == 204 or not response.content:
                    return True

                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"HTTP Error: {e.response.status_code} - {e.response.text}")  # Debug log
                raise Exception(f"API error: {e.response.status_code} - {e.response.text}")

    async def put(self, endpoint: str, data: Dict) -> Any:
        """PUT request with error handling"""
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'

        async with self.session() as client:
            try:
                response = await client.put(endpoint, json=data)
                response.raise_for_status()

                if response.status_code == 204 or not response.content:
                    return True

                return response.json()
            except httpx.HTTPStatusError as e:
                raise Exception(f"API error: {e.response.status_code} - {e.response.text}")

    async def delete(self, endpoint: str) -> bool:
        """DELETE request with error handling"""
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'

        async with self.session() as client:
            try:
                response = await client.delete(endpoint)
                response.raise_for_status()
                return True
            except httpx.HTTPStatusError as e:
                raise Exception(f"API error: {e.response.status_code} - {e.response.text}")

    async def close(self):
        """Close the client connection"""
        if self._client:
            await self._client.aclose()
            self._client = None