"""Request models for API endpoints."""

import logging
import re
from typing import Any, Dict, List
from pydantic import BaseModel, Field, field_validator, model_validator


logger = logging.getLogger(__name__)

# Define valid roles
VALID_ROLES = {"system", "user", "assistant"}

# Regex to match ANSI escape sequences
ANSI_ESCAPE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class Message(BaseModel):
    """Message model for chat completions."""

    role: str  # Validated by ChatCompletionRequest
    content: str | List[Dict[str, str]] | Dict[str, Any]

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: Any) -> Any:
        """Validate and sanitize content."""
        if not v or (isinstance(v, str) and not v.strip()):
            raise ValueError("Content cannot be empty")

        if isinstance(v, str):
            # Escape ANSI sequences properly
            v = ANSI_ESCAPE_PATTERN.sub(
                lambda m: m.group().encode("unicode_escape").decode(), v
            )
            return v.strip()

        if isinstance(v, list):
            return [
                {
                    "text": ANSI_ESCAPE_PATTERN.sub(
                        lambda m: m.group().encode("unicode_escape").decode(),
                        item.get("text", ""),
                    )
                }
                for item in v
                if isinstance(item, dict)
            ]

        if isinstance(v, dict):
            # If dict has text field, clean it
            if "text" in v:
                v["text"] = ANSI_ESCAPE_PATTERN.sub(
                    lambda m: m.group().encode("unicode_escape").decode(), v["text"]
                )
            return v

        # For any other type, convert to string and escape ANSI
        return ANSI_ESCAPE_PATTERN.sub(
            lambda m: m.group().encode("unicode_escape").decode(), str(v)
        )

    @property
    def formatted_content(self) -> str:
        """Format message content into string."""
        try:
            if isinstance(self.content, list):
                return "".join(
                    item["text"]
                    for item in self.content
                    if isinstance(item, dict) and "text" in item
                )
            return str(self.content)
        except Exception as e:
            logger.error(f"Error formatting content: {str(e)}")
            raise ValueError(f"Error formatting content: {str(e)}")


class ChatCompletionRequest(BaseModel):
    """Request model for chat completions endpoint."""

    model: str
    messages: List[Dict[str, Any]]
    stream: bool = Field(default=False)

    @model_validator(mode="after")
    def validate_messages(self) -> "ChatCompletionRequest":
        """Validate message array format and content."""
        if not self.messages:
            raise ValueError("Messages array cannot be empty")

        has_user = False
        for msg in self.messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                raise ValueError(
                    "Each message must be a dictionary with role and content"
                )

            role = msg["role"]
            if role not in VALID_ROLES:
                raise ValueError(
                    f"Invalid role: {role}. Must be one of: {', '.join(VALID_ROLES)}"
                )

            if role == "user":
                has_user = True

        if not has_user:
            raise ValueError("Messages must contain at least one user message")

        return self

    def get_formatted_messages(self) -> List[Message]:
        """Convert raw message dicts to Message objects."""
        try:
            return [Message(**msg) for msg in self.messages]
        except ValueError as e:
            logger.warning(f"Error formatting messages: {str(e)}")
            raise ValueError("Invalid message format")
