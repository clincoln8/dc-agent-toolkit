import sys

import click


@click.group()
def cli() -> None:
    """DataCommons MCP CLI - Model Context Protocol server for Data Commons."""

@cli.command()
def hello() -> None:
    """Print a hello message."""
    click.echo("Hello from datacommons-mcp CLI!")

@cli.group()
def serve() -> None:
    """Serve the MCP server in different modes."""

@serve.command()
@click.option("--host", default="localhost", help="Host to bind.")
@click.option("--port", default=8080, help="Port to bind.", type=int)
@click.option("--reload", is_flag=True, help="Enable auto-reload on code changes.")
def http(host: str, port: int, reload: bool) -> None:
    """Start the MCP server in HTTP/SSE mode."""
    try:
        from datacommons_mcp.server import mcp

        click.echo("Starting DataCommons MCP server in HTTP mode")
        click.echo(f"Server URL: http://{host}:{port}")
        click.echo(f"SSE endpoint: http://{host}:{port}/sse")
        click.echo("Press CTRL+C to stop")

        mcp.run(host=host, port=port, transport="sse")

    except ImportError as e:
        click.echo(f"Error importing server: {e}", err=True)
        sys.exit(1)

@serve.command()
def stdio() -> None:
    """Start the MCP server in stdio mode."""
    try:
        from datacommons_mcp.server import mcp

        click.echo("Starting DataCommons MCP server in stdio mode", err=True)
        click.echo("Server is ready to receive requests via stdin/stdout", err=True)

        mcp.run(transport="stdio")

    except ImportError as e:
        click.echo(f"Error importing server: {e}", err=True)
        sys.exit(1)

def main() -> None:
    """Main entry point for the CLI."""
    cli()

