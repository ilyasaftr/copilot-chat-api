"""Models service module."""

import logging
from typing import Dict, List, Optional
from cachetools import TTLCache
import httpx

from src.core.client import get_client
from src.core.auth import get_token
from src.config.settings import COPILOT_MODELS_URL, MODELS_HEADERS

logger = logging.getLogger(__name__)

# Cache models data for 30 minutes
models_cache = TTLCache(maxsize=1, ttl=30 * 60)
CACHE_KEY = "models"


class ModelValidationError(Exception):
    """Raised when model validation fails."""

    pass


async def fetch_models() -> List[Dict]:
    """Fetch models from GitHub Copilot API."""
    token = await get_token()
    client = await get_client()

    try:
        headers = {**MODELS_HEADERS, "Authorization": f"Bearer {token}"}
        resp = await client.get(
            COPILOT_MODELS_URL,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"]

    except httpx.RequestError as e:
        logger.error(f"Error fetching models: {e}")
        raise


async def get_models(force_refresh: bool = False) -> List[Dict]:
    """Get models with caching."""
    if not force_refresh and CACHE_KEY in models_cache:
        return models_cache[CACHE_KEY]

    models = await fetch_models()
    models_cache[CACHE_KEY] = models
    return models


def get_model_capabilities(model_id: str, models: List[Dict]) -> Optional[Dict]:
    """Get capabilities for a specific model."""
    for model in models:
        if model["id"] == model_id:
            return model["capabilities"]
    return None


async def validate_chat_request(model: str) -> None:
    """Validate chat request against model capabilities."""
    try:
        models = await get_models()
        capabilities = get_model_capabilities(model, models)

        if not capabilities:
            raise ModelValidationError(f"Model '{model}' not found")

        if capabilities["type"] != "chat":
            raise ModelValidationError(f"Model '{model}' does not support chat")

    except Exception as e:
        logger.error(f"Model validation error: {e}")
        raise ModelValidationError(str(e))
