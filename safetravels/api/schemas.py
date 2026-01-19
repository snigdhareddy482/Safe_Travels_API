#!/usr/bin/env python3
"""
SafeTravels API - Pydantic Schemas
==================================

This module defines all request and response models for the SafeTravels API.
Models use Pydantic for automatic validation, serialization, and documentation.

Schema Categories:
    - Core: Coordinates, Source (shared components)
    - Risk Assessment: Location-based risk scoring
    - Route Analysis: Multi-segment route risk evaluation
    - Natural Language Query: Free-text question answering
    - Safe Stops: Secure parking location finder
    - Incident Reporting: User-submitted theft reports

All risk scores use a standardized 1-10 scale:
    - 1-3: Low risk (safe for overnight parking)
    - 4-5: Moderate risk (use caution)
    - 6-7: High risk (avoid if possible)
    - 8-10: Critical risk (do not stop)

Author: SafeTravels Team
Created: January 2026
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# =============================================================================
# CORE SCHEMAS (Shared Components)
# =============================================================================

class Coordinates(BaseModel):
    """
    Geographic coordinates for a location.
    
    Used throughout the API to represent positions on Earth.
    Validates that coordinates are within valid ranges.
    
    Attributes:
        latitude: North-South position (-90 to 90)
        longitude: East-West position (-180 to 180)
        
    Example:
        >>> loc = Coordinates(latitude=32.7767, longitude=-96.7970)  # Dallas
    """
    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude in decimal degrees (-90 to 90)"
    )
    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude in decimal degrees (-180 to 180)"
    )


class Source(BaseModel):
    """
    Document source citation from RAG retrieval.
    
    Represents a document used to generate the API response,
    providing transparency about data sources.
    
    Attributes:
        title: Name or description of the source document
        relevance: Semantic similarity score (0.0 to 1.0)
        snippet: Optional excerpt from the document
    """
    title: str = Field(..., description="Name of the source document")
    relevance: float = Field(
        ...,
        ge=0,
        le=1,
        description="Relevance score (0=low, 1=high)"
    )
    snippet: Optional[str] = Field(
        None,
        description="Optional text excerpt from the source"
    )


# =============================================================================
# RISK ASSESSMENT SCHEMAS
# =============================================================================

class RiskAssessmentRequest(BaseModel):
    """
    Request for RAG-powered risk assessment at a location.
    
    Provide coordinates to get a comprehensive risk analysis
    with score, factors, and recommendations.
    
    Attributes:
        latitude: Location's latitude
        longitude: Location's longitude
        time: Optional datetime for time-based analysis
        commodity: Optional cargo type for commodity-specific risk
        query: Optional natural language question
        
    Example:
        >>> request = RiskAssessmentRequest(
        ...     latitude=32.7767,
        ...     longitude=-96.7970,
        ...     commodity="electronics"
        ... )
    """
    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Location latitude"
    )
    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Location longitude"
    )
    time: Optional[datetime] = Field(
        None,
        description="Optional time for temporal risk factors"
    )
    commodity: Optional[str] = Field(
        None,
        description="Cargo type (e.g., 'electronics', 'pharmaceuticals')"
    )
    query: Optional[str] = Field(
        None,
        description="Optional natural language question about the location"
    )


class RiskAssessmentResponse(BaseModel):
    """
    RAG-generated risk assessment result.
    
    Contains a risk score, natural language explanation,
    contributing factors, and actionable recommendations.
    
    Attributes:
        location: The assessed coordinates
        risk_score: Risk level 1-10 (10 being highest risk)
        risk_level: Categorical level (low/moderate/high/critical)
        assessment: Natural language explanation
        key_factors: List of main risk contributors
        sources: Documents used to generate the assessment
        recommendations: Actionable safety suggestions
        confidence: Model confidence in the assessment
        generated_at: Timestamp of response generation
    """
    location: Coordinates
    risk_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Risk score 1-10 (10=highest risk)"
    )
    risk_level: str = Field(
        ...,
        description="Category: low, moderate, high, or critical"
    )
    assessment: str = Field(
        ...,
        description="Natural language risk explanation"
    )
    key_factors: List[str] = Field(
        default_factory=list,
        description="Main factors contributing to the risk score"
    )
    sources: List[Source] = Field(
        default_factory=list,
        description="Documents used for this assessment"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable safety recommendations"
    )
    confidence: float = Field(
        default=0.8,
        ge=0,
        le=1,
        description="Model confidence (0=low, 1=high)"
    )
    generated_at: datetime = Field(
        ...,
        description="Timestamp when response was generated"
    )


# =============================================================================
# ROUTE ANALYSIS SCHEMAS
# =============================================================================

class RouteAnalysisRequest(BaseModel):
    """
    Request for route-level risk analysis.
    
    Provide origin and destination to analyze theft risk
    along the entire route, including segment-by-segment breakdown.
    
    Attributes:
        origin: Starting point coordinates
        destination: Ending point coordinates
        departure_time: When the trip will start
        commodity: Optional cargo type for specific analysis
    """
    origin: Coordinates = Field(..., description="Route starting point")
    destination: Coordinates = Field(..., description="Route ending point")
    departure_time: datetime = Field(..., description="Planned departure time")
    commodity: Optional[str] = Field(
        None,
        description="Cargo type for commodity-specific analysis"
    )


class SegmentRisk(BaseModel):
    """
    Risk information for a single route segment.
    
    Routes are divided into segments, each with its own
    risk assessment and explanation.
    
    Attributes:
        segment_id: Sequential segment number
        start: Segment starting point
        end: Segment ending point
        risk_score: Risk level 1-10 for this segment
        risk_level: Categorical risk level
        explanation: Why this segment has this risk level
    """
    segment_id: int = Field(..., description="Segment number (sequential)")
    start: Coordinates = Field(..., description="Segment start point")
    end: Coordinates = Field(..., description="Segment end point")
    risk_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Risk score 1-10 for this segment"
    )
    risk_level: str = Field(..., description="low/moderate/high/critical")
    explanation: str = Field(..., description="Reason for this risk level")


class SafeStop(BaseModel):
    """
    Safe parking stop recommendation.
    
    Represents a truck stop or rest area with security features
    that make it a safer choice for parking.
    
    Attributes:
        name: Stop name (e.g., "Pilot Travel Center #521")
        location: GPS coordinates
        risk_score: Safety rating 1-10 (lower is safer)
        risk_level: Categorical safety level
        distance_miles: Distance from query location
        explanation: Why this stop is considered safe
    """
    name: str = Field(..., description="Name of the truck stop/rest area")
    location: Coordinates = Field(..., description="Stop GPS coordinates")
    risk_score: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Risk score 1-10 (lower is safer)"
    )
    risk_level: str = Field(..., description="low/moderate/high/critical")
    distance_miles: float = Field(..., description="Distance from query point")
    explanation: str = Field(
        ...,
        description="Security features and safety rationale"
    )


class RouteAnalysisResponse(BaseModel):
    """
    Complete route risk analysis result.
    
    Provides overall route risk, segment-by-segment breakdown,
    high-risk segments, and recommended safe stops.
    
    Attributes:
        overall_risk_score: Average risk for entire route
        overall_risk: Categorical overall risk level
        total_distance_miles: Route length in miles
        segments: List of segment risk assessments
        high_risk_segments: Segments with score >= 7
        safe_stops: Recommended stops along the route
        summary: Natural language route summary
        sources: Documents used for the analysis
    """
    overall_risk_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Overall route risk 1-10"
    )
    overall_risk: str = Field(..., description="Overall risk category")
    total_distance_miles: float = Field(..., description="Total route distance")
    segments: List[SegmentRisk] = Field(
        ...,
        description="Risk assessment for each segment"
    )
    high_risk_segments: List[SegmentRisk] = Field(
        default_factory=list,
        description="Segments with risk score >= 7"
    )
    safe_stops: List[SafeStop] = Field(
        default_factory=list,
        description="Recommended safe parking stops"
    )
    summary: str = Field(..., description="Natural language route summary")
    sources: List[Source] = Field(
        default_factory=list,
        description="Documents used for this analysis"
    )


# =============================================================================
# NATURAL LANGUAGE QUERY SCHEMAS
# =============================================================================

class QueryRequest(BaseModel):
    """
    Natural language query request.
    
    Ask any question about cargo theft risk in plain English.
    Optionally provide coordinates for location context.
    
    Attributes:
        query: Natural language question
        latitude: Optional location latitude for context
        longitude: Optional location longitude for context
        
    Example:
        >>> request = QueryRequest(
        ...     query="What commodities are most targeted in Texas?",
        ...     latitude=32.7767,
        ...     longitude=-96.7970
        ... )
    """
    query: str = Field(
        ...,
        description="Natural language question about cargo theft"
    )
    latitude: Optional[float] = Field(
        None,
        description="Optional latitude for location context"
    )
    longitude: Optional[float] = Field(
        None,
        description="Optional longitude for location context"
    )


class QueryResponse(BaseModel):
    """
    RAG-generated answer to natural language query.
    
    Contains the answer, supporting sources, and timestamp.
    
    Attributes:
        query: Original question
        answer: Natural language answer
        sources: Documents used to generate the answer
        generated_at: Timestamp of response
    """
    query: str = Field(..., description="Original question")
    answer: str = Field(..., description="Natural language answer")
    sources: List[Source] = Field(
        default_factory=list,
        description="Documents used for this answer"
    )
    generated_at: datetime = Field(..., description="Response timestamp")


# =============================================================================
# SAFE STOPS SCHEMAS
# =============================================================================

class SafeStopsRequest(BaseModel):
    """
    Request for nearby safe parking stops.
    
    Attributes:
        latitude: Search center latitude
        longitude: Search center longitude
        radius_miles: Search radius (max 100 miles)
    """
    latitude: float = Field(..., description="Search center latitude")
    longitude: float = Field(..., description="Search center longitude")
    radius_miles: float = Field(
        default=25,
        le=100,
        description="Search radius in miles (max 100)"
    )


class SafeStopsResponse(BaseModel):
    """
    List of safe parking stops within search radius.
    
    Attributes:
        location: Search center point
        radius_miles: Search radius used
        stops: List of safe stop recommendations
        total_found: Number of stops found
    """
    location: Coordinates = Field(..., description="Search center")
    radius_miles: float = Field(..., description="Search radius used")
    stops: List[SafeStop] = Field(..., description="List of safe stops")
    total_found: int = Field(..., description="Number of stops found")


# =============================================================================
# INCIDENT REPORTING SCHEMAS
# =============================================================================

class IncidentReport(BaseModel):
    """
    User-submitted theft or suspicious activity report.
    
    Incident reports are ingested into the RAG system to
    improve future risk assessments.
    
    Attributes:
        latitude: Incident location latitude
        longitude: Incident location longitude
        event_type: Type of incident (theft, suspicious_activity, etc.)
        description: Optional details about the incident
        timestamp: When the incident occurred
        
    Example:
        >>> report = IncidentReport(
        ...     latitude=32.7767,
        ...     longitude=-96.7970,
        ...     event_type="theft",
        ...     description="Trailer broken into while driver was in restaurant"
        ... )
    """
    latitude: float = Field(..., description="Incident latitude")
    longitude: float = Field(..., description="Incident longitude")
    event_type: str = Field(
        ...,
        description="Type: theft, suspicious_activity, attempted_theft"
    )
    description: Optional[str] = Field(
        None,
        description="Details about the incident"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the incident occurred"
    )


class IncidentResponse(BaseModel):
    """
    Confirmation of incident report submission.
    
    Attributes:
        id: Unique incident identifier
        message: Confirmation message
        received_at: When the report was processed
    """
    id: str = Field(..., description="Unique incident ID")
    message: str = Field(..., description="Confirmation message")
    received_at: datetime = Field(..., description="Processing timestamp")
