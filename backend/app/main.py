"""Main FastAPI application entry point for AutoTrack."""

from fastapi import FastAPI
import sys
import os

# Ensure the api package is importable
_api_dir = os.path.join(os.path.dirname(__file__), '..', 'api')
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

app = FastAPI(
    title="AutoTrack API",
    description="Staff management application for an autohaus/body-repair shop",
    version="0.1.0",
)

from api.customers import router as customers_router
from api.vehicles import router as vehicles_router

app.include_router(customers_router)
app.include_router(vehicles_router)


@app.get("/health", tags=["root"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "autotrack-api"}
