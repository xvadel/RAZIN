"""
Shared data contract for RAZIN.

These models are used by the API layer, the agent's tools, and the DB
layer, so a detection produced by app/cv/detector.py, a decision made
by app/agents/react_agent.py, and a row read from app/db/crud.py all
speak the same shape. See RAZIN_Preliminary_Plan.md, Section 4.2.
"""

from __future__ import annotations

from datetime import datetime
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
    """Raw output from the detector (app/cv/detector.py), before agent triage."""

    evidence_class: EvidenceClass
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox


class EvidenceItem(BaseModel):
    """A detection the agent has decided to log (or flag) as candidate evidence."""

    evidence_id: UUID = Field(default_factory=uuid4)
    scene_id: str
    evidence_class: EvidenceClass
    confidence: float
    bbox: BoundingBox
    source_image: str
    scene_area_label: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    requires_review: bool = False
    reviewed: bool = False
    notes: str | None = None


class SceneUploadRequest(BaseModel):
    scene_id: str
    case_reference: str | None = None
