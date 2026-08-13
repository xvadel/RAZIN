"""
API routes for RAZIN — Phase 1.

These are stubs matching RAZIN_Preliminary_Plan.md, Section 4.2 (API
layer). Each one is intentionally unimplemented (raises NotImplementedError)
until the piece it depends on exists — the comment on each route says
which build-sequence step unblocks it. Wire them up in that order:

    1. repo scaffold + Docker + /health           <- this file, done
    2. Pydantic schemas                            <- app/models/schemas.py, done
    3. SQLite + CRUD layer                         <- app/db/
    4. create_scene / upload_media                 <- storage + frame extraction
    5-9. analyze_scene                             <- app/cv/detector.py + app/agents/
   10. list_evidence / get_evidence                <- app/db/crud.py
"""

from fastapi import APIRouter, UploadFile

from app.models.schemas import SceneUploadRequest

scenes_router = APIRouter(prefix="/scenes", tags=["scenes"])
evidence_router = APIRouter(prefix="/evidence", tags=["evidence"])


@scenes_router.post("")
def create_scene(request: SceneUploadRequest):
    """Register a new scene/case."""
    # TODO(build step 3): persist via app/db/crud.py
    raise NotImplementedError


@scenes_router.post("/{scene_id}/upload")
async def upload_media(scene_id: str, file: UploadFile):
    """Accept an image or video for a scene; store it and (if video) extract frames."""
    # TODO(build step 4): save the upload; if it's video, extract frames with OpenCV
    raise NotImplementedError


@scenes_router.post("/{scene_id}/analyze")
async def analyze_scene(scene_id: str):
    """Run detection + the ReAct agent over all unanalyzed media for this scene."""
    # TODO(build steps 5-9): call app/cv/detector.py, then app/agents/react_agent.py
    raise NotImplementedError


@scenes_router.get("/{scene_id}/evidence")
def list_evidence(scene_id: str):
    """Return all logged evidence for a scene, including review-flagged items."""
    # TODO(build step 3): query via app/db/crud.py
    raise NotImplementedError


@evidence_router.get("/{evidence_id}")
def get_evidence(evidence_id: str):
    """Return a single evidence record."""
    # TODO(build step 3): query via app/db/crud.py
    raise NotImplementedError
