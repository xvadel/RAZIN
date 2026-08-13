"""
RAZIN — AI-Assisted Crime-Scene Evidence Surveying System.
Main FastAPI application entrypoint.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables on startup
    init_db()
    yield


app = FastAPI(
    title="RAZIN Forensic AI API",
    description="Autonomous & AI-assisted preliminary crime-scene evidence surveying system",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(api_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Basic liveness probe confirming API is reachable."""
    return {"status": "ok", "service": "razin-api", "version": "0.1.0"}
