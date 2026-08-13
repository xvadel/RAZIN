"""
RAZIN dashboard — RAZIN_Preliminary_Plan.md, Section 4.2 (Dashboard).

Build-sequence step 10 — this is a placeholder until the API has real
data to show. Run with: streamlit run app/dashboard/streamlit_app.py

Talks to the FastAPI layer over HTTP (httpx) rather than the database
directly, per the plan. Minimum views for Phase 1:
  - scene upload form
  - evidence list with thumbnails, per scene
  - a "needs review" view, filtered on requires_review
"""

import streamlit as st

API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="RAZIN", layout="wide")
st.title("RAZIN — Evidence Dashboard")
st.info(
    "Dashboard not wired up yet — this is a Phase 1 placeholder. "
    "See build-sequence step 10 in RAZIN_Preliminary_Plan.md."
)
