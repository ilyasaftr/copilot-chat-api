"""Authentication and token management module."""

import asyncio
import logging
import random
import time
from typing import Optional, List, Callable, Awaitable
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx

from src.core.client import get_client
from src.config.settings import (
    AUTH_HEADERS,
    COPILOT_TOKENS,
    token_pool_cache,
    API_SECRET_KEY,
)

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def get_auth_dependency() -> Callable[[HTTPAuthorizationCredentials], Awaitable[None]]:
    """Get the appropriate auth dependency based on API_SECRET_KEY."""
    if API_SECRET_KEY:

        async def verify_api_key(
            credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
        ):
            if not credentials:
                raise HTTPException(
                    status_code=401,
                    detail="Missing bearer token",
                )
            if credentials.scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication scheme",
                )
            if credentials.credentials != API_SECRET_KEY:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid bearer token",
                )

        return verify_api_key

    # If no API_SECRET_KEY, return a pass-through dependency
    async def no_auth(
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    ):
        pass

    return no_auth


def is_token_invalid(token: str) -> bool:
    """Check if the token is invalid or expired."""
    if not token:
        return True

    exp_time = extract_exp_value(token)
    if exp_time is None:
        return True

    return exp_time <= int(time.time())


def extract_exp_value(token: str) -> Optional[int]:
    """Extract expiration time from token."""
    try:
        pairs = token.split(";")
        for pair in pairs:
            key, value = pair.split("=")
            if key.strip() == "exp":
                return int(value.strip())
    except (ValueError, AttributeError):
        pass
    return None


async def get_token() -> str:
    """Get a valid token from the pool."""
    # Get list of currently valid tokens from cache
    valid_tokens: List[str] = [
        token
        for token in COPILOT_TOKENS
        if token in token_pool_cache and not is_token_invalid(token_pool_cache[token])
    ]

    if valid_tokens:
        # Return a random valid token
        chosen_token = random.choice(valid_tokens)
        return token_pool_cache[chosen_token]

    # If no valid tokens in cache, try refreshing tokens
    for token in COPILOT_TOKENS:
        try:
            refreshed_token = await refresh_token(token)
            if refreshed_token:
                token_pool_cache[token] = refreshed_token
                return refreshed_token
        except Exception as e:
            logger.warning(f"Failed to refresh token: {e}")
            continue

    raise HTTPException(
        status_code=500,
        detail="No valid tokens available. Please check your token configuration.",
    )


async def refresh_token(token: str) -> Optional[str]:
    """Attempt to refresh a specific token."""
    try:
        client = await get_client()
        resp = await client.get(
            "https://api.github.com/copilot_internal/v2/token",
            headers={"authorization": f"token {token}", **AUTH_HEADERS},
        )
        resp.raise_for_status()
        token_data = resp.json()

        if "token" not in token_data:
            logger.warning(f"Invalid token response for {token[:10]}...")
            return None

        new_token = token_data["token"]
        if not isinstance(new_token, str):
            logger.warning(f"Invalid token type for {token[:10]}...")
            return None

        return new_token

    except httpx.RequestError as e:
        logger.error(f"Token refresh failed for {token[:10]}...: {e}")
        return None


async def token_refresh_task():
    """Background task to refresh tokens periodically."""
    while True:
        try:
            # Try to refresh each token
            for token in COPILOT_TOKENS:
                try:
                    refreshed = await refresh_token(token)
                    if refreshed:
                        token_pool_cache[token] = refreshed
                        logger.info(f"Successfully refreshed token {token[:10]}...")
                    else:
                        logger.warning(f"Failed to refresh token {token[:10]}...")
                except Exception as e:
                    logger.error(f"Error refreshing token {token[:10]}...: {e}")

            # Sleep for 20 minutes
            await asyncio.sleep(20 * 60)
        except Exception as e:
            logger.error(f"Error in token refresh task: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying
