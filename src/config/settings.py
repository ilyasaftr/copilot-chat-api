"""Configuration settings module."""

import json
import logging
import os
from typing import List
from cachetools import TTLCache

# Get environment variables
API_SECRET_KEY = os.getenv(
    "API_SECRET_KEY"
)  # Optional secret key for API authorization
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Set up logging configuration
logging.basicConfig(
    level=LOG_LEVEL_MAP.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Token pool cache with 20 minute TTL for each token
token_pool_cache = TTLCache(maxsize=100, ttl=20 * 60)

# API endpoints
COPILOT_CHAT_URL = "https://api.individual.githubcopilot.com/chat/completions"
COPILOT_MODELS_URL = "https://api.individual.githubcopilot.com/models"

# Common headers shared across all requests
AUTH_HEADERS = {
    "accept": "application/json",
    "editor-version": "Neovim/0.6.1",
    "editor-plugin-version": "copilot.vim/1.16.0",
    "content-type": "application/json",
    "user-agent": "GithubCopilot/1.155.0",
    "accept-encoding": "gzip,deflate,br",
}

# Common Copilot API headers
COPILOT_API_HEADERS = {
    "User-Agent": "GitHubCopilotChat/0.23.2",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/json",
    "Copilot-Integration-Id": "vscode-chat",
    "Editor-Plugin-Version": "copilot-chat/0.23.2",
    "Editor-Version": "vscode/1.96.2",
    "Openai-Organization": "github-copilot",
    "X-Github-Api-Version": "2024-12-15",
    "Priority": "u=4, i",
}

# Endpoint-specific headers
CHAT_HEADERS = {
    **COPILOT_API_HEADERS,
    "Openai-Intent": "conversation-panel",
}

MODELS_HEADERS = {
    **COPILOT_API_HEADERS,
    "Openai-Intent": "model-access",
}


def load_tokens() -> List[str]:
    """Load Copilot tokens from environment variables or file."""
    # Try loading from environment variable first
    tokens_env = os.getenv("COPILOT_TOKENS")
    if tokens_env:
        try:
            # Try parsing as JSON array
            return json.loads(tokens_env)
        except json.JSONDecodeError:
            # Fall back to comma-separated string
            return [token.strip() for token in tokens_env.split(",") if token.strip()]

    # Try loading from file
    tokens_file = os.getenv("COPILOT_TOKENS_FILE")
    if tokens_file and os.path.exists(tokens_file):
        try:
            with open(tokens_file, "r") as f:
                content = f.read().strip()
                try:
                    # Try parsing as JSON array
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Fall back to line-separated tokens
                    return [
                        line.strip() for line in content.splitlines() if line.strip()
                    ]
        except Exception as e:
            logging.error(f"Error reading tokens file: {e}")

    raise ValueError(
        "No tokens found. Please set COPILOT_TOKENS environment variable "
        "with comma-separated tokens or JSON array, or set COPILOT_TOKENS_FILE "
        "with path to tokens file."
    )


# Initialize tokens
COPILOT_TOKENS = load_tokens()
