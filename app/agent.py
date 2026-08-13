"""
ReAct Agent and analysis pipeline for RAZIN.

Reviews AI detections from crime-scene imagery, applies forensic triage logic
(auto-log vs. flag for human review), and generates scene summaries.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import (
    CONFIDENCE_THRESHOLD,
    FRAMES_DIR,
    GOOGLE_API_KEY,
    GROQ_API_KEY,
    LLM_PROVIDER,
    VIDEO_SAMPLE_FPS,
)
from app.db import (
    add_media,
    create_evidence,
    flag_for_review,
    list_evidence,
    list_media,
    mark_media_analyzed,
)
from app.detector import get_detector
from app.schemas import (
    AnalysisResponse,
    BoundingBox,
    DetectionResult,
    EvidenceClass,
    EvidenceItem,
)
from app.video import extract_frames

RAZIN_SYSTEM_PROMPT = f"""You are RAZIN's forensic evidence triage assistant.
You review AI-generated object detections from crime-scene imagery and decide whether to log them as candidate evidence or flag them for human review.

System Rules:
1. Never assert a detection is confirmed evidence — all AI output is unverified pending human confirmation.
2. If confidence is below {CONFIDENCE_THRESHOLD}, ALWAYS flag for human review with a clear reason.
3. If multiple detections of different classes significantly overlap, flag both for human review.
4. When uncertain or in doubt, prefer flagging for review over discarding.
5. Provide concise forensic reasoning for every decision.
"""


def _get_llm():
    """Instantiate the configured LLM client (Gemini or Groq) with fallback."""
    provider = LLM_PROVIDER.lower().strip()

    if provider == "gemini" and GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=GOOGLE_API_KEY,
                temperature=0.1,
            )
        except Exception:
            pass

    if (provider == "groq" or not GOOGLE_API_KEY) and GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model_name="llama-3.3-70b-versatile",
                groq_api_key=GROQ_API_KEY,
                temperature=0.1,
            )
        except Exception:
            pass

    # Fallback to Gemini if key exists
    if GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=GOOGLE_API_KEY,
                temperature=0.1,
            )
        except Exception:
            pass

    return None


def _calculate_iou(b1: BoundingBox, b2: BoundingBox) -> float:
    """Calculate Intersection over Union between two bounding boxes."""
    x_left = max(b1.x_min, b2.x_min)
    y_top = max(b1.y_min, b2.y_min)
    x_right = min(b1.x_max, b2.x_max)
    y_bottom = min(b1.y_max, b2.y_max)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection = (x_right - x_left) * (y_bottom - y_top)
    area1 = (b1.x_max - b1.x_min) * (b1.y_max - b1.y_min)
    area2 = (b2.x_max - b2.x_min) * (b2.y_max - b2.y_min)
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def triage_detection(
    scene_id: str,
    detection: DetectionResult,
    source_image: str,
    crop_image: str | None = None,
    sibling_detections: list[DetectionResult] | None = None,
    llm: Any = None,
) -> EvidenceItem:
    """Triage a single detection into an EvidenceItem (deciding requires_review)."""
    sibling_detections = sibling_detections or []
    requires_review = False
    notes_list: list[str] = []

    # Rule 1: Confidence threshold
    if detection.confidence < CONFIDENCE_THRESHOLD:
        requires_review = True
        notes_list.append(
            f"Confidence ({detection.confidence:.2f}) below threshold ({CONFIDENCE_THRESHOLD})"
        )

    # Rule 2: Overlapping bounding boxes with different classes
    for sib in sibling_detections:
        if sib != detection and sib.evidence_class != detection.evidence_class:
            iou = _calculate_iou(detection.bbox, sib.bbox)
            if iou > 0.3:
                requires_review = True
                notes_list.append(
                    f"Overlaps with {sib.evidence_class.value} (IoU {iou:.2f})"
                )

    notes = "; ".join(notes_list) if notes_list else "Auto-triaged by AI detector"

    # If LLM is available, enrich reasoning with LLM agent insight
    if llm is not None and requires_review:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            prompt = (
                f"Candidate detection: {detection.evidence_class.value} (confidence: {detection.confidence:.2f}). "
                f"Flag reasons: {notes}. "
                f"Provide a 1-sentence forensic triage recommendation for the investigator."
            )
            resp = llm.invoke([SystemMessage(content=RAZIN_SYSTEM_PROMPT), HumanMessage(content=prompt)])
            if resp and resp.content:
                notes = f"{notes} | LLM Note: {resp.content.strip()}"
        except Exception:
            pass

    evidence_item = EvidenceItem(
        evidence_id=uuid4(),
        scene_id=scene_id,
        evidence_class=detection.evidence_class,
        confidence=detection.confidence,
        bbox=detection.bbox,
        source_image=str(source_image),
        crop_image=str(crop_image) if crop_image else None,
        scene_area_label=None,
        timestamp=datetime.now(timezone.utc),
        requires_review=requires_review,
        reviewed=False,
        notes=notes,
    )

    create_evidence(evidence_item)
    return evidence_item


def generate_scene_summary(scene_id: str, evidence_list: list[EvidenceItem], llm: Any = None) -> str:
    """Generate natural language forensic summary of all evidence in the scene."""
    if not evidence_list:
        return "No candidate evidence was detected in the uploaded scene imagery."

    counts: dict[str, int] = {}
    flagged_count = 0
    for item in evidence_list:
        cls_val = item.evidence_class.value
        counts[cls_val] = counts.get(cls_val, 0) + 1
        if item.requires_review:
            flagged_count += 1

    summary_bullets = [f"- {cls_name}: {count}" for cls_name, count in counts.items()]
    basic_summary = (
        f"Scene {scene_id} Evidence Summary:\n"
        f"Total items logged: {len(evidence_list)} ({flagged_count} flagged for human review).\n"
        + "\n".join(summary_bullets)
    )

    if llm is not None:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            evidence_digest = [
                f"- Class: {e.evidence_class.value}, Conf: {e.confidence:.2f}, Needs Review: {e.requires_review}, Notes: {e.notes}"
                for e in evidence_list[:25]
            ]
            prompt = (
                f"Scene ID: {scene_id}\n"
                f"Logged Evidence Items:\n" + "\n".join(evidence_digest) + "\n\n"
                "Write a professional, concise preliminary forensic survey report (3-4 paragraphs) summarizing findings, "
                "critical evidence requiring immediate human verification, and recommended next steps for investigators."
            )
            resp = llm.invoke([SystemMessage(content=RAZIN_SYSTEM_PROMPT), HumanMessage(content=prompt)])
            if resp and resp.content:
                return resp.content.strip()
        except Exception:
            pass

    return basic_summary


def analyze_scene(scene_id: str) -> AnalysisResponse:
    """Orchestrate end-to-end scene analysis for all unanalyzed media."""
    detector = get_detector()
    llm = _get_llm()

    media_records = list_media(scene_id, only_unanalyzed=True)
    images_to_process: list[tuple[int | None, str]] = []

    # Expand video files into frames
    for media in media_records:
        file_path = Path(media["file_path"])
        file_type = media["file_type"]

        if file_type == "video":
            frame_paths = extract_frames(
                video_path=file_path,
                output_dir=FRAMES_DIR / scene_id,
                scene_id=scene_id,
                fps=VIDEO_SAMPLE_FPS,
            )
            for fp in frame_paths:
                frame_media_id = add_media(scene_id, fp, "image")
                images_to_process.append((frame_media_id, fp))
            mark_media_analyzed(media["media_id"])
        else:
            images_to_process.append((media["media_id"], str(file_path)))

    logged_items: list[EvidenceItem] = []

    # Process each image
    for media_id, image_path in images_to_process:
        results_with_crops, annotated_path = detector.process_and_annotate(
            image_path, scene_id
        )
        raw_detections = [det for det, _ in results_with_crops]

        for det, crop_path in results_with_crops:
            item = triage_detection(
                scene_id=scene_id,
                detection=det,
                source_image=image_path,
                crop_image=crop_path,
                sibling_detections=raw_detections,
                llm=llm,
            )
            logged_items.append(item)

        if media_id is not None:
            mark_media_analyzed(media_id)

    # Fetch all evidence for scene
    all_evidence = list_evidence(scene_id)
    flagged_count = sum(1 for e in all_evidence if e.requires_review)
    summary = generate_scene_summary(scene_id, all_evidence, llm=llm)

    # Index evidence into vector store for RAG chatbot
    try:
        from app.rag import index_evidence, index_evidence_visuals
        index_evidence(scene_id, all_evidence)
        index_evidence_visuals(scene_id, all_evidence)
    except Exception as e:
        print(f"[RAZIN] RAG indexing warning: {e}")

    return AnalysisResponse(
        scene_id=scene_id,
        images_analyzed=len(images_to_process),
        evidence_found=len(all_evidence),
        flagged_for_review=flagged_count,
        summary=summary,
    )
