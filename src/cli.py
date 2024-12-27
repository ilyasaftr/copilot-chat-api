"""Command-line interface for the application."""

import click
import uvicorn


@click.group()
def cli():
    """Copilot Chat API CLI."""
    pass


@cli.command()
@click.option("--port", "-p", default=8080, help="Port to run the server on")
@click.option("--workers", "-w", default=4, help="Number of worker processes")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def start(port: int, workers: int, reload: bool):
    """Start the API server."""
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        workers=workers if not reload else 1,  # Workers > 1 not supported with reload
        reload=reload,
        http="h11",
        loop="uvloop",
    )


if __name__ == "__main__":
    cli()
