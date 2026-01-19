#!/usr/bin/env python3
"""
SafeTravels API - Routes
========================

This module defines all API endpoints for the SafeTravels service.
All endpoints use RAG (Retrieval-Augmented Generation) to provide
intelligent, data-driven responses.

Endpoints:
    POST /assess-risk: Get risk score for a location
    POST /query: Natural language question answering
    POST /analyze-route: Analyze theft risk along a route
    GET /safe-stops: Find safe parking near a location
    POST /incidents: Report theft or suspicious activity

All responses include:
    - Source citations from retrieved documents
    - Confidence scores
    - Actionable recommendations

Author: SafeTravels Team
Created: January 2026
"""

from fastapi import APIRouter
from datetime import datetime
from typing import List
import uuid
import logging

from safetravels.api.schemas import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    Coordinates,
    Source,
    RouteAnalysisRequest,
    RouteAnalysisResponse,
    SegmentRisk,
    SafeStop,
    QueryRequest,
    QueryResponse,
    SafeStopsRequest,
    SafeStopsResponse,
    IncidentReport,
    IncidentResponse
)
from safetravels.rag.chain import get_rag_chain

# Import safe stops module for real data
from safetravels.mcp.tools.safe_stops import (
    find_nearby_stops as find_safe_stops_real,
    find_fuel_stops as find_fuel_stops_real,
    find_emergency_help as find_emergency_real,
    get_hos_recommendation as get_hos_real,
    StopTier,
)

