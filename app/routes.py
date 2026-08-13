"""
FastAPI route definitions for RAZIN.

Endpoints for managing scenes, uploading media, running AI detection/triage,
browsing evidence, human review, and serving media files.
"""

from pathlib import Path
import shutil
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Header, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.agent import analyze_scene
from app.config import API_KEY, ROOT_DIR, UPLOAD_DIR
from app.db import (
    add_media,
    create_scene as db_create_scene,
    get_evidence as db_get_evidence,
    get_scene as db_get_scene,
    list_evidence as db_list_evidence,
    list_scenes as db_list_scenes,
    mark_reviewed as db_mark_reviewed,
)
from app.schemas import AnalysisResponse, EvidenceItem, SceneResponse, SceneUploadRequest

api_router = APIRouter()


class ReviewRequest(BaseModel):
    notes: Optional[str] = None


def _check_auth(x_api_key: Optional[str] = Header(None)) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


# --- Scene Management ---

@api_router.post("/scenes", response_model=SceneResponse, tags=["scenes"])
def create_scene(request: SceneUploadRequest, x_api_key: Optional[str] = Header(None)) -> SceneResponse:
    """Register a new crime scene investigation."""
    _check_auth(x_api_key)
    existing = db_get_scene(request.scene_id)
    if existing:
        return existing
    return db_create_scene(request)


@api_router.get("/scenes", response_model=list[SceneResponse], tags=["scenes"])
def list_scenes(x_api_key: Optional[str] = Header(None)) -> list[SceneResponse]:
    """List all registered crime scenes."""
    _check_auth(x_api_key)
    return db_list_scenes()


@api_router.get("/scenes/{scene_id}", response_model=SceneResponse, tags=["scenes"])
def get_scene(scene_id: str, x_api_key: Optional[str] = Header(None)) -> SceneResponse:
    """Get details for a specific crime scene."""
    _check_auth(x_api_key)
    scene = db_get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    return scene


# --- Media Ingestion ---

@api_router.post("/scenes/{scene_id}/upload", tags=["media"])
async def upload_media(
    scene_id: str,
    file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None),
) -> dict:
    """Upload an image or video file for a specific crime scene."""
    _check_auth(x_api_key)
    scene = db_get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    scene_upload_dir = UPLOAD_DIR / scene_id
    scene_upload_dir.mkdir(parents=True, exist_ok=True)

    dest_path = scene_upload_dir / file.filename
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ext = dest_path.suffix.lower()
    file_type = "video" if ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"] else "image"

    media_id = add_media(scene_id, str(dest_path), file_type)
    return {
        "status": "uploaded",
        "media_id": media_id,
        "filename": file.filename,
        "file_type": file_type,
        "path": str(dest_path),
    }


@api_router.post("/scenes/{scene_id}/upload-batch", tags=["media"])
async def upload_batch(
    scene_id: str,
    files: list[UploadFile] = File(...),
    x_api_key: Optional[str] = Header(None),
) -> dict:
    """Upload multiple images or videos in a single batch."""
    _check_auth(x_api_key)
    scene = db_get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    uploaded = []
    scene_upload_dir = UPLOAD_DIR / scene_id
    scene_upload_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        dest_path = scene_upload_dir / file.filename
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        ext = dest_path.suffix.lower()
        file_type = "video" if ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"] else "image"
        media_id = add_media(scene_id, str(dest_path), file_type)
        uploaded.append({"media_id": media_id, "filename": file.filename, "file_type": file_type})

    return {"status": "batch_uploaded", "count": len(uploaded), "files": uploaded}


# --- Analysis & Agentic Pipeline ---

@api_router.post("/scenes/{scene_id}/analyze", response_model=AnalysisResponse, tags=["analysis"])
def run_scene_analysis(scene_id: str, x_api_key: Optional[str] = Header(None)) -> AnalysisResponse:
    """Run YOLO detection and ReAct agent triage on all unanalyzed media for the scene."""
    _check_auth(x_api_key)
    scene = db_get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    return analyze_scene(scene_id)


# --- Evidence Query & Review ---

@api_router.get("/scenes/{scene_id}/evidence", response_model=list[EvidenceItem], tags=["evidence"])
def list_evidence_for_scene(
    scene_id: str,
    requires_review: Optional[bool] = Query(None),
    x_api_key: Optional[str] = Header(None),
) -> list[EvidenceItem]:
    """Retrieve all logged evidence for a scene, optionally filtered by review flag."""
    _check_auth(x_api_key)
    return db_list_evidence(scene_id, requires_review=requires_review)


@api_router.get("/evidence/{evidence_id}", response_model=EvidenceItem, tags=["evidence"])
def get_evidence_item(evidence_id: UUID, x_api_key: Optional[str] = Header(None)) -> EvidenceItem:
    """Get full details of a single evidence record."""
    _check_auth(x_api_key)
    evidence = db_get_evidence(str(evidence_id))
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return evidence


@api_router.patch("/evidence/{evidence_id}/review", tags=["evidence"])
def review_evidence(
    evidence_id: UUID,
    request: ReviewRequest = ReviewRequest(),
    x_api_key: Optional[str] = Header(None),
) -> dict:
    """Mark an evidence item as human-reviewed and confirmed."""
    _check_auth(x_api_key)
    evidence = db_get_evidence(str(evidence_id))
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    db_mark_reviewed(str(evidence_id), notes=request.notes)
    return {"status": "reviewed", "evidence_id": str(evidence_id)}


# --- RAG Chatbot ---

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    scope: str = "scene"  # "scene" or "all"


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []


@api_router.post("/scenes/{scene_id}/chat", response_model=ChatResponse, tags=["chat"])
def chat_with_scene(
    scene_id: str,
    request: ChatRequest,
    x_api_key: Optional[str] = Header(None),
) -> ChatResponse:
    """Ask a question about evidence in a scene (or all scenes)."""
    _check_auth(x_api_key)
    scene = db_get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    from app.rag import chat as rag_chat

    target_scene = scene_id if request.scope == "scene" else None
    result = rag_chat(
        scene_id=target_scene,
        question=request.message,
        chat_history=request.history,
    )
    return ChatResponse(answer=result["answer"], sources=result.get("sources", []))


@api_router.post("/scenes/{scene_id}/reindex", tags=["chat"])
def reindex_scene(
    scene_id: str,
    x_api_key: Optional[str] = Header(None),
) -> dict:
    """Force re-index all evidence for a scene into the vector store."""
    _check_auth(x_api_key)
    scene = db_get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    from app.rag import index_evidence, index_evidence_visuals

    evidence = db_list_evidence(scene_id)
    text_count = index_evidence(scene_id, evidence)
    visual_count = index_evidence_visuals(scene_id, evidence)
    return {
        "status": "reindexed",
        "scene_id": scene_id,
        "text_indexed": text_count,
        "visual_indexed": visual_count,
    }


# --- Static Media Serving ---

@api_router.get("/files/{file_path:path}", tags=["media"])
def serve_file(file_path: str):
    """Serve uploaded, cropped, or annotated image files securely."""
    # Resolve relative or absolute path within project directory
    target = Path(file_path)
    if not target.is_absolute():
        target = (ROOT_DIR / file_path).resolve()
    else:
        target = target.resolve()

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(str(target))
