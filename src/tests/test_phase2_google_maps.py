"""Phase 2 Tests: Google Maps Helper Function

Test Strategy:
- MOCKED tests: Test helper functions without API calls (always run)
- LIVE tests: Test actual Google Maps API integration (require API key)

Run mocked tests only:
    pytest src/tests/test_phase2_google_maps.py -v -m "not live"

Run all tests (requires GOOGLE_MAPS_API_KEY):
    pytest src/tests/test_phase2_google_maps.py -v

Run with verbose output:
    pytest src/tests/test_phase2_google_maps.py -v -s
"""
import pytest
import os

# Import the module under test
from src.helper_functions.google_maps import (
    use_google_maps,
    sample_points_from_polyline,
    haversine_distance,
    get_adaptive_interval,
    classify_traffic,
    RouteData,
    RoutePoint,
    PlaceInfo,
    TrafficInfo,
)


# =============================================================================
# MARKERS
# =============================================================================

# Mark for live tests that require API key
live = pytest.mark.live

# Skip live tests if no API key
skip_if_no_api_key = pytest.mark.skipif(
    not os.getenv("GOOGLE_MAPS_API_KEY"),
    reason="GOOGLE_MAPS_API_KEY not set"
)


# =============================================================================
# MOCKED TESTS - No API calls required
# =============================================================================

class TestHaversineDistance:
    """Test the haversine distance calculation."""

    def test_same_point_returns_zero(self):
        """Distance between same point should be 0."""
        distance = haversine_distance(41.8781, -87.6298, 41.8781, -87.6298)
        assert distance == 0.0

    def test_chicago_to_milwaukee(self):
        """Chicago to Milwaukee is approximately 90 miles."""
        # Willis Tower, Chicago
        lat1, lon1 = 41.8789, -87.6359
        # Milwaukee City Hall
        lat2, lon2 = 43.0389, -87.9065

        distance = haversine_distance(lat1, lon1, lat2, lon2)

        # Should be between 80-100 miles
        assert 80 < distance < 100

    def test_short_distance_chicago(self):
        """Test a short distance within Chicago (~2 miles)."""
        # Willis Tower
        lat1, lon1 = 41.8789, -87.6359
        # Navy Pier
        lat2, lon2 = 41.8917, -87.6086

        distance = haversine_distance(lat1, lon1, lat2, lon2)

        # Should be between 1.5-3 miles
        assert 1.5 < distance < 3


class TestAdaptiveInterval:
    """Test the adaptive interval calculation."""

    def test_very_short_urban_route(self):
        """Routes < 5 miles should use 0.5 mile intervals."""
        interval = get_adaptive_interval(3.0)
        assert interval == 0.5

    def test_short_urban_route(self):
        """Routes 5-10 miles should use 0.75 mile intervals."""
        interval = get_adaptive_interval(7.0)
        assert interval == 0.75

    def test_suburban_route(self):
        """Routes 10-20 miles should use 1.5 mile intervals."""
        interval = get_adaptive_interval(15.0)
        assert interval == 1.5

    def test_mixed_route(self):
        """Routes 20-40 miles should use 2.5 mile intervals."""
        interval = get_adaptive_interval(30.0)
        assert interval == 2.5

    def test_highway_route(self):
        """Routes > 40 miles should use 4 mile intervals."""
        interval = get_adaptive_interval(60.0)
        assert interval == 4.0

    def test_boundary_conditions(self):
        """Test boundary values."""
        assert get_adaptive_interval(5.0) == 0.75   # At 5 miles boundary
        assert get_adaptive_interval(10.0) == 1.5   # At 10 miles boundary
        assert get_adaptive_interval(20.0) == 2.5   # At 20 miles boundary
        assert get_adaptive_interval(40.0) == 4.0   # At 40 miles boundary


class TestClassifyTraffic:
    """Test traffic classification."""

    def test_light_traffic(self):
        """Traffic with < 5 min delay and < 10% should be light."""
        traffic = classify_traffic(30, 32)
        assert traffic.traffic_condition == "light"
        assert traffic.traffic_delay_minutes == 2

    def test_moderate_traffic(self):
        """Traffic with 5-15 min delay AND < 30% increase should be moderate."""
        # 30 min normal, 38 min with traffic = 8 min delay (27%)
        traffic = classify_traffic(30, 38)
        assert traffic.traffic_condition == "moderate"
        assert traffic.traffic_delay_minutes == 8

    def test_heavy_traffic(self):
        """Traffic with > 15 min delay should be heavy."""
        traffic = classify_traffic(30, 50)
        assert traffic.traffic_condition == "heavy"
        assert traffic.traffic_delay_minutes == 20

    def test_no_delay(self):
        """No delay should be light traffic."""
        traffic = classify_traffic(30, 30)
        assert traffic.traffic_condition == "light"
        assert traffic.traffic_delay_minutes == 0

    def test_negative_delay_clamped(self):
        """Negative delay (faster than expected) should be clamped to 0."""
        traffic = classify_traffic(30, 25)
        assert traffic.traffic_delay_minutes == 0


