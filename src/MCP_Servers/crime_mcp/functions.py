"""Crimeometer API implementation functions.

Contains the actual HTTP logic for calling Crimeometer endpoints.
Business logic is kept separate from the MCP server definition.

Endpoints used:
    GET /v1/incidents/stats      - Crime statistics (totals + breakdown by type)
    GET /v1/incidents/raw-data   - Individual crime incident records
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

import httpx

logger = logging.getLogger("crime-mcp")


# =============================================================================
# DATE RANGE HELPER
# =============================================================================

def get_date_range(days_back: int = 180) -> tuple[str, str]:
    """
    Compute datetime_ini and datetime_end for Crimeometer queries.

    Args:
        days_back: Number of days to look back (default 180 = ~6 months).

    Returns:
        Tuple of (datetime_ini, datetime_end) formatted as yyyy-MM-ddT00:00:00.000Z
    """
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days_back)

    fmt = "%Y-%m-%dT00:00:00.000Z"
    return start.strftime(fmt), now.strftime(fmt)


# =============================================================================
# CRIMEOMETER API CALLS
# =============================================================================

async def get_crime_stats(
    latitude: float,
    longitude: float,
    radius_miles: float,
    days_back: int,
    api_key: str,
    base_url: str,
    client: httpx.AsyncClient,
) -> Dict[str, Any]:
    """
    Get crime statistics for a location from Crimeometer.

    Calls GET /v1/incidents/stats with lat/lon/distance/date range.

    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        radius_miles: Search radius in miles
        days_back: Number of days to look back
        api_key: Crimeometer API key
        base_url: Crimeometer base URL
        client: Shared httpx async client

    Returns:
        Dict with total_incidents, report_types, and query metadata.
    """
    datetime_ini, datetime_end = get_date_range(days_back)

    url = f"{base_url}/incidents/stats"
    params = {
        "lat": latitude,
        "lon": longitude,
        "distance": f"{radius_miles}mi",
        "datetime_ini": datetime_ini,
        "datetime_end": datetime_end,
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    logger.info(f"Calling stats: ({latitude}, {longitude}) radius={radius_miles}mi")

    try:
        response = await client.get(url, params=params, headers=headers)

        if response.status_code == 429:
            return {
                "error": "Rate limit exceeded",
                "status_code": 429,
                "location": {"lat": latitude, "lon": longitude},
            }

        response.raise_for_status()
        data = response.json()

        # Crimeometer returns a list with one element
        if isinstance(data, list) and len(data) > 0:
            result = data[0]
            return {
                "total_incidents": result.get("total_incidents", 0),
                "report_types": result.get("report_types", []),
                "location": {"lat": latitude, "lon": longitude},
                "query": {
                    "radius_miles": radius_miles,
                    "datetime_ini": datetime_ini,
                    "datetime_end": datetime_end,
                },
            }

        return {
            "total_incidents": 0,
            "report_types": [],
            "location": {"lat": latitude, "lon": longitude},
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"Stats API HTTP error: {e.response.status_code}")
        return {
            "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            "status_code": e.response.status_code,
            "location": {"lat": latitude, "lon": longitude},
        }
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return {
            "error": str(e),
            "location": {"lat": latitude, "lon": longitude},
        }


async def get_crime_incidents(
    latitude: float,
    longitude: float,
    radius_miles: float,
    days_back: int,
    api_key: str,
    base_url: str,
    client: httpx.AsyncClient,
    page: int = 1,
) -> Dict[str, Any]:
    """
    Get raw crime incident data for a location from Crimeometer.

    Calls GET /v1/incidents/raw-data with lat/lon/distance/date range.

    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        radius_miles: Search radius in miles
        days_back: Number of days to look back
        api_key: Crimeometer API key
        base_url: Crimeometer base URL
        client: Shared httpx async client
        page: Page number for pagination (default 1)

    Returns:
        Dict with incidents list, total count, and query metadata.
    """
    datetime_ini, datetime_end = get_date_range(days_back)

    url = f"{base_url}/incidents/raw-data"
    params = {
        "lat": latitude,
        "lon": longitude,
        "distance": f"{radius_miles}mi",
        "datetime_ini": datetime_ini,
        "datetime_end": datetime_end,
        "page": page,
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    logger.info(f"Calling raw-data: ({latitude}, {longitude}) radius={radius_miles}mi page={page}")

    try:
        response = await client.get(url, params=params, headers=headers)

        if response.status_code == 429:
            return {
                "error": "Rate limit exceeded",
                "status_code": 429,
                "incidents": [],
                "total_incidents": 0,
                "location": {"lat": latitude, "lon": longitude},
            }

        response.raise_for_status()
        data = response.json()

        # Crimeometer returns a list with one element containing incidents
        if isinstance(data, list) and len(data) > 0:
            result = data[0]
            incidents = result.get("incidents", [])
            return {
                "total_incidents": result.get("total_incidents", 0),
                "total_pages": result.get("total_pages", 1),
                "incidents": incidents,
                "incidents_returned": len(incidents),
                "location": {"lat": latitude, "lon": longitude},
                "query": {
                    "radius_miles": radius_miles,
                    "datetime_ini": datetime_ini,
                    "datetime_end": datetime_end,
                    "page": page,
                },
            }

        return {
            "total_incidents": 0,
            "incidents": [],
            "incidents_returned": 0,
            "location": {"lat": latitude, "lon": longitude},
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"Raw-data API HTTP error: {e.response.status_code}")
        return {
            "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            "status_code": e.response.status_code,
            "incidents": [],
            "total_incidents": 0,
            "location": {"lat": latitude, "lon": longitude},
        }
    except Exception as e:
        logger.error(f"Raw-data API error: {e}")
        return {
            "error": str(e),
            "incidents": [],
            "total_incidents": 0,
            "location": {"lat": latitude, "lon": longitude},
        }
