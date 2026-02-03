# Next Steps (After Crimeo API Testing)

## Two Helper Functions We Need to Build

### 1. Route Point Sampler (Google Maps)

**The problem**: The Crimeo API takes a single lat/lon + radius. Our product analyzes an entire route. A route is a line, not a point. We need to turn that line into multiple points so we can query crime data along the full path.

**What Google Maps gives us**: When you request directions, the response includes an `overview_polyline` -- an encoded string that represents the full route path as a series of GPS coordinates.

**What we need to build**: A helper function that:
1. Takes the encoded polyline from Google Maps
2. Decodes it into raw GPS coordinates (using the `polyline` Python library)
3. Samples points at regular intervals (every 1.5 miles) along the decoded path
4. Returns a list of `{lat, lon}` points to feed into Crimeo

**Why 1.5 mile intervals**: Each Crimeo call uses a 1-mile radius. Points spaced 1.5 miles apart create overlapping circles (0.5mi overlap) with zero gaps along the route. This ensures we never miss a high-crime area.

**Testing needed**:
- Use `google-maps-services-python` (already in the repo) to make real direction requests
- Verify the polyline decoding works
- Verify the sampling interval produces the right number of points
- Test with short routes (2mi), medium (15mi), and long (50mi+)

**Key file to study**: `google-maps-services-python/googlemaps/directions.py` -- this is how we get routes with polylines.

**Relevant refactor_plan code**: `src/helper_functions/google_maps.py` -- Phase 2 of refactor_plan.md already sketches out `sample_points_from_polyline()` and `use_google_maps()`. Start there.

---

### 2. Date Range Calculator (Crimeo)

**The problem**: Crimeo requires `datetime_ini` (start of window) and `datetime_end` (end of window) in ISO 8601 format. We always want `datetime_end` = now, and `datetime_ini` = 6 months ago. These must be computed at runtime, not hardcoded.

**What we need to build**: A helper function that:
1. Gets the current date/time
2. Subtracts 6 months
3. Returns both dates formatted as `yyyy-MM-ddT00:00:00.000Z`

**This is simple** -- just `datetime.now()` and `timedelta(days=180)`. But it needs to be a shared utility so both the test scripts and the MCP server use the same logic.

---

## Order of Operations

1. **Now**: Run `src/tests/test_crimeo_api.py` -- verify Crimeo API works and analyze the JSON output
2. **Next**: Test Google Maps directions API -- get a real polyline, decode it, verify we can sample points
3. **Then**: Build both helper functions
4. **Finally**: Wire them into the Crime MCP Server (Phase 1 of refactor_plan.md)