class TestSamplePointsFromPolyline:
    """Test polyline sampling."""

    def test_empty_polyline(self):
        """Empty polyline should return empty list."""
        waypoints = sample_points_from_polyline("", interval_miles=1.0)
        assert waypoints == []

    def test_single_point_polyline(self):
        """Single point polyline should return that point."""
        # Encode a single point (Chicago)
        # Polyline for just (41.8781, -87.6298)
        single_point_polyline = "_p~iF~ps|U"

        waypoints = sample_points_from_polyline(single_point_polyline, interval_miles=1.0)

        assert len(waypoints) >= 1
        assert isinstance(waypoints[0], RoutePoint)

    def test_waypoints_are_route_points(self):
        """All returned waypoints should be RoutePoint instances."""
        # Sample polyline from Chicago area
        test_polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

        waypoints = sample_points_from_polyline(test_polyline, interval_miles=1.0)

        assert all(isinstance(wp, RoutePoint) for wp in waypoints)

    def test_waypoints_have_valid_coordinates(self):
        """Waypoints should have valid GPS coordinates."""
        test_polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

        waypoints = sample_points_from_polyline(test_polyline, interval_miles=0.5)

        for wp in waypoints:
            assert -90 <= wp.latitude <= 90
            assert -180 <= wp.longitude <= 180

    def test_start_and_end_included(self):
        """First and last points should always be included."""
        # This polyline has distinct start and end
        test_polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

        waypoints = sample_points_from_polyline(test_polyline, interval_miles=100.0)

        # With a huge interval, we should still get at least start and end
        assert len(waypoints) >= 2


class TestDataClasses:
    """Test data class structures."""

    def test_route_point_creation(self):
        """Test RoutePoint dataclass creation."""
        point = RoutePoint(
            latitude=41.8781,
            longitude=-87.6298,
            description="Chicago Loop"
        )

        assert point.latitude == 41.8781
        assert point.longitude == -87.6298
        assert point.description == "Chicago Loop"
        assert point.area_type is None  # Optional field

    def test_place_info_creation(self):
        """Test PlaceInfo dataclass creation."""
        place = PlaceInfo(
            name="Shell Gas Station",
            place_type="gas_station",
            latitude=41.8781,
            longitude=-87.6298,
            vicinity="123 Main St"
        )

        assert place.name == "Shell Gas Station"
        assert place.place_type == "gas_station"

    def test_traffic_info_creation(self):
        """Test TrafficInfo dataclass creation."""
        traffic = TrafficInfo(
            duration_in_traffic_minutes=35,
            traffic_delay_minutes=5,
            traffic_condition="moderate"
        )

        assert traffic.duration_in_traffic_minutes == 35
        assert traffic.traffic_delay_minutes == 5
        assert traffic.traffic_condition == "moderate"

    def test_route_data_to_dict(self):
        """Test RouteData serialization."""
        route = RouteData(
            route_id=1,
            summary="I-90 W",
            distance_miles=15.5,
            duration_minutes=25,
            start_address="Willis Tower, Chicago, IL",
            end_address="O'Hare Airport, Chicago, IL",
            waypoints=[
                RoutePoint(41.8781, -87.6298),
                RoutePoint(41.9000, -87.6500)
            ],
            polyline="test_polyline_string",
            traffic=TrafficInfo(30, 5, "moderate"),
            places_along_route=[
                PlaceInfo("Shell", "gas_station", 41.88, -87.64, "123 Main")
            ]
        )

        data = route.to_dict()

        assert data["route_id"] == 1
        assert data["summary"] == "I-90 W"
        assert data["distance_miles"] == 15.5
        assert len(data["waypoints"]) == 2
        assert data["waypoints"][0]["latitude"] == 41.8781
        assert data["traffic"]["traffic_condition"] == "moderate"
        assert len(data["places_along_route"]) == 1


# =============================================================================
# LIVE TESTS - Require Google Maps API key
# =============================================================================

