"""FastAPI application setup module."""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.core.auth import token_refresh_task
from src.core.client import get_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    # Start token refresh task
    refresh_task = asyncio.create_task(token_refresh_task())

    yield  # Server is running

    # Cleanup
    refresh_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
        pass

    # Close HTTP client
    client = await get_client()
    await client.aclose()


# Initialize FastAPI application
app = FastAPI(
    lifespan=lifespan,
    title="Copilot Chat API",
    description="High-performance API for GitHub Copilot chat completions",
    version="1.0.0",
)

# Add middleware for better performance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
