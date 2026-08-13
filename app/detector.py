"""
YOLO detection wrapper for RAZIN.

Performs object detection on images, crops candidate evidence regions,
and saves annotated images with bounding boxes.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

from app.config import ANNOTATED_DIR, CROPS_DIR, MODEL_PATH
from app.schemas import BoundingBox, DetectionResult, EvidenceClass

# Map model class names to standard EvidenceClass enum values
COCO_OR_CUSTOM_CLASS_MAP: dict[str, EvidenceClass] = {
    # Fine-tuned classes
    "bloodstain": EvidenceClass.BLOODSTAIN,
    "blood": EvidenceClass.BLOODSTAIN,
    "footprint": EvidenceClass.FOOTPRINT,
    "shoeprint": EvidenceClass.FOOTPRINT,
    "shoe": EvidenceClass.FOOTPRINT,
    "footwear": EvidenceClass.FOOTPRINT,
    "digital_device": EvidenceClass.DIGITAL_DEVICE,
    # COCO fallback classes for digital devices
    "cell phone": EvidenceClass.DIGITAL_DEVICE,
    "laptop": EvidenceClass.DIGITAL_DEVICE,
    "mouse": EvidenceClass.DIGITAL_DEVICE,
    "keyboard": EvidenceClass.DIGITAL_DEVICE,
    "tv": EvidenceClass.DIGITAL_DEVICE,
    "remote": EvidenceClass.DIGITAL_DEVICE,
}


class Detector:
    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = str(model_path or MODEL_PATH)
        # If specified model file doesn't exist locally, fallback to yolo11n.pt
        if not Path(self.model_path).exists() and not self.model_path.endswith(".pt"):
            self.model_path = "yolo11n.pt"
        try:
            self.model = YOLO(self.model_path)
        except Exception:
            # Fallback to base model if custom weights not found
            self.model = YOLO("yolo11n.pt")

    def _map_class_name(self, raw_name: str) -> EvidenceClass | None:
        """Map raw YOLO detection class name to EvidenceClass."""
        raw_lower = raw_name.lower().strip()
        if raw_lower in COCO_OR_CUSTOM_CLASS_MAP:
            return COCO_OR_CUSTOM_CLASS_MAP[raw_lower]

        # Substring heuristics
        if "blood" in raw_lower:
            return EvidenceClass.BLOODSTAIN
        if "foot" in raw_lower or "shoe" in raw_lower or "print" in raw_lower:
            return EvidenceClass.FOOTPRINT
        if any(w in raw_lower for w in ["phone", "laptop", "computer", "tablet", "device"]):
            return EvidenceClass.DIGITAL_DEVICE

        return None

    def detect(self, image_path: str | Path) -> list[DetectionResult]:
        """Run detection on a single image and return raw DetectionResult list."""
        image_path = str(image_path)
        results = self.model(image_path, verbose=False)
        detections: list[DetectionResult] = []

        if not results:
            return detections

        result = results[0]
        boxes = result.boxes
        if boxes is None:
            return detections

        for box in boxes:
            cls_id = int(box.cls[0])
            raw_name = result.names.get(cls_id, f"class_{cls_id}")
            evidence_class = self._map_class_name(raw_name)
            if evidence_class is None:
                continue

            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()  # [x_min, y_min, x_max, y_max]

            detections.append(
                DetectionResult(
                    evidence_class=evidence_class,
                    confidence=round(conf, 4),
                    bbox=BoundingBox(
                        x_min=round(xyxy[0], 2),
                        y_min=round(xyxy[1], 2),
                        x_max=round(xyxy[2], 2),
                        y_max=round(xyxy[3], 2),
                    ),
                )
            )

        return detections

    def process_and_annotate(
        self, image_path: str | Path, scene_id: str
    ) -> tuple[list[tuple[DetectionResult, str | None]], str | None]:
        """Run detection, crop each candidate item, and save an annotated image.

        Returns:
            Tuple of:
              - list of (DetectionResult, crop_image_path or None)
              - annotated_image_path or None
        """
        image_path = Path(image_path)
        detections = self.detect(image_path)

        if not image_path.exists():
            return ([(d, None) for d in detections], None)

        try:
            img = Image.open(image_path).convert("RGB")
        except Exception:
            return ([(d, None) for d in detections], None)

        draw = ImageDraw.Draw(img)
        img_w, img_h = img.size

        class_colors = {
            EvidenceClass.BLOODSTAIN: "#FF2A2A",      # Red
            EvidenceClass.FOOTPRINT: "#FFA500",       # Orange
            EvidenceClass.DIGITAL_DEVICE: "#00C0FF",  # Cyan
        }

        results_with_crops: list[tuple[DetectionResult, str | None]] = []

        for idx, det in enumerate(detections):
            b = det.bbox
            x1 = max(0, int(b.x_min))
            y1 = max(0, int(b.y_min))
            x2 = min(img_w, int(b.x_max))
            y2 = min(img_h, int(b.y_max))

            crop_path_str: str | None = None
            if x2 > x1 and y2 > y1:
                # Add small padding to crop for better forensic view
                pad_x = int((x2 - x1) * 0.1)
                pad_y = int((y2 - y1) * 0.1)
                crop_box = (
                    max(0, x1 - pad_x),
                    max(0, y1 - pad_y),
                    min(img_w, x2 + pad_x),
                    min(img_h, y2 + pad_y),
                )
                crop_img = img.crop(crop_box)
                crop_filename = f"crop_{scene_id}_{image_path.stem}_{idx}_{det.evidence_class.value}.jpg"
                crop_file_path = CROPS_DIR / crop_filename
                crop_img.save(crop_file_path, quality=95)
                crop_path_str = str(crop_file_path)

            results_with_crops.append((det, crop_path_str))

            # Draw bounding box and label on annotated image
            color = class_colors.get(det.evidence_class, "#00FF00")
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            label = f"{det.evidence_class.value} ({det.confidence:.2f})"
            # Draw label background
            text_bbox = draw.textbbox((x1, max(0, y1 - 20)), label)
            draw.rectangle(text_bbox, fill=color)
            draw.text((x1 + 2, max(0, y1 - 18)), label, fill="#FFFFFF")

        # Save annotated image
        annotated_filename = f"annotated_{scene_id}_{image_path.name}"
        annotated_path = ANNOTATED_DIR / annotated_filename
        img.save(annotated_path, quality=90)

        return results_with_crops, str(annotated_path)


# Singleton detector instance
_detector_instance: Detector | None = None


def get_detector() -> Detector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = Detector()
    return _detector_instance


def detect(image_path: str | Path) -> list[DetectionResult]:
    return get_detector().detect(image_path)