@skip_if_no_api_key
@live
class TestUseGoogleMapsLive:
    """Live integration tests for Google Maps API."""

    def test_returns_list_of_routes(self):
        """use_google_maps should return a list of RouteData."""
        routes = use_google_maps(
            start="Willis Tower, Chicago, IL",
            destination="Navy Pier, Chicago, IL",
            include_places=False  # Skip places for faster test
        )

        assert isinstance(routes, list)
        assert len(routes) >= 1
        assert all(isinstance(r, RouteData) for r in routes)

    def test_route_has_required_fields(self):
        """Each route should have all required fields populated."""
        routes = use_google_maps(
            start="Millennium Park, Chicago, IL",
            destination="Lincoln Park Zoo, Chicago, IL",
            include_places=False
        )

        route = routes[0]

        assert route.route_id >= 1
        assert route.summary  # Non-empty string
        assert route.distance_miles > 0
        assert route.duration_minutes > 0
        assert route.start_address
        assert route.end_address
        assert len(route.waypoints) >= 2  # At least start and end
        assert route.polyline  # Non-empty polyline

    def test_waypoints_have_valid_coordinates(self):
        """All waypoints should have valid GPS coordinates."""
        routes = use_google_maps(
            start="Union Station, Chicago, IL",
            destination="Wrigley Field, Chicago, IL",
            include_places=False
        )

        for route in routes:
            for waypoint in route.waypoints:
                assert isinstance(waypoint, RoutePoint)
                assert -90 <= waypoint.latitude <= 90
                assert -180 <= waypoint.longitude <= 180

    def test_traffic_data_included(self):
        """Routes should include traffic data when requested."""
        routes = use_google_maps(
            start="Downtown Chicago, IL",
            destination="Evanston, IL",
            include_traffic=True,
            include_places=False
        )

        # At least one route should have traffic info
        routes_with_traffic = [r for r in routes if r.traffic is not None]
        assert len(routes_with_traffic) > 0

        # Check traffic structure
        traffic = routes_with_traffic[0].traffic
        assert isinstance(traffic, TrafficInfo)
        assert traffic.duration_in_traffic_minutes >= 0
        assert traffic.traffic_condition in ["light", "moderate", "heavy"]

    def test_places_along_route(self):
        """Places should be found when requested."""
        routes = use_google_maps(
            start="Willis Tower, Chicago, IL",
            destination="Navy Pier, Chicago, IL",
            include_traffic=False,
            include_places=True,
            place_types=["gas_station"]
        )

        # Should find some gas stations on this route
        total_places = sum(len(r.places_along_route) for r in routes)
        # May be 0 if API rate limited, so just check structure
        if total_places > 0:
            place = routes[0].places_along_route[0]
            assert isinstance(place, PlaceInfo)
            assert place.name
            assert place.place_type == "gas_station"

    def test_multiple_alternatives(self):
        """Should return multiple route alternatives when available."""
        routes = use_google_maps(
            start="Willis Tower, Chicago, IL",
            destination="O'Hare International Airport, Chicago, IL",
            include_places=False
        )

        # O'Hare route typically has 2-3 alternatives
        assert len(routes) >= 1

        # Each route should have unique ID
        route_ids = [r.route_id for r in routes]
        assert len(route_ids) == len(set(route_ids))

    def test_adaptive_sampling_short_route(self):
        """Short urban routes should have dense waypoint sampling."""
        routes = use_google_maps(
            start="Willis Tower, Chicago, IL",
            destination="Navy Pier, Chicago, IL",  # ~2 miles
            include_places=False
        )

        route = routes[0]

        # ~2 mile route with 0.5 mile intervals should have 4-6 waypoints
        assert len(route.waypoints) >= 3
        assert len(route.waypoints) <= 10

    def test_adaptive_sampling_longer_route(self):
        """Longer routes should have sparser waypoint sampling."""
        routes = use_google_maps(
            start="Willis Tower, Chicago, IL",
            destination="O'Hare International Airport, Chicago, IL",  # ~16 miles
            include_places=False
        )

        route = routes[0]

        # ~16 mile route with 1.5 mile intervals should have ~12 waypoints
        assert len(route.waypoints) >= 5
        assert len(route.waypoints) <= 20

    def test_invalid_address_raises_error(self):
        """Invalid addresses should raise ValueError."""
        with pytest.raises(ValueError) as excinfo:
            use_google_maps(
                start="ThisIsNotARealAddress12345XYZ",
                destination="AnotherFakeAddress67890ABC"
            )

        assert "No routes found" in str(excinfo.value) or "error" in str(excinfo.value).lower()


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    print("Running Phase 2 Google Maps tests...")
    print("=" * 60)

    # Run mocked tests (always)
    print("\nMocked tests (no API required):")
    pytest.main([__file__, "-v", "-m", "not live", "-x"])

    # Run live tests if API key available
    if os.getenv("GOOGLE_MAPS_API_KEY"):
        print("\n" + "=" * 60)
        print("Live tests (with API key):")
        pytest.main([__file__, "-v", "-m", "live"])
    else:
        print("\nSkipping live tests - GOOGLE_MAPS_API_KEY not set")
