#!/usr/bin/env python3
"""
SafeTravels API - Configuration
===============================

This module defines application settings using Pydantic's BaseSettings.
All configuration values can be overridden via environment variables or
a .env file in the project root.

Configuration Categories:
    - API Settings: Application name, version, debug mode
    - Database: Connection URLs for persistent storage
    - LLM: OpenAI API configuration for text generation
    - Embeddings: Model for text-to-vector conversion
    - ChromaDB: Vector database settings
    - RAG: Retrieval-Augmented Generation parameters

Environment Variables:
    OPENAI_API_KEY: Required for LLM-powered risk assessments
    DEBUG: Set to "false" in production
    DATABASE_URL: Optional database connection string

Usage:
    from safetravels.core.app_settings import settings
    
    api_key = settings.openai_api_key
    model = settings.llm_model

Author: SafeTravels Team
Created: January 2026
"""

from pydantic_settings import BaseSettings
from typing import Optional


# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    
    All settings can be overridden by setting the corresponding
    environment variable (uppercase, with underscores).
    
    Attributes:
        app_name: Display name of the application
        debug: Enable debug mode for development
        api_version: API version prefix (e.g., "v1")
        database_url: Optional database connection string
        openai_api_key: API key for OpenAI services
        llm_model: OpenAI model to use for text generation
        embedding_model: Sentence transformer model for embeddings
        chroma_persist_dir: Directory for ChromaDB persistence
        chroma_collection_name: Default collection name
        retrieval_k: Number of documents to retrieve per query
        
    Example:
        >>> from safetravels.core.config import settings
        >>> print(settings.app_name)
        'SafeTravels API'
        >>> print(settings.llm_model)
        'gpt-4o-mini'
    """
    
    # -------------------------------------------------------------------------
    # API Settings
    # -------------------------------------------------------------------------
    app_name: str = "SafeTravels API"
    """Display name shown in API documentation and responses."""
    
    debug: bool = True
    """Enable debug mode. Set to False in production."""
    
    api_version: str = "v1"
    """API version prefix for route URLs."""
    
    # -------------------------------------------------------------------------
    # Database Configuration
    # -------------------------------------------------------------------------
    database_url: Optional[str] = None
    """Optional SQL database connection string for persistent storage."""
    
    # -------------------------------------------------------------------------
    # OpenAI / LLM Configuration
    # -------------------------------------------------------------------------
    openai_api_key: Optional[str] = None
    """OpenAI API key. Required for LLM-powered risk assessments."""
    
    llm_model: str = "gpt-4o-mini"
    """OpenAI model to use. Options: gpt-4o-mini, gpt-4o, gpt-4-turbo."""

    azure_openai_api_key: Optional[str] = None
    """Azure OpenAI API Key (if using Azure)."""

    azure_openai_endpoint: Optional[str] = None
    """Azure OpenAI Endpoint URL (e.g., https://my-resource.openai.azure.com/)."""

    azure_openai_api_version: str = "2023-12-01-preview"
    """Azure OpenAI API Version."""

    azure_deployment_name: Optional[str] = None
    """Azure OpenAI Deployment Name (required if using Azure)."""
    
    azure_openai_deployment: Optional[str] = None
    """Azure OpenAI Deployment Name (alternate name)."""
    
    # -------------------------------------------------------------------------
    # Google Maps Configuration
    # -------------------------------------------------------------------------
    google_maps_api_key: Optional[str] = None
    """Google Maps API Key for routes, places, geocoding."""
    
    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: str = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR."""
    
    # -------------------------------------------------------------------------
    # Embedding Configuration
    # -------------------------------------------------------------------------
    embedding_model: str = "all-MiniLM-L6-v2"
    """Sentence transformer model for text embeddings."""
    
    # -------------------------------------------------------------------------
    # ChromaDB Configuration
    # -------------------------------------------------------------------------
    chroma_persist_dir: str = "./chroma_db"
    """Directory path for ChromaDB persistent storage."""
    
    chroma_collection_name: str = "safetravels"
    """Default collection name for document storage."""
    
    # -------------------------------------------------------------------------
    # RAG Configuration
    # -------------------------------------------------------------------------
    retrieval_k: int = 5
    """Number of documents to retrieve per RAG query."""
    
    # -------------------------------------------------------------------------
    # Pydantic Configuration
    # -------------------------------------------------------------------------
    class Config:
        """Pydantic model configuration."""
        
        env_file = ".env"
        """Load environment variables from .env file."""
        
        env_file_encoding = "utf-8"
        """Encoding for .env file."""


# =============================================================================
# SINGLETON SETTINGS INSTANCE
# =============================================================================

settings = Settings()
"""Global settings instance. Import this to access configuration values."""
