"""
RAZIN configuration — loads all settings from .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project root
ROOT_DIR = Path(__file__).resolve().parent.parent

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" or "groq"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Detection
MODEL_PATH = os.getenv("MODEL_PATH", "models/yolo11n.pt")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))

# Database
DATABASE_PATH = ROOT_DIR / os.getenv("DATABASE_PATH", "data/razin.db")

# File storage
UPLOAD_DIR = ROOT_DIR / os.getenv("UPLOAD_DIR", "data/uploads")
FRAMES_DIR = ROOT_DIR / os.getenv("FRAMES_DIR", "data/frames")
CROPS_DIR = ROOT_DIR / os.getenv("CROPS_DIR", "data/crops")
ANNOTATED_DIR = ROOT_DIR / os.getenv("ANNOTATED_DIR", "data/annotated")

# Video
VIDEO_SAMPLE_FPS = float(os.getenv("VIDEO_SAMPLE_FPS", "2"))

# API auth
API_KEY = os.getenv("API_KEY", "")

# Ensure data directories exist
for d in [UPLOAD_DIR, FRAMES_DIR, CROPS_DIR, ANNOTATED_DIR]:
    d.mkdir(parents=True, exist_ok=True)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
