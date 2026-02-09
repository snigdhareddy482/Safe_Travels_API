"""Crime MCP Server Configuration.

Loads settings from environment variables / .env file.

Environment variables:
    CRIME_API_KEY: API key for Crimeometer
    CRIME_API_BASE_URL: Base URL (default: https://api.crimeometer.com/v1)
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class CrimeMCPSettings(BaseSettings):
    """Settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    CRIME_API_KEY: str
    CRIME_API_BASE_URL: str = "https://api.crimeometer.com/v1"
