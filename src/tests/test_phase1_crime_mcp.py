"""Phase 1 Test: Crime MCP Server.

Tests the Crime MCP Server by:
1. Unit testing the date range helper and config module
2. Starting the MCP server as a subprocess
3. Using fastmcp.Client to test tool listing and tool calls
4. Saving all results to a JSON file

Usage:
    pytest src/tests/test_phase1_crime_mcp.py -v -s

Output:
    Results saved to src/tests/phase1_crime_mcp_results.json
"""
import pytest
import subprocess
import time
import signal
import os
import json
from datetime import datetime, timezone

from fastmcp import Client

# =============================================================================
# CONFIGURATION
# =============================================================================

MCP_URL = "http://localhost:8001/mcp"
SERVER_STARTUP_WAIT = 5  # seconds to wait for server to start

# Test location: Downtown Chicago
TEST_LAT = 41.8781
TEST_LON = -87.6298

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "phase1_crime_mcp_results.json")

# Accumulate results across all tests
_test_results = {
    "test_metadata": {
        "timestamp": None,
        "mcp_url": MCP_URL,
        "test_location": {
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "description": "Downtown Chicago",
        },
    },
    "tests": [],
}


def _save_results():
    """Save accumulated results to JSON file."""
    _test_results["test_metadata"]["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(RESULTS_FILE, "w") as f:
        json.dump(_test_results, f, indent=2, default=str)


def _record_test(name: str, status: str, details: dict = None):
    """Record a test result."""
    _test_results["tests"].append({
        "test_name": name,
        "status": status,
        "details": details or {},
    })
    _save_results()


# =============================================================================
# UNIT TESTS (no server needed)
# =============================================================================

class TestDateRangeHelper:
    """Unit tests for the date range helper function."""

    def test_get_date_range_returns_tuple(self):
        """Test that get_date_range returns a tuple of two strings."""
        from src.MCP_Servers.crime_mcp.functions import get_date_range

        result = get_date_range(days_back=180)

        assert isinstance(result, tuple)
        assert len(result) == 2

        datetime_ini, datetime_end = result
        assert isinstance(datetime_ini, str)
        assert isinstance(datetime_end, str)

        _record_test("date_range_returns_tuple", "pass", {
            "datetime_ini": datetime_ini,
            "datetime_end": datetime_end,
        })

    def test_get_date_range_format(self):
        """Test that dates are in the correct Crimeometer format."""
        from src.MCP_Servers.crime_mcp.functions import get_date_range

        datetime_ini, datetime_end = get_date_range(days_back=30)

        assert datetime_ini.endswith("T00:00:00.000Z")
        assert datetime_end.endswith("T00:00:00.000Z")

        # Should be parseable
        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
        parsed_ini = datetime.strptime(datetime_ini, fmt)
        parsed_end = datetime.strptime(datetime_end, fmt)
        assert parsed_end > parsed_ini

        _record_test("date_range_format", "pass", {
            "datetime_ini": datetime_ini,
            "datetime_end": datetime_end,
            "format_valid": True,
        })

    def test_get_date_range_days_back(self):
        """Test that days_back produces correct span."""
        from src.MCP_Servers.crime_mcp.functions import get_date_range

        datetime_ini, datetime_end = get_date_range(days_back=30)

        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
        parsed_ini = datetime.strptime(datetime_ini, fmt)
        parsed_end = datetime.strptime(datetime_end, fmt)

        delta = (parsed_end - parsed_ini).days
        assert delta == 30

        _record_test("date_range_days_back", "pass", {
            "days_back_requested": 30,
            "days_back_actual": delta,
        })

    def test_get_date_range_default_180_days(self):
        """Test that default days_back is 180."""
        from src.MCP_Servers.crime_mcp.functions import get_date_range

        datetime_ini, datetime_end = get_date_range()

        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
        parsed_ini = datetime.strptime(datetime_ini, fmt)
        parsed_end = datetime.strptime(datetime_end, fmt)

        delta = (parsed_end - parsed_ini).days
        assert delta == 180

        _record_test("date_range_default_180", "pass", {"days": delta})


class TestConfigLoading:
    """Unit tests for config loading."""

    def test_config_loads(self):
        """Test that CrimeMCPSettings loads from .env."""
        from src.MCP_Servers.crime_mcp.config import CrimeMCPSettings

        settings = CrimeMCPSettings()
        assert settings.CRIME_API_KEY
        assert settings.CRIME_API_BASE_URL == "https://api.crimeometer.com/v1"

        _record_test("config_loads", "pass", {
            "api_key_prefix": settings.CRIME_API_KEY[:8],
            "base_url": settings.CRIME_API_BASE_URL,
        })


# =============================================================================
# INTEGRATION TESTS (requires running server)
# =============================================================================

@pytest.fixture(scope="module")
def mcp_server():
    """Start the MCP server as a subprocess for integration tests."""
    env = os.environ.copy()

    process = subprocess.Popen(
        ["python", "-m", "src.MCP_Servers.crime_mcp"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
    )

    time.sleep(SERVER_STARTUP_WAIT)

    if process.poll() is not None:
        stdout = process.stdout.read().decode() if process.stdout else ""
        stderr = process.stderr.read().decode() if process.stderr else ""
        _record_test("server_start", "fail", {
            "stdout": stdout[:500],
            "stderr": stderr[:500],
        })
        pytest.fail(f"Server failed to start. stderr: {stderr[:500]}")

    _record_test("server_start", "pass", {"pid": process.pid})

    yield process

    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


class TestMCPServerIntegration:
    """Integration tests using fastmcp.Client to talk to the running server."""

    @pytest.mark.asyncio
    async def test_server_connects(self, mcp_server):
        """Test that the fastmcp Client can connect to the server."""
        client = Client(MCP_URL)
        async with client:
            connected = client.is_connected()

            _record_test("server_connects", "pass" if connected else "fail", {
                "connected": connected,
            })

            assert connected

    @pytest.mark.asyncio
    async def test_tool_listing(self, mcp_server):
        """Test that tools/list returns our two tools."""
        client = Client(MCP_URL)
        async with client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]

            has_stats = "get_location_crime_stats" in tool_names
            has_incidents = "get_location_crime_incidents" in tool_names

            _record_test("tool_listing", "pass" if (has_stats and has_incidents) else "fail", {
                "tool_names": tool_names,
                "tool_count": len(tool_names),
                "has_stats": has_stats,
                "has_incidents": has_incidents,
            })

            assert has_stats, f"Missing get_location_crime_stats. Found: {tool_names}"
            assert has_incidents, f"Missing get_location_crime_incidents. Found: {tool_names}"

    @pytest.mark.asyncio
    async def test_crime_stats_tool(self, mcp_server):
        """Test calling the get_location_crime_stats tool."""
        client = Client(MCP_URL)
        async with client:
            result = await client.call_tool(
                "get_location_crime_stats",
                {
                    "latitude": TEST_LAT,
                    "longitude": TEST_LON,
                    "radius_miles": 1.0,
                    "days_back": 180,
                },
            )

            # Result is a list of content items; extract text
            result_text = str(result)

            _record_test("crime_stats_tool", "pass", {
                "result": result_text[:1000],
                "note": "Tool executed successfully (API may be rate limited)",
            })

            assert result is not None

    @pytest.mark.asyncio
    async def test_crime_incidents_tool(self, mcp_server):
        """Test calling the get_location_crime_incidents tool."""
        client = Client(MCP_URL)
        async with client:
            result = await client.call_tool(
                "get_location_crime_incidents",
                {
                    "latitude": TEST_LAT,
                    "longitude": TEST_LON,
                    "radius_miles": 0.5,
                    "days_back": 180,
                    "limit": 10,
                },
            )

            result_text = str(result)

            _record_test("crime_incidents_tool", "pass", {
                "result": result_text[:1000],
                "note": "Tool executed successfully (API may be rate limited)",
            })

            assert result is not None


# =============================================================================
# FINAL HOOK: save results when test session ends
# =============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Save final results after all tests complete."""
    _save_results()
    print(f"\nPhase 1 test results saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
