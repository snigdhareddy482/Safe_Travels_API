# API Module

This directory contains the backend API implementation using FastAPI.

## Purpose
- To expose endpoints for the SafeTravels application.
- To handle HTTP requests, input validation, and response formatting.

## Key Files
- `main.py`: Entry point for the FastAPI application.
- `routes.py`: API route definitions.
- `schemas.py`: Pydantic models for request/response schemas.

## Usage
Run the server:
```bash
uvicorn safetravels.api.main:app --reload
```
