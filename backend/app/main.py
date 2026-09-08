"""Main FastAPI application entry point for AutoTrack."""

from fastapi import FastAPI

app = FastAPI(
    title="AutoTrack API",
    description="Staff management application for an autohaus/body-repair shop",
    version="0.1.0",
)


@app.get("/health", tags=["root"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "autotrack-api"}
