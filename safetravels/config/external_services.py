"""
API Configuration
=================

Centralized configuration for external APIs.
Loads from environment variables or .env file.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GoogleMapsConfig:
    """Google Maps API Configuration"""
    API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # API Endpoints (new versions)
    PLACES_URL = "https://places.googleapis.com/v1/places:searchNearby"
    ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
    GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
    
    @classmethod
    def get_headers(cls):
        """Get headers for new Google APIs"""
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": cls.API_KEY,
        }


class AzureOpenAIConfig:
    """Azure OpenAI Configuration"""
    API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    
    @classmethod
    def get_chat_url(cls):
        """Get the chat completions URL"""
        return f"{cls.ENDPOINT}openai/deployments/{cls.DEPLOYMENT}/chat/completions?api-version={cls.API_VERSION}"
    
    @classmethod
    def get_headers(cls):
        """Get headers for Azure OpenAI"""
        return {
            "Content-Type": "application/json",
            "api-key": cls.API_KEY,
        }


class Config:
    """Main configuration class"""
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    google_maps = GoogleMapsConfig
    azure_openai = AzureOpenAIConfig


# Export config instance
config = Config()
