# Build stage
FROM python:3.13.1-alpine AS builder

WORKDIR /app

# Install build dependencies and cleanup in single layer
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    && pip install --no-cache-dir poetry \
    && rm -rf /var/cache/apk/*

# Install dependencies
COPY pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi \
    && pip uninstall -y poetry \
    && find /usr/local -name '*.pyc' -delete \
    && find /usr/local -name '__pycache__' -delete \
    && rm -rf ~/.cache/pip ~/.cache/pypoetry

# Runtime stage
FROM python:3.13.1-alpine

WORKDIR /app

# Create directory for token file if needed
RUN mkdir -p /app/tokens

# Install runtime dependencies
RUN apk add --no-cache libstdc++ \
    && rm -rf /usr/local/lib/python3.13/test/ \
    /usr/local/lib/python3.13/lib2to3/ \
    /usr/local/lib/python3.13/idlelib/ \
    /usr/local/lib/python3.13/ensurepip/ \
    /usr/local/lib/python3.13/distutils/command/*.exe \
    /usr/local/share/python-wheels/ \
    /usr/share/man/ \
    /usr/local/share/doc/ \
    /var/cache/apk/*

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy only necessary application files
COPY src/__init__.py src/
COPY src/main.py src/
COPY src/cli.py src/
COPY src/api/ src/api/
COPY src/config/ src/config/
COPY src/core/ src/core/
COPY src/models/ src/models/
COPY src/services/ src/services/

# Set Python optimizations and disable bytecode generation
ENV PYTHONOPTIMIZE=2 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Default path for tokens file (can be overridden)
    COPILOT_TOKENS_FILE=/app/tokens/copilot_tokens.txt

# Create non-root user and set permissions
RUN adduser -D user \
    && chown -R user:user /app \
    && chmod -R 755 /app/tokens
USER user

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8081", "--http", "h11", "--loop", "uvloop"]
