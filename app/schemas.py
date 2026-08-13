"""
Shared data contracts for RAZIN.

Used by the API, the agent tools, the detector, and the DB layer so
every component speaks the same shape.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EvidenceClass(str, Enum):
    BLOODSTAIN = "bloodstain"
    FOOTPRINT = "footprint"
    DIGITAL_DEVICE = "digital_device"


class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class DetectionResult(BaseModel):
    """Raw output from the YOLO detector, before agent triage."""

    evidence_class: EvidenceClass
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox


class EvidenceItem(BaseModel):
    """A detection the agent has decided to log or flag as candidate evidence."""

    evidence_id: UUID = Field(default_factory=uuid4)
    scene_id: str
    evidence_class: EvidenceClass
    confidence: float
    bbox: BoundingBox
    source_image: str
    crop_image: str | None = None
    scene_area_label: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requires_review: bool = False
    reviewed: bool = False
    notes: str | None = None


class SceneUploadRequest(BaseModel):
    scene_id: str
    case_reference: str | None = None


class SceneResponse(BaseModel):
    scene_id: str
    case_reference: str | None = None
    created_at: str
    media_count: int = 0
    evidence_count: int = 0


class AnalysisResponse(BaseModel):
    scene_id: str
    images_analyzed: int
    evidence_found: int
    flagged_for_review: int
    summary: str | None = None
