"""
SQLite database — plain sqlite3, no ORM.

Tables: scenes, evidence, media.
"""

import json
import sqlite3
from pathlib import Path

from app.config import DATABASE_PATH
from app.schemas import BoundingBox, EvidenceItem, SceneResponse, SceneUploadRequest


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scenes (
            scene_id TEXT PRIMARY KEY,
            case_reference TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS media (
            media_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scene_id TEXT NOT NULL REFERENCES scenes(scene_id),
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            analyzed INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id TEXT PRIMARY KEY,
            scene_id TEXT NOT NULL REFERENCES scenes(scene_id),
            evidence_class TEXT NOT NULL,
            confidence REAL NOT NULL,
            bbox TEXT NOT NULL,
            source_image TEXT NOT NULL,
            crop_image TEXT,
            scene_area_label TEXT,
            timestamp TEXT NOT NULL,
            requires_review INTEGER NOT NULL DEFAULT 0,
            reviewed INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        );
    """)
    conn.commit()
    conn.close()


# --- Scenes ---

def create_scene(req: SceneUploadRequest) -> SceneResponse:
    from datetime import datetime, timezone
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO scenes (scene_id, case_reference, created_at) VALUES (?, ?, ?)",
        (req.scene_id, req.case_reference, now),
    )
    conn.commit()
    conn.close()
    return SceneResponse(scene_id=req.scene_id, case_reference=req.case_reference, created_at=now)


def get_scene(scene_id: str) -> SceneResponse | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM scenes WHERE scene_id = ?", (scene_id,)).fetchone()
    if not row:
        conn.close()
        return None
    media_count = conn.execute(
        "SELECT COUNT(*) FROM media WHERE scene_id = ?", (scene_id,)
    ).fetchone()[0]
    evidence_count = conn.execute(
        "SELECT COUNT(*) FROM evidence WHERE scene_id = ?", (scene_id,)
    ).fetchone()[0]
    conn.close()
    return SceneResponse(
        scene_id=row["scene_id"],
        case_reference=row["case_reference"],
        created_at=row["created_at"],
        media_count=media_count,
        evidence_count=evidence_count,
    )


def list_scenes() -> list[SceneResponse]:
    conn = _connect()
    rows = conn.execute("SELECT * FROM scenes ORDER BY created_at DESC").fetchall()
    results = []
    for row in rows:
        media_count = conn.execute(
            "SELECT COUNT(*) FROM media WHERE scene_id = ?", (row["scene_id"],)
        ).fetchone()[0]
        evidence_count = conn.execute(
            "SELECT COUNT(*) FROM evidence WHERE scene_id = ?", (row["scene_id"],)
        ).fetchone()[0]
        results.append(SceneResponse(
            scene_id=row["scene_id"],
            case_reference=row["case_reference"],
            created_at=row["created_at"],
            media_count=media_count,
            evidence_count=evidence_count,
        ))
    conn.close()
    return results


# --- Media ---

def add_media(scene_id: str, file_path: str, file_type: str) -> int:
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO media (scene_id, file_path, file_type) VALUES (?, ?, ?)",
        (scene_id, file_path, file_type),
    )
    conn.commit()
    media_id = cur.lastrowid
    conn.close()
    return media_id


def list_media(scene_id: str, only_unanalyzed: bool = False) -> list[dict]:
    conn = _connect()
    if only_unanalyzed:
        rows = conn.execute(
            "SELECT * FROM media WHERE scene_id = ? AND analyzed = 0", (scene_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM media WHERE scene_id = ?", (scene_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_media_analyzed(media_id: int) -> None:
    conn = _connect()
    conn.execute("UPDATE media SET analyzed = 1 WHERE media_id = ?", (media_id,))
    conn.commit()
    conn.close()


# --- Evidence ---

def create_evidence(item: EvidenceItem) -> str:
    conn = _connect()
    bbox_json = item.bbox.model_dump_json()
    conn.execute(
        """INSERT INTO evidence
           (evidence_id, scene_id, evidence_class, confidence, bbox, source_image,
            crop_image, scene_area_label, timestamp, requires_review, reviewed, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(item.evidence_id),
            item.scene_id,
            item.evidence_class.value,
            item.confidence,
            bbox_json,
            item.source_image,
            item.crop_image,
            item.scene_area_label,
            item.timestamp.isoformat(),
            int(item.requires_review),
            int(item.reviewed),
            item.notes,
        ),
    )
    conn.commit()
    conn.close()
    return str(item.evidence_id)


def _row_to_evidence(row: sqlite3.Row) -> EvidenceItem:
    bbox_data = json.loads(row["bbox"])
    return EvidenceItem(
        evidence_id=row["evidence_id"],
        scene_id=row["scene_id"],
        evidence_class=row["evidence_class"],
        confidence=row["confidence"],
        bbox=BoundingBox(**bbox_data),
        source_image=row["source_image"],
        crop_image=row["crop_image"],
        scene_area_label=row["scene_area_label"],
        timestamp=row["timestamp"],
        requires_review=bool(row["requires_review"]),
        reviewed=bool(row["reviewed"]),
        notes=row["notes"],
    )


def list_evidence(scene_id: str, requires_review: bool | None = None) -> list[EvidenceItem]:
    conn = _connect()
    if requires_review is not None:
        rows = conn.execute(
            "SELECT * FROM evidence WHERE scene_id = ? AND requires_review = ? ORDER BY timestamp DESC",
            (scene_id, int(requires_review)),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM evidence WHERE scene_id = ? ORDER BY timestamp DESC",
            (scene_id,),
        ).fetchall()
    conn.close()
    return [_row_to_evidence(r) for r in rows]


def get_evidence(evidence_id: str) -> EvidenceItem | None:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM evidence WHERE evidence_id = ?", (evidence_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_evidence(row)


def flag_for_review(evidence_id: str, reason: str) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE evidence SET requires_review = 1, notes = ? WHERE evidence_id = ?",
        (reason, evidence_id),
    )
    conn.commit()
    conn.close()


def mark_reviewed(evidence_id: str, notes: str | None = None) -> None:
    conn = _connect()
    if notes:
        conn.execute(
            "UPDATE evidence SET reviewed = 1, requires_review = 0, notes = ? WHERE evidence_id = ?",
            (notes, evidence_id),
        )
    else:
        conn.execute(
            "UPDATE evidence SET reviewed = 1, requires_review = 0 WHERE evidence_id = ?",
            (evidence_id,),
        )
    conn.commit()
    conn.close()
