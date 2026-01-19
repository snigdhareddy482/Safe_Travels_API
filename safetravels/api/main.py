#!/usr/bin/env python3
"""
SafeTravels API - Main Entry Point
===================================

This module initializes the FastAPI application and configures middleware.
It serves as the main entry point for the SafeTravels API server.

Endpoints:
    - GET /: API information and status
    - GET /health: Health check endpoint
    - /api/v1/*: API routes (see app.api.routes)

Usage:
    Development:
        uvicorn safetravels.api.main:app --reload
        
    Production:
        uvicorn safetravels.api.main:app --host 0.0.0.0 --port 8000

Author: SafeTravels Team
Created: January 2026
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

from safetravels.api.routes import router
from safetravels.core.app_settings import settings


# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

# API metadata for OpenAPI documentation
API_TITLE = "SafeTravels API"
API_DESCRIPTION = """
Real-time cargo theft prevention API with ML risk scoring and RAG explanations.

## Features

* **Risk Assessment**: Get 1-10 risk scores for any location
* **Route Analysis**: Analyze theft risk along an entire route
* **Safe Stops**: Find secure parking locations nearby
* **Natural Language Queries**: Ask questions in plain English
* **Incident Reporting**: Report theft incidents to improve the system

## Data Sources

* FBI Uniform Crime Reports (UCR)
* DOT Truck Stop Parking Survey
* CargoNet theft statistics
"""
API_VERSION = "0.1.0"


# =============================================================================
# APPLICATION INITIALIZATION
# =============================================================================

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# CORS middleware for cross-origin requests
# Note: In production, replace allow_origins=["*"] with specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# API ROUTES
# =============================================================================

# Include versioned API routes
app.include_router(router, prefix="/api/v1")


# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """
    API root endpoint.
    
    Returns basic API information including name, version, and 
    documentation URL.
    
    Returns:
        Dictionary with API name, version, status, and docs URL.
    """
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring.
    
    Used by load balancers and monitoring systems to verify
    the API is responding.
    
    Returns:
        Dictionary with status "healthy".
    """
    return {"status": "healthy"}


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    """Run the API server directly using uvicorn."""
    import uvicorn
    
    # Server configuration
    HOST = "0.0.0.0"
    PORT = 8000
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info" if not settings.debug else "debug"
    )
