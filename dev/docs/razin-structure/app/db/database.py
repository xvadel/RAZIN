"""
Database engine/session setup — RAZIN_Preliminary_Plan.md, Section 4.2
(Supporting Infrastructure -> Persistence).

Build-sequence step 3. Route access through SQLAlchemy (rather than raw
sqlite3 calls) so this can swap to Postgres later without touching the
rest of the app. Table shape (mirrors app/models/schemas.py):

    CREATE TABLE scenes (
        scene_id TEXT PRIMARY KEY,
        case_reference TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE evidence (
        evidence_id TEXT PRIMARY KEY,
        scene_id TEXT NOT NULL REFERENCES scenes(scene_id),
        evidence_class TEXT NOT NULL,
        confidence REAL NOT NULL,
        bbox_x_min REAL, bbox_y_min REAL, bbox_x_max REAL, bbox_y_max REAL,
        source_image TEXT NOT NULL,
        scene_area_label TEXT,
        timestamp TEXT NOT NULL,
        requires_review INTEGER NOT NULL DEFAULT 0,
        reviewed INTEGER NOT NULL DEFAULT 0,
        notes TEXT
    );

Wire these up as SQLAlchemy declarative models here, backed by
DATABASE_URL from the environment (see .env.example).
"""

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/razin.db")

# TODO(build step 3): create the SQLAlchemy engine, session factory, and
# declarative models for `scenes` and `evidence` per the schema above.
