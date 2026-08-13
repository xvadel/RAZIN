"""
YOLO detection wrapper — RAZIN_Preliminary_Plan.md, Section 4.2 (Transfer Learning).

Build-sequence steps 5-7:
  5. Load an off-the-shelf pretrained checkpoint just to prove the
     pipeline works end to end, before spending time on the dataset.
  6. Fine-tune on a labeled forensic dataset (bloodstain / footprint /
     digital_device).
  7. Point `MODEL_PATH` below at the fine-tuned weights.

Example (see the plan for the training call):

    from ultralytics import YOLO

    class Detector:
        def __init__(self, model_path: str = "models/yolo_finetuned.pt"):
            self.model = YOLO(model_path)

        def detect(self, image_path: str) -> list[DetectionResult]:
            results = self.model(image_path)
            # map results -> app.models.schemas.DetectionResult objects
            ...
"""

from app.models.schemas import DetectionResult

MODEL_PATH = "models/yolo_finetuned.pt"


def detect(image_path: str) -> list[DetectionResult]:
    """Run the detector on a single image and return raw detections.

    Not implemented yet — see build-sequence steps 5-7 above.
    """
    raise NotImplementedError
