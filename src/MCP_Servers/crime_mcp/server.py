"""Crime MCP Server.

Provides crime data tools for AI agents to analyze route safety.
Uses the Crimeometer API for crime statistics and incident data.

Running the Server:
    python -m src.MCP_Servers.crime_mcp
"""
import logging
import sys
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from fastmcp import FastMCP

from .config import CrimeMCPSettings
from .functions import get_crime_stats, get_crime_incidents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logger = logging.getLogger("crime-mcp")

# Global HTTP client - reused across requests
http_client: Optional[httpx.AsyncClient] = None

# Load settings from .env
settings = CrimeMCPSettings()


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    """Manages the lifecycle of the MCP server."""
    global http_client

    logger.info("Crime MCP server starting...")
    http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("HTTP client initialized")

    yield

    logger.info("Crime MCP server shutting down...")
    if http_client and not http_client.is_closed:
        await http_client.aclose()
        http_client = None
    logger.info("Cleanup complete")


# Initialize MCP server
mcp = FastMCP(
    name="crime-analysis",
    instructions=(
        "Crime data analysis tools for route safety assessment. "
        "Use these tools to query crime statistics and incidents "
        "at specific locations along a route."
    ),
    lifespan=lifespan,
)


@mcp.tool(
    description=(
        "Get crime statistics for a specific location. "
        "Returns total incidents and breakdown by crime type. "
        "Use this to assess the overall crime level at a point along a route."
    )
)
async def get_location_crime_stats(
    latitude: float,
    longitude: float,
    radius_miles: float = 1.0,
    days_back: int = 180,
) -> dict:
    """
    Query crime statistics for a geographic location.

    Args:
        latitude: GPS latitude of the location
        longitude: GPS longitude of the location
        radius_miles: Search radius in miles (default: 1.0)
        days_back: Number of days to look back (default: 180 = ~6 months)

    Returns:
        Dictionary containing:
        - total_incidents: Total crime count
        - report_types: Breakdown by offense type [{type, count}]
        - location: Queried coordinates
    """
    if not http_client:
        logger.error("HTTP client not initialized")
        return {"error": "Server not properly initialized"}

    try:
        result = await get_crime_stats(
            latitude=latitude,
            longitude=longitude,
            radius_miles=radius_miles,
            days_back=days_back,
            api_key=settings.CRIME_API_KEY,
            base_url=settings.CRIME_API_BASE_URL,
            client=http_client,
        )
        return result
    except Exception as e:
        logger.error(f"Crime stats error: {e}")
        return {"error": str(e)}


@mcp.tool(
    description=(
        "Get detailed crime incident data for a location. "
        "Returns individual crime reports with offense types, dates, and descriptions. "
        "Use this for deeper analysis of specific areas."
    )
)
async def get_location_crime_incidents(
    latitude: float,
    longitude: float,
    radius_miles: float = 0.5,
    days_back: int = 180,
    limit: int = 50,
) -> dict:
    """
    Query raw crime incident data for a location.

    Args:
        latitude: GPS latitude of the location
        longitude: GPS longitude of the location
        radius_miles: Search radius in miles (default: 0.5)
        days_back: Number of days to look back (default: 180 = ~6 months)
        limit: Maximum incidents to return (default: 50)

    Returns:
        Dictionary containing:
        - incidents: List of crime incidents with offense details
        - total_incidents: Total count in the area
        - incidents_returned: Count returned on this page
        - location: Queried coordinates
    """
    if not http_client:
        logger.error("HTTP client not initialized")
        return {"error": "Server not properly initialized"}

    try:
        result = await get_crime_incidents(
            latitude=latitude,
            longitude=longitude,
            radius_miles=radius_miles,
            days_back=days_back,
            api_key=settings.CRIME_API_KEY,
            base_url=settings.CRIME_API_BASE_URL,
            client=http_client,
        )
        # Apply limit
        if "incidents" in result and len(result["incidents"]) > limit:
            result["incidents"] = result["incidents"][:limit]
            result["incidents_returned"] = limit
        return result
    except Exception as e:
        logger.error(f"Crime incidents error: {e}")
        return {"error": str(e)}


def run_server():
    """Start the MCP server on port 8001."""
    logger.info("Starting Crime MCP server on port 8001...")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8001,
        path="/mcp",
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
