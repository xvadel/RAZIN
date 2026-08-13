"""
Video processing module for RAZIN.

Extracts frames from uploaded video clips at a configurable sampling rate
and filters out near-duplicate consecutive frames.
"""

from pathlib import Path
import cv2
import numpy as np


def extract_frames(
    video_path: str | Path,
    output_dir: str | Path,
    scene_id: str,
    fps: float = 2.0,
    min_diff_threshold: float = 0.05,
) -> list[str]:
    """Extract frames from a video file, skipping near-duplicate consecutive frames.

    Args:
        video_path: Path to the video file.
        output_dir: Directory where extracted frame images will be stored.
        scene_id: Identifier of the scene (used for naming frame files).
        fps: Target frames per second to extract.
        min_diff_threshold: Minimum normalized pixel difference to accept a frame.

    Returns:
        List of paths to saved frame image files.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return []

    native_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_interval = max(1, int(native_fps / fps))

    saved_frame_paths: list[str] = []
    prev_gray: np.ndarray | None = None
    frame_idx = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_small = cv2.resize(gray, (160, 120))

            is_duplicate = False
            if prev_gray is not None:
                diff = np.mean(np.abs(gray_small.astype(float) - prev_gray.astype(float))) / 255.0
                if diff < min_diff_threshold:
                    is_duplicate = True

            if not is_duplicate:
                prev_gray = gray_small
                saved_count += 1
                frame_filename = f"{scene_id}_frame_{saved_count:04d}.jpg"
                frame_path = output_dir / frame_filename
                cv2.imwrite(str(frame_path), frame)
                saved_frame_paths.append(str(frame_path))

        frame_idx += 1

    cap.release()
    return saved_frame_paths
