"""
RAZIN API entrypoint.

Run locally with:   uvicorn app.main:app --reload
Run in Docker with: docker compose up --build
Then check:          curl http://localhost:8000/health
"""

from fastapi import FastAPI

from app.api.routes import evidence_router, scenes_router

app = FastAPI(title="RAZIN API", version="0.1.0")
app.include_router(scenes_router)
app.include_router(evidence_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Basic liveness check — confirms the API is up and reachable."""
    return {"status": "ok", "service": "razin-api"}
