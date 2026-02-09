"""Entry point for running the Crime MCP server.

Usage:
    python -m src.MCP_Servers.crime_mcp
"""
from .server import run_server, logger


def main():
    """Main entry point to start the Crime MCP server."""
    try:
        logger.info("Starting Crime MCP Server...")
        print("--- Crime MCP Server --- (Press Ctrl+C to exit)")
        run_server()
    except KeyboardInterrupt:
        logger.info("Shutdown requested via KeyboardInterrupt.")
        print("\nShutting down server...")
    except Exception as e:
        logger.exception("An unexpected error occurred during server execution.")
        print(f"\nError: {e}")
    finally:
        logger.info("Server stopped.")
        print("Server stopped.")


if __name__ == "__main__":
    main()
