"""API routes module."""

import json
from fastapi import Depends
from fastapi.responses import StreamingResponse, JSONResponse

from src.core.app import app
from src.core.auth import get_token, get_auth_dependency
from src.models.requests import ChatCompletionRequest
from src.services.chat import make_copilot_request, process_messages
from src.services.models import get_models, ModelValidationError


@app.get("/v1/models", dependencies=[Depends(get_auth_dependency())])
async def list_models():
    """Get list of available models."""
    try:
        models = await get_models()
        return {"object": "list", "data": models}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/v1/chat/completions", dependencies=[Depends(get_auth_dependency())])
async def chat_completions(request: ChatCompletionRequest):
    """Handle chat completions endpoint with input validation."""
    try:
        messages = request.get_formatted_messages()
        messages_dict = [
            {"role": m.role, "content": m.formatted_content} for m in messages
        ]

        if not request.stream:
            response_content = await process_messages(
                model=request.model,
                messages=messages,
                stream=False,
            )
            if response_content is None:
                return JSONResponse({"error": "API request failed"}, status_code=500)

            return response_content

        # For streaming responses, delegate to the Copilot API's streaming
        current_token = await get_token()
        resp = await make_copilot_request(
            current_token,
            messages_dict,
            request.model,
            stream=True,
        )
        resp.raise_for_status()

        # Return streaming response that handles each chunk
        async def stream_chunks():
            try:
                async for line in resp.aiter_lines():
                    if line:  # Skip empty lines
                        yield f"{line}\n\n".encode("utf-8")
            except Exception as e:
                error_msg = f"data: {json.dumps({'error': str(e)})}\n\n"
                yield error_msg.encode("utf-8")
            finally:
                await resp.aclose()

        return StreamingResponse(stream_chunks(), media_type="text/event-stream")

    except ModelValidationError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
