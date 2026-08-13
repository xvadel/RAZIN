"""
End-to-end automated verification script for RAZIN Phase 1 MVP.
"""

from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

from app.config import UPLOAD_DIR
from app.db import (
    create_scene,
    get_scene,
    init_db,
    list_evidence,
    list_scenes,
)
from app.detector import get_detector
from app.agent import analyze_scene, triage_detection
from app.schemas import DetectionResult, EvidenceClass, BoundingBox, SceneUploadRequest


def create_mock_scene_image(filepath: Path):
    """Generate a test crime scene image with distinct colored objects."""
    img = Image.new("RGB", (640, 480), color=(70, 70, 75))
    draw = ImageDraw.Draw(img)

    # Simulated phone / laptop (rectangle)
    draw.rectangle([100, 150, 250, 300], fill=(20, 20, 20), outline=(200, 200, 200), width=2)
    draw.text((120, 170), "DIGITAL DEVICE", fill=(255, 255, 255))

    # Simulated bloodstain (red blob)
    draw.ellipse([350, 200, 480, 320], fill=(160, 10, 10), outline=(200, 0, 0), width=2)
    draw.text((370, 250), "BLOODSTAIN", fill=(255, 255, 255))

    filepath.parent.mkdir(parents=True, exist_ok=True)
    img.save(filepath, quality=95)
    print(f"Created mock scene image at {filepath}")


def run_tests():
    print("=" * 60)
    print("STEP 1: Testing DB Initialization & CRUD...")
    init_db()
    test_scene_id = "SCENE-TEST-001"
    req = SceneUploadRequest(scene_id=test_scene_id, case_reference="CASE-REF-999")
    sc = create_scene(req)
    assert sc.scene_id == test_scene_id
    scenes = list_scenes()
    assert any(s.scene_id == test_scene_id for s in scenes)
    print(f"✓ DB test passed: Scene {test_scene_id} created.")

    print("\n" + "=" * 60)
    print("STEP 2: Testing YOLO Detector initialization...")
    detector = get_detector()
    assert detector.model is not None
    print("✓ YOLO detector successfully loaded.")

    print("\n" + "=" * 60)
    print("STEP 3: Testing Media & Detection pipeline...")
    test_img_path = UPLOAD_DIR / test_scene_id / "test_scene_frame.jpg"
    create_mock_scene_image(test_img_path)

    # Test processing & annotation
    results, annotated_path = detector.process_and_annotate(test_img_path, test_scene_id)
    print(f"✓ Processed image. Annotated output: {annotated_path}")

    print("\n" + "=" * 60)
    print("STEP 4: Testing Agent Triage Logic (ReAct / Rules)...")
    # Simulate a high-confidence and a low-confidence detection
    det_high = DetectionResult(
        evidence_class=EvidenceClass.DIGITAL_DEVICE,
        confidence=0.88,
        bbox=BoundingBox(x_min=100, y_min=150, x_max=250, y_max=300),
    )
    item_high = triage_detection(
        scene_id=test_scene_id,
        detection=det_high,
        source_image=str(test_img_path),
    )
    assert item_high.requires_review is False, "High confidence should be auto-approved"
    print("✓ High-confidence detection correctly auto-approved.")

    det_low = DetectionResult(
        evidence_class=EvidenceClass.BLOODSTAIN,
        confidence=0.35,
        bbox=BoundingBox(x_min=350, y_min=200, x_max=480, y_max=320),
    )
    item_low = triage_detection(
        scene_id=test_scene_id,
        detection=det_low,
        source_image=str(test_img_path),
    )
    assert item_low.requires_review is True, "Low confidence (<0.5) must require human review"
    print("✓ Low-confidence detection correctly flagged for human review.")

    print("\n" + "=" * 60)
    print("STEP 5: Testing Evidence Retrieval...")
    evidence_list = list_evidence(test_scene_id)
    assert len(evidence_list) >= 2
    print(f"✓ Retrieved {len(evidence_list)} logged evidence items for scene.")

    print("\n" + "=" * 60)
    print("ALL CORE UNIT TESTS PASSED SUCCESSFULLY! 🚀")


if __name__ == "__main__":
    run_tests()