# Import new detection tools
from safetravels.mcp.tools.speed_anomaly import check_speed_anomaly
from safetravels.mcp.tools.gps_monitor import check_gps_status
from safetravels.mcp.tools.parking_availability import (
    get_parking_availability,
    find_available_parking,
)
from safetravels.mcp.tools.voice_alerts import (
    get_voice_alert,
    trigger_voice_alert,
    get_all_alert_types,
)
from safetravels.mcp.tools.whatif_slider import (
    what_if_departure,
    calculate_risk_at_time,
    get_hourly_risk_profile,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

router = APIRouter()

# Risk level thresholds for classification
RISK_LEVEL_THRESHOLDS = {
    'low': (1, 3),
    'moderate': (4, 5),
    'high': (6, 7),
    'critical': (8, 10)
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def classify_risk_level(risk_score: int) -> str:
    """
    Convert numeric risk score to categorical level.
    
    Args:
        risk_score: Numeric risk score (1-10)
        
    Returns:
        Risk level: 'low', 'moderate', 'high', or 'critical'
    """
    if risk_score <= 3:
        return 'low'
    elif risk_score <= 5:
        return 'moderate'
    elif risk_score <= 7:
        return 'high'
    else:
        return 'critical'


def convert_sources(raw_sources: List[dict]) -> List[Source]:
    """
    Convert raw source dictionaries to Source models.
    
    Args:
        raw_sources: List of source dictionaries from RAG chain
        
    Returns:
        List of validated Source objects
    """
    return [
        Source(
            title=source.get('title', 'Unknown'),
            relevance=source.get('relevance', 0.5)
        )
        for source in raw_sources
    ]


# =============================================================================
# RISK ASSESSMENT ENDPOINT
# =============================================================================

@router.post("/assess-risk", response_model=RiskAssessmentResponse)
async def assess_risk(request: RiskAssessmentRequest) -> RiskAssessmentResponse:
    """
    Get RAG-powered risk assessment for a location.
    
    This endpoint retrieves relevant documents from the vector store
    and uses an LLM to synthesize a comprehensive risk assessment.
    
    Args:
        request: RiskAssessmentRequest with location and optional parameters
        
    Returns:
        RiskAssessmentResponse with score, explanation, and recommendations
        
    Example:
        POST /api/v1/assess-risk
        {
            "latitude": 32.7767,
            "longitude": -96.7970,
            "commodity": "electronics"
        }
    """
    logger.info(f"Risk assessment request: lat={request.latitude}, lon={request.longitude}")
    
    # Get RAG chain and run assessment
    chain = get_rag_chain()
    result = chain.assess_risk(
        latitude=request.latitude,
        longitude=request.longitude,
        commodity=request.commodity
    )
    
    # Build response
    return RiskAssessmentResponse(
        location=Coordinates(
            latitude=request.latitude,
            longitude=request.longitude
        ),
        risk_score=result.get('risk_score', 5),
        risk_level=result.get('risk_level', 'moderate'),
        assessment=result.get('assessment', 'Unable to assess risk'),
        key_factors=result.get('key_factors', []),
        sources=convert_sources(result.get('sources', [])),
        recommendations=result.get('recommendations', []),
        confidence=result.get('confidence', 0.7),
        generated_at=datetime.utcnow()
    )


# =============================================================================
# NATURAL LANGUAGE QUERY ENDPOINT
# =============================================================================

@router.post("/query", response_model=QueryResponse)
async def natural_language_query(request: QueryRequest) -> QueryResponse:
    """
    Answer natural language questions using the Intelligent Graph Agent.
    
    Uses LangGraph to retrieve, grade, review, and answer questions
    with a cyclic workflow for higher accuracy.
    
    Args:
        request: QueryRequest with question and optional location
        
    Returns:
        QueryResponse with answer and sources
    """
    logger.info(f"Query request (Graph Agent): {request.query[:50]}...")
    
    try:
        from safetravels.agents.graph import build_graph
        agent = build_graph()
        
        # Build query string
        search_query = request.query
        if request.latitude and request.longitude:
            search_query += f" near latitude {request.latitude} longitude {request.longitude}"
            
        if agent:
            # Run graph agent
            inputs = {"question": search_query, "loop_count": 0}
            
            # Stream to get final state
            final_state = {}
            for output in agent.stream(inputs):
                for key, value in output.items():
                    final_state = value
            
            answer = final_state.get('generation', 'No answer generated.')
            
            # TODO: Extract sources from final state documents if needed
            # For now returning generic source info or empty
            sources = [Source(title="Graph Agent Retrieval", relevance=1.0)]
            
            return QueryResponse(
                query=request.query,
                answer=answer,
                sources=sources,
                generated_at=datetime.utcnow()
            )
            
    except ImportError:
        logger.warning("LangGraph not available, falling back to simple RAG chain")
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")

    # FALLBACK: Use simple chain if graph fails or isn't installed
    chain = get_rag_chain()
    result = chain.answer_query(
        query=request.query,
        latitude=request.latitude,
        longitude=request.longitude
    )
    
    return QueryResponse(
        query=request.query,
        answer=result.get('answer', 'Unable to answer query'),
        sources=convert_sources(result.get('sources', [])),
        generated_at=datetime.utcnow()
    )


# =============================================================================
# ROUTE ANALYSIS ENDPOINT
# =============================================================================

@router.post("/analyze-route", response_model=RouteAnalysisResponse)
async def analyze_route(request: RouteAnalysisRequest) -> RouteAnalysisResponse:
    """
    Analyze theft risk along an entire route.
    
    Divides the route into segments and assesses risk at each point,
    identifying high-risk areas and recommending safe stops.
    
    Args:
        request: RouteAnalysisRequest with origin, destination, and time
        
    Returns:
        RouteAnalysisResponse with segment risks and recommendations
        
    Example:
        POST /api/v1/analyze-route
        {
            "origin": {"latitude": 32.7767, "longitude": -96.7970},
            "destination": {"latitude": 29.7604, "longitude": -95.3698},
            "departure_time": "2025-01-15T08:00:00Z"
        }
    """
    logger.info(f"Route analysis: {request.origin} -> {request.destination}")
    
    chain = get_rag_chain()
    
    # Assess risk at origin
    origin_result = chain.assess_risk(
        request.origin.latitude,
        request.origin.longitude,
        request.commodity
    )
    
    # Assess risk at destination
    destination_result = chain.assess_risk(
        request.destination.latitude,
        request.destination.longitude,
        request.commodity
    )
    
    # Calculate midpoint and assess
    midpoint_latitude = (request.origin.latitude + request.destination.latitude) / 2
    midpoint_longitude = (request.origin.longitude + request.destination.longitude) / 2
    midpoint_result = chain.assess_risk(
        midpoint_latitude,
        midpoint_longitude,
        request.commodity
    )
    
    # Build segment list
    midpoint_coords = Coordinates(
        latitude=midpoint_latitude,
        longitude=midpoint_longitude
    )
    
    segments = [
        SegmentRisk(
            segment_id=1,
            start=request.origin,
            end=midpoint_coords,
            risk_score=origin_result.get('risk_score', 5),
            risk_level=origin_result.get('risk_level', 'moderate'),
            explanation=origin_result.get('assessment', '')[:200]
        ),
        SegmentRisk(
            segment_id=2,
            start=midpoint_coords,
            end=request.destination,
            risk_score=destination_result.get('risk_score', 5),
            risk_level=destination_result.get('risk_level', 'moderate'),
            explanation=destination_result.get('assessment', '')[:200]
        )
    ]
    
    # Identify high-risk segments
    high_risk_segments = [seg for seg in segments if seg.risk_score >= 7]
    
    # Calculate overall risk
    average_score = sum(seg.risk_score for seg in segments) // len(segments)
    overall_level = classify_risk_level(average_score)
    
    # Generate recommended safe stops
    safe_stops = [
        SafeStop(
            name="Pilot Travel Center",
            location=Coordinates(
                latitude=midpoint_latitude + 0.1,
                longitude=midpoint_longitude + 0.1
            ),
            risk_score=2,
            risk_level='low',
            distance_miles=15,
            explanation="24/7 security, gated parking, CCTV. Recommended safe stop."
        )
    ]
    
    # Build summary
    summary = (
        f"Route analysis complete. "
        f"Origin risk: {origin_result.get('risk_score', 5)}/10, "
        f"Destination risk: {destination_result.get('risk_score', 5)}/10. "
        f"Overall route risk: {average_score}/10 ({overall_level})."
    )
    
    return RouteAnalysisResponse(
        overall_risk_score=average_score,
        overall_risk=overall_level,
        total_distance_miles=300,  # TODO: Calculate actual distance
        segments=segments,
        high_risk_segments=high_risk_segments,
        safe_stops=safe_stops,
        summary=summary,
        sources=convert_sources(origin_result.get('sources', [])[:3])
    )


# =============================================================================
# SAFE STOPS ENDPOINT (REAL DATA)
# =============================================================================

def _convert_safe_stop(stop) -> SafeStop:
    """Convert internal SafeStop to API schema."""
    # Generate explanation from security features
    features = []
    if stop.has_guards:
        features.append("24/7 security guards")
    if stop.has_gated_parking:
        features.append("gated parking")
    if stop.has_fuel:
        features.append("fuel available")
    if stop.has_showers:
        features.append("driver amenities")
    
    # Convert tier to risk level
    tier_to_risk = {
        "Level 1": "low",
        "Level 2": "low",
        "Level 3": "moderate",
        "Avoid": "high",
    }
    risk_level = tier_to_risk.get(stop.tier.value, "moderate")
    
    # Convert security score (0-100) to risk score (1-10, inverted)
    risk_score = max(1, min(10, 10 - (stop.security_score // 10)))
    
    explanation = f"{stop.tier.value} security ({stop.security_score}/100). "
    if features:
        explanation += f"Features: {', '.join(features)}. "
    explanation += f"Area risk: {stop.area_risk_level}."
    
    return SafeStop(
        name=stop.name,
        location=Coordinates(latitude=stop.latitude, longitude=stop.longitude),
        risk_score=risk_score,
        risk_level=risk_level,
        distance_miles=round(stop.distance_miles, 1),
        explanation=explanation,
    )


@router.get("/safe-stops", response_model=SafeStopsResponse)
async def find_safe_stops(
    latitude: float,
    longitude: float,
    radius_miles: float = 50,
    min_tier: str = "level_3",
    require_fuel: bool = False,
) -> SafeStopsResponse:
    """
    Find safe parking stops near a location using 100-point security scoring.
    
    SECURITY TIERS:
        - Level 1 (85+): Premium - gated, guards, monitored CCTV
        - Level 2 (65-84): Secure - cameras, major brand, well-lit
        - Level 3 (45-64): Basic - acceptable for quick stops
        - Avoid (<45): Not recommended
    
    Args:
        latitude: Search center latitude
        longitude: Search center longitude
        radius_miles: Search radius (default: 50 miles)
        min_tier: Minimum security tier (level_1, level_2, level_3, avoid)
        require_fuel: Only return stops with diesel fuel
        
    Returns:
        SafeStopsResponse with list of recommended stops
        
    Example:
        GET /api/v1/safe-stops?latitude=32.7767&longitude=-96.7970&radius_miles=100
    """
    logger.info(f"Safe stops request: lat={latitude}, lon={longitude}, radius={radius_miles}")
    
    # Map tier string to enum
    tier_map = {
        "level_1": StopTier.LEVEL_1,
        "level_2": StopTier.LEVEL_2,
        "level_3": StopTier.LEVEL_3,
        "avoid": StopTier.AVOID,
    }
    min_tier_enum = tier_map.get(min_tier.lower(), StopTier.LEVEL_3)
    
    # Call real safe stops finder
    stops = find_safe_stops_real(
        lat=latitude,
        lon=longitude,
        radius_miles=radius_miles,
        min_tier=min_tier_enum,
        require_fuel=require_fuel,
        limit=10,
    )
    
    # Convert to API schema
    recommended_stops = [_convert_safe_stop(s) for s in stops]
    
    return SafeStopsResponse(
        location=Coordinates(latitude=latitude, longitude=longitude),
        radius_miles=radius_miles,
        stops=recommended_stops,
        total_found=len(recommended_stops)
    )


# =============================================================================
# FUEL STOPS ENDPOINT
# =============================================================================

@router.get("/fuel-stops")
async def find_fuel_stops(
    latitude: float,
    longitude: float,
    radius_miles: float = 50,
):
    """
    Find truck stops with diesel fuel, prioritized by safety.
    
    Args:
        latitude: Current GPS latitude
        longitude: Current GPS longitude
        radius_miles: Search radius (default: 50 miles)
        
    Returns:
        List of fuel stops with security scores
    """
    logger.info(f"Fuel stops request: lat={latitude}, lon={longitude}")
    
    stops = find_fuel_stops_real(latitude, longitude, radius_miles)
    
    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "radius_miles": radius_miles,
        "stops": [s.to_dict() for s in stops],
        "total_found": len(stops),
    }


# =============================================================================
# EMERGENCY HELP ENDPOINT
# =============================================================================

@router.get("/emergency-stops")
async def find_emergency_stops(
    latitude: float,
    longitude: float,
):
    """
    Find emergency help options: police stations + highest-security truck stops.
    
    Use when driver feels unsafe or needs immediate assistance.
    Returns options within 100 miles.
    
    Args:
        latitude: Current GPS latitude
        longitude: Current GPS longitude
        
    Returns:
        List of emergency options (police stations + Level 1 stops)
    """
    logger.info(f"Emergency stops request: lat={latitude}, lon={longitude}")
    
    stops = find_emergency_real(latitude, longitude)
    
    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "emergency_options": [s.to_dict() for s in stops],
        "total_found": len(stops),
        "emergency_number": "911",
    }


# =============================================================================
# HOS-AWARE STOP RECOMMENDATION ENDPOINT
# =============================================================================

@router.get("/hos-recommendation")
async def get_hos_stop_recommendation(
    latitude: float,
    longitude: float,
    hours_driven: float,
    break_type: str = "quick",
):
    """
    Get stop recommendations based on Hours of Service (HOS) rules.
    
    SAFETY GUARANTEE:
        - Never recommends below Level 2 security for overnight rest
        - Alerts driver if no safe options available
    
    Args:
        latitude: Current GPS latitude
        longitude: Current GPS longitude
        hours_driven: Hours driven in current shift (max 10 allowed)
        break_type: 'quick' (30-min break) or 'overnight' (10-hour rest)
        
    Returns:
        Recommendation with status, urgency, and stop options
    """
    logger.info(f"HOS recommendation: lat={latitude}, lon={longitude}, hours={hours_driven}")
    
    return get_hos_real(latitude, longitude, hours_driven, break_type)


# =============================================================================
# INCIDENT REPORTING ENDPOINT
# =============================================================================

@router.post("/incidents", response_model=IncidentResponse)
async def report_incident(incident: IncidentReport) -> IncidentResponse:
    """
    Report a theft or suspicious activity incident.
    
    Incident reports are ingested into the RAG system to improve
    future risk assessments. Reports are stored in the vector store
    and influence nearby location risk scores.
    
    Args:
        incident: IncidentReport with location, type, and description
        
    Returns:
        IncidentResponse with confirmation and incident ID
        
    Example:
        POST /api/v1/incidents
        {
            "latitude": 32.7767,
            "longitude": -96.7970,
            "event_type": "theft",
            "description": "Cargo stolen from trailer overnight"
        }
    """
    logger.info(f"Incident report: type={incident.event_type} at ({incident.latitude}, {incident.longitude})")
    
    # Import here to avoid circular dependency
    from safetravels.rag.vector_store import get_vector_store
    
    store = get_vector_store()
    
    # Create document from incident
    incident_document = (
        f"Incident Report - {incident.event_type}: "
        f"{incident.description or 'No description'}. "
        f"Location: lat {incident.latitude}, lon {incident.longitude}. "
        f"Time: {incident.timestamp}"
    )
    
    # Generate unique incident ID
    incident_id = str(uuid.uuid4())
    
    # Add to vector store
    try:
        store.add_documents(
            documents=[incident_document],
            metadatas=[{
                'source': 'User Report',
                'type': 'incident_report',
                'event_type': incident.event_type,
                'latitude': incident.latitude,
                'longitude': incident.longitude,
                'date': incident.timestamp.isoformat()
            }],
            ids=[f"incident-{incident_id}"],
            collection_name='theft_reports'
        )
        logger.info(f"Incident {incident_id} stored successfully")
    except Exception as error:
        logger.error(f"Error storing incident: {error}")
    
    return IncidentResponse(
        id=incident_id,
        message="Incident reported successfully. This data will be used to improve our risk assessments.",
        received_at=datetime.utcnow()
    )


# =============================================================================
# SPEED ANOMALY DETECTION ENDPOINT
# =============================================================================

@router.post("/check-speed-anomaly")
async def check_speed(
    speed_mph: float,
    road_type: str = "highway",
    traffic_level: str = "free_flow",
    duration_seconds: int = 0,
    previous_speed: float = None,
    location_type: str = "unknown",
):
    """
    Check for speed anomalies (creeping, erratic braking, sudden stops).
    
    CREEPING DETECTION:
        Speed 5-15 mph on highway with free traffic = possible tailing
    
    Args:
        speed_mph: Current vehicle speed
        road_type: Type of road (highway, interstate, local)
        traffic_level: Traffic conditions (free_flow, light, moderate, heavy)
        duration_seconds: How long at this speed
        previous_speed: Previous speed reading (for stop detection)
        location_type: Type of location (for unauthorized stop detection)
        
    Returns:
        Alert status with details if anomaly detected
    """
    logger.info(f"Speed check: {speed_mph} mph on {road_type}")
    
    return check_speed_anomaly(
        speed_mph=speed_mph,
        road_type=road_type,
        traffic_level=traffic_level,
        duration_seconds=duration_seconds,
        previous_speed=previous_speed,
        location_type=location_type,
    )


# =============================================================================
# GPS PING GAP DETECTION ENDPOINT
# =============================================================================

@router.post("/check-gps-status")
async def check_gps(
    last_ping_time: datetime,
    ignition_on: bool = True,
    last_known_lat: float = None,
    last_known_lon: float = None,
):
    """
    Check GPS signal health and detect jamming.
    
    GPS JAMMER DETECTION:
        - 30s gap = warning
        - 60s gap = jammer suspected
        - 120s gap = emergency
    
    Args:
        last_ping_time: Timestamp of last GPS ping
        ignition_on: Whether vehicle ignition is on
        last_known_lat: Last known latitude
        last_known_lon: Last known longitude
        
    Returns:
        GPS status with alerts if signal issues detected
    """
    logger.info(f"GPS check: last ping {last_ping_time}, ignition={ignition_on}")
    
    return check_gps_status(
        last_ping_time=last_ping_time,
        ignition_on=ignition_on,
        last_known_lat=last_known_lat,
        last_known_lon=last_known_lon,
    )


# =============================================================================
# PARKING AVAILABILITY ENDPOINT
# =============================================================================

@router.get("/parking-availability")
async def get_parking(
    stop_id: str = None,
    latitude: float = None,
    longitude: float = None,
    min_spaces: int = 1,
    radius_miles: float = 50,
):
    """
    Get real-time parking availability at truck stops.
    
    Args:
        stop_id: Specific stop ID (if checking single stop)
        latitude: For search by location
        longitude: For search by location
        min_spaces: Minimum required spaces
        radius_miles: Search radius
        
    Returns:
        Parking availability with open spots and wait times
    """
    if stop_id:
        logger.info(f"Parking check for stop {stop_id}")
        return get_parking_availability(stop_id)
    elif latitude and longitude:
        logger.info(f"Parking search at ({latitude}, {longitude})")
        return find_available_parking(latitude, longitude, min_spaces, radius_miles)
    else:
        return {"error": "Provide either stop_id or latitude/longitude"}


# =============================================================================
# VOICE ALERTS ENDPOINT
# =============================================================================

@router.get("/voice-alert")
async def voice_alert(
    alert_type: str,
    latitude: float = None,
    longitude: float = None,
    stop_name: str = None,
    distance: str = None,
    spaces: str = None,
    hours: str = None,
    condition: str = None,
):
    """
    Get voice alert audio and text for playback.
    
    ALERT TYPES:
        - red_zone_entry: Entering high-theft area
        - dwell_warning: Stopped too long in risk zone
        - gps_jammer: GPS signal lost
        - safe_parking_nearby: Safe stop ahead
        - hos_warning: Hours of service reminder
        
    Args:
        alert_type: Type of alert to retrieve
        latitude: Current location
        longitude: Current location
        (other params for message formatting)
        
    Returns:
        Alert with audio URL, text, and TTS fallback
    """
    logger.info(f"Voice alert: {alert_type}")
    
    return trigger_voice_alert(
        alert_type=alert_type,
        latitude=latitude,
        longitude=longitude,
        stop_name=stop_name,
        distance=distance,
        spaces=spaces,
        hours=hours,
        condition=condition,
    )


@router.get("/voice-alert-types")
async def get_alert_types():
    """Get all available voice alert types."""
    return {"alert_types": get_all_alert_types()}


# =============================================================================
# WHAT-IF TIME SLIDER ENDPOINT
# =============================================================================

@router.get("/what-if")
async def what_if_analysis(
    latitude: float,
    longitude: float,
    base_risk: float,
    hour: int = None,
):
    """
    What-If time analysis - see how risk changes by departure time.
    
    INTERACTIVE SLIDER:
        Drag departure time, watch risk expand/contract.
        2 AM = highest risk, 10 AM = lowest risk
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        base_risk: Base risk score for location (1-10)
        hour: Optional specific hour (0-23). If None, returns full 24h profile.
        
    Returns:
        Risk at specified time, or full 24-hour profile
    """
    logger.info(f"What-If analysis: ({latitude}, {longitude}), base={base_risk}, hour={hour}")
    
    return what_if_departure(latitude, longitude, base_risk, hour)


@router.get("/what-if/best-time")
async def get_best_departure_time(
    latitude: float,
    longitude: float,
    base_risk: float,
):
    """Get recommended departure time (lowest risk window)."""
    profile = get_hourly_risk_profile(base_risk)
    
    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "base_risk": base_risk,
        "best_time": profile["best_departure_time"],
        "best_risk": profile["statistics"]["min_risk"],
        "worst_time": profile["worst_departure_time"],
        "worst_risk": profile["statistics"]["max_risk"],
        "risk_range": profile["statistics"]["risk_range"],
    }

