"""
RAZIN — Main Command Line Entrypoint.

Usage:
  uv run main.py api        -> Run FastAPI backend on port 8000
  uv run main.py web        -> Run React + Vite web dashboard on port 5173
  uv run main.py dashboard  -> Run Streamlit dashboard on port 8501 (legacy fallback)
"""

import os
import sys
import subprocess


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "help"

    if action in ["web", "ui", "frontend"]:
        print("Starting RAZIN React + Vite Web Dashboard (http://localhost:5173)...")
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
        subprocess.run(["npm", "run", "dev"], cwd=frontend_dir, shell=True)
    elif action == "api":
        print("Starting RAZIN FastAPI Backend (http://localhost:8000)...")
        subprocess.run(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    elif action == "dashboard":
        print("Starting RAZIN Streamlit Dashboard (http://localhost:8501)...")
        subprocess.run(["streamlit", "run", "app/dashboard.py"])
    else:
        print("=" * 65)
        print("RAZIN v0.1 — Autonomous Forensic Evidence Surveying Platform")
        print("=" * 65)
        print("Run commands:")
        print("  uv run main.py api        -> Launch FastAPI backend (port 8000)")
        print("  uv run main.py web        -> Launch React + Vite Web App (port 5173)")
        print("  uv run main.py dashboard  -> Launch Streamlit fallback (port 8501)")
        print("=" * 65)
        print("Defaulting to starting the FastAPI backend...")
        subprocess.run(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])


if __name__ == "__main__":
    main()
