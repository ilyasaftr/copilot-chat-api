"""Main entry point for the application."""

import sys
import uvicorn

# Import routes to register them with FastAPI
from src.api import routes  # noqa: F401
from src.core.app import app

if __name__ == "__main__":
    # Get the port from command line
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

    # Run the server
    uvicorn.run(
        app,  # Pass app instance directly
        host="0.0.0.0",
        port=port,
        workers=4,  # Multiple workers for better concurrency
        reload=False,  # Disable auto-reload in production
        http="h11",  # Modern HTTP/1.1 implementation
        loop="uvloop",  # High-performance event loop
    )
