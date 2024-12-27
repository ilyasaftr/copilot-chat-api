# Copilot Chat API 🤖

A FastAPI implementation for GitHub Copilot chat completions with token management.

Forked from [Copilot Chat API](https://github.com/jiaweing/copilot-chat-api).

## Features 🚀

- ✨ Multi-token support with automatic rotation and refresh
- 🔐 Optional bearer token authentication for API endpoints
- 🐳 Docker support with multi-platform builds (amd64, arm64)

## Requirements 📋

- 🐍 Python 3.13 or higher
- 👨‍💻 GitHub Copilot subscription

## Getting Started 🎯

### Obtaining Copilot Tokens 🔑
You need valid GitHub Copilot tokens to use this API. Follow these steps to get your tokens:

1. 🖥️ Run this command to get your device codes:
```bash
# 01ab8ac9400c4e429b23 is the client_id for VS Code
curl https://github.com/login/device/code -X POST -d 'client_id=01ab8ac9400c4e429b23&scope=user:email'
```

2. 🌐 Visit https://github.com/login/device/ and enter your `user_code`

3. 🔄 Get your access token by running:
```bash
curl https://github.com/login/oauth/access_token -X POST -d 'client_id=01ab8ac9400c4e429b23&scope=user:email&device_code=YOUR_DEVICE_CODE&grant_type=urn:ietf:params:oauth:grant-type:device_code'
```
Replace `YOUR_DEVICE_CODE` with the `device_code` from step 1

4. ✨ Save your `access_token` (starts with `gho_`) - You'll need this for the API!

## Installation 📦

### Docker 🐳
```bash
# Pull from GitHub Container Registry
docker pull ghcr.io/ilyasaftr/copilot-chat-api:latest

# Or build locally
docker build -t copilot-chat-api .
docker run -p 8081:8081 -e COPILOT_TOKENS='["token1","token2"]' copilot-chat-api
```

### Local Setup 💻
```bash
# With poetry (recommended)
poetry install
poetry run python -m src.cli start

# With pip
pip install -r requirements.txt
python -m src.cli start
```

## Configuration ⚙️

### Token Setup 🔒

```bash
# Environment variable options:
# 1. JSON array
export COPILOT_TOKENS='["token1", "token2"]'

# 2. Comma-separated
export COPILOT_TOKENS='token1,token2'

# 3. File (recommended for production)
export COPILOT_TOKENS_FILE=/path/to/tokens.txt
```

Token file format:
```text
# JSON array
["token1", "token2"]

# OR one per line
token1
token2
```

### Authentication 🔐

The API supports optional bearer token authentication:

1. Set `API_SECRET_KEY` to enable authentication:
```bash
export API_SECRET_KEY="your-secret-key"
```

2. Include the bearer token in requests:
```bash
curl -H "Authorization: Bearer your-secret-key" http://localhost:8081/v1/models
```

3. If `API_SECRET_KEY` is not set, endpoints remain publicly accessible without authentication.

### Environment Variables 🔧

| Variable | Description | Default |
|----------|-------------|---------|
| COPILOT_TOKENS | Token list | Required |
| COPILOT_TOKENS_FILE | Token file path | /app/tokens/copilot_tokens.txt |
| API_SECRET_KEY | Optional bearer token for API authentication | None |
| PORT | Server port | 8081 |
| WORKERS | Number of workers | 4 |
| LOG_LEVEL | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | INFO |

## API Reference 📚

### GET /v1/models 🔍
Returns available models.

Response:
```json
{
  "object": "list",
  "data": [
    {
      "id": "claude-3.5-sonnet",
      "capabilities": {
        "type": "chat"
      }
    }
  ]
}
```

### POST /v1/chat/completions 💬
Creates chat completion.

Request:
```json
{
  "model": "claude-3.5-sonnet",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "stream": false
}
```

Response:
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    }
  }]
}
```

## Docker Deployment 🚢

### Basic Run ▶️
```bash
docker run -d \
  -p 8081:8081 \
  -e COPILOT_TOKENS='["token1","token2"]' \
  copilot-chat-api
```

### Using Token File 📄
```bash
# Create a directory for tokens
mkdir -p /path/to/tokens

# Create and populate your tokens file
echo '["token1","token2"]' > /path/to/tokens/copilot_tokens.txt

# Run with token file mounted
docker run -d \
  -p 8081:8081 \
  -v /path/to/tokens:/app/tokens \
  copilot-chat-api
```

### Docker Compose 🔄
```yaml
services:
  copilot-chat-api:
    build: .
    ports:
      - "8081:8081"
    volumes:
      # Ensure the tokens directory exists locally
      - /path/to/tokens:/app/tokens
    environment:
      - COPILOT_TOKENS_FILE=/app/tokens/custom_file.txt
      # - COPILOT_TOKENS=token1,token2
      - API_SECRET_KEY=your-secret-key  # Optional: Enable API authentication
    restart: unless-stopped
```

### Supported Platforms 💪
- 💻 linux/amd64 (x86_64)
- 🍎 linux/arm64/v8 (Apple Silicon, other ARM64)

## Development 🛠️

### Command Line Options ⌨️
```bash
python -m src.cli start [OPTIONS]

Options:
  -p, --port INTEGER    Port number [default: 8081]
  -w, --workers INTEGER Number of workers [default: 4]
  --reload             Enable auto-reload
```

## Disclaimer ⚠️

This is an unofficial API implementation. Use in compliance with GitHub's terms of service and your Copilot subscription agreement.

## License 📝

MIT License
