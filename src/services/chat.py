"""Chat completion service module."""

import json
import logging
from typing import Dict, List, Any, Optional
import httpx

from src.core.client import get_client
from src.core.auth import get_token
from src.config.settings import COPILOT_CHAT_URL, CHAT_HEADERS
from src.models.requests import Message
from src.services.models import validate_chat_request

logger = logging.getLogger(__name__)


async def make_copilot_request(
    token: str,
    messages: List[Dict[str, Any]],
    model: str,
    stream: bool = False,
) -> httpx.Response:
    """Make an async POST request to GitHub Copilot's API for chat completions."""
    request_payload = {
        "messages": messages,
        "model": model,
        "stream": stream,
    }
    logger.debug(
        f"Making chat completion request: {json.dumps(request_payload, indent=2)}"
    )

    client = await get_client()
    headers = {**CHAT_HEADERS, "Authorization": f"Bearer {token}"}
    return await client.post(
        COPILOT_CHAT_URL,
        headers=headers,
        json=request_payload,
    )


async def process_messages(
    model: str = "claude-3.5-sonnet",
    messages: List[Message] = [],
    stream: bool = False,
) -> Optional[str]:
    """Process messages and get completion from the API."""
    # Convert Pydantic models to dict with formatted content and validate model
    messages_dict = [{"role": m.role, "content": m.formatted_content} for m in messages]
    await validate_chat_request(model)

    try:
        logger.debug(f"Processing messages: {json.dumps(messages_dict, indent=2)}")
        current_token = await get_token()

        resp = await make_copilot_request(current_token, messages_dict, model, stream)
        resp.raise_for_status()

        if not stream:
            # For non-streaming responses, read the full response
            data = resp.json()
            if not data.get("choices"):
                logger.error(f"Unexpected response structure: {data}")
                return None
            return data

        # For streaming responses, process chunks
        result_chunks = []
        async for line in resp.aiter_lines():
            if not line:
                continue
            try:
                if line.startswith("data: "):
                    chunk = line[6:]  # Remove "data: " prefix
                    if chunk.strip() == "[DONE]":  # Handle stream completion marker
                        logger.debug("Received stream completion marker")
                        continue

                    try:
                        json_data = json.loads(chunk)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON chunk: {e}")
                        logger.error(
                            f"Problematic chunk content: {chunk!r}"
                        )  # Use repr for exact content
                        continue

                    if json_data.get("choices"):
                        completion = (
                            json_data["choices"][0].get("delta", {}).get("content", "")
                        )
                        if completion:
                            result_chunks.append(completion)
                            logger.debug(f"Received chunk: {completion}")
                    else:
                        logger.warning(f"Unexpected JSON structure: {json_data}")
            except Exception as e:
                logger.error(f"Error processing response line: {e}")
                logger.error(
                    f"Problematic line content: {line!r}"
                )  # Use repr for exact content
                continue

        result = "".join(result_chunks) if result_chunks else None
        logger.debug(f"Chat completion final response: {result}")
        return result

    except httpx.RequestError as e:
        logger.error(f"Chat API request failed: {e}")
        return None
