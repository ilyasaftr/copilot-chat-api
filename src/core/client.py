"""HTTP client module."""

import httpx
from typing import Optional

# Global HTTP client instance
client: Optional[httpx.AsyncClient] = None


async def get_client() -> httpx.AsyncClient:
    """Get the HTTP client, ensuring it's initialized and connected."""
    global client
    if client is None or client.is_closed:
        client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
            http2=True,
        )
    return client
