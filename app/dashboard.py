"""
Streamlit Dashboard for RAZIN.

Acts purely as an API client over HTTP (httpx), providing investigators
with scene ingestion, AI analysis triggers, forensic evidence browsing,
review queue triage, and preliminary reporting.
"""

import os
from pathlib import Path
import httpx
from PIL import Image
import streamlit as st

# Configure page layout and forensic dark theme
st.set_page_config(
    page_title="RAZIN — Forensic Evidence Survey",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for forensic aesthetic
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        padding: 12px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .evidence-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge-blood {
        background-color: #781010;
        color: #ffb4b4;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .badge-footprint {
        background-color: #8c5200;
        color: #ffd699;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .badge-device {
        background-color: #005682;
        color: #a3e5ff;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .badge-review {
        background-color: #8f6b00;
        color: #fff0a6;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .badge-confirmed {
        background-color: #1b6329;
        color: #a3f7b5;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def get_headers(api_key: str = "") -> dict[str, str]:
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key
    return headers


# --- Sidebar ---
st.sidebar.title("🔍 RAZIN Forensics")
st.sidebar.caption("AI-Assisted Preliminary Crime-Scene Evidence Survey")

api_key_input = st.sidebar.text_input("API Key (if enabled)", type="password", value="")

# Health check
api_online = False
try:
    res = httpx.get(f"{API_BASE}/health", timeout=3.0)
    if res.status_code == 200:
        api_online = True
        st.sidebar.success("● API Connected (v0.1.0)")
    else:
        st.sidebar.warning(f"API returned status {res.status_code}")
except Exception:
    st.sidebar.error("● API Disconnected (Check uvicorn)")

st.sidebar.markdown("---")

# Scene Selector
scenes_list = []
if api_online:
    try:
        r = httpx.get(f"{API_BASE}/scenes", headers=get_headers(api_key_input), timeout=5.0)
        if r.status_code == 200:
            scenes_list = r.json()
    except Exception:
        scenes_list = []

scene_ids = [s["scene_id"] for s in scenes_list]
selected_scene_id = None

if scene_ids:
    selected_scene_id = st.sidebar.selectbox("Active Crime Scene", scene_ids, index=0)
else:
    st.sidebar.info("No scenes registered yet. Create one below.")

st.sidebar.markdown("---")
st.sidebar.subheader("New Crime Scene")
with st.sidebar.form("create_scene_form", clear_on_submit=True):
    new_scene_id = st.text_input("Scene ID", placeholder="e.g. SCENE-2026-08A")
    new_case_ref = st.text_input("Case Reference", placeholder="e.g. CASE-CR-8891")
    submit_create = st.form_submit_button("Register Scene", use_container_width=True)

    if submit_create and new_scene_id:
        try:
            payload = {"scene_id": new_scene_id, "case_reference": new_case_ref or None}
            res = httpx.post(
                f"{API_BASE}/scenes",
                json=payload,
                headers=get_headers(api_key_input),
                timeout=5.0,
            )
            if res.status_code in [200, 201]:
                st.sidebar.success(f"Scene {new_scene_id} registered!")
                st.rerun()
            else:
                st.sidebar.error(f"Error: {res.text}")
        except Exception as ex:
            st.sidebar.error(f"Failed to create scene: {ex}")


# --- Main Application Header ---
st.title("RAZIN — Evidence Surveying System")

if not selected_scene_id:
    st.info("👈 Register or select a Crime Scene in the sidebar to begin.")
    st.stop()

# Fetch active scene metadata
active_scene = next((s for s in scenes_list if s["scene_id"] == selected_scene_id), None)
if active_scene:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Active Scene", active_scene["scene_id"])
    col_m2.metric("Case Ref", active_scene.get("case_reference") or "N/A")
    col_m3.metric("Uploaded Media", active_scene.get("media_count", 0))
    col_m4.metric("Logged Evidence", active_scene.get("evidence_count", 0))

# Tabs
tab_upload, tab_evidence, tab_review, tab_report = st.tabs([
    "📤 Ingestion & Analysis",
    "🔍 Evidence Catalog",
    "⚠️ Review Queue",
    "📋 Forensic Report & Visuals",
])


# ==========================================
# TAB 1: Ingestion & Analysis
# ==========================================
with tab_upload:
    st.subheader(f"Media Ingestion for Scene: `{selected_scene_id}`")
    st.markdown("Upload crime-scene imagery (JPEG/PNG) or short scene-survey videos (MP4/MOV).")

    uploaded_files = st.file_uploader(
        "Upload Scene Photos or Video",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png", "mp4", "mov", "avi"],
    )

    if uploaded_files:
        if st.button(f"Save {len(uploaded_files)} Uploaded Files to Server", type="primary"):
            with st.spinner("Uploading files to backend..."):
                files_payload = [
                    ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
                    for f in uploaded_files
                ]
                try:
                    resp = httpx.post(
                        f"{API_BASE}/scenes/{selected_scene_id}/upload-batch",
                        files=files_payload,
                        headers=get_headers(api_key_input),
                        timeout=60.0,
                    )
                    if resp.status_code == 200:
                        st.success(f"Successfully uploaded {len(uploaded_files)} files.")
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {resp.text}")
                except Exception as e:
                    st.error(f"Upload error: {e}")

    st.markdown("---")
    st.subheader("⚡ Run AI Detection & ReAct Agent Triage")
    st.write(
        "Runs the YOLO object detector across all unanalyzed scene media, extracts video frames, "
        "and triggers the ReAct Agent to apply forensic triage rules."
    )

    if st.button("🚀 Analyze All Unprocessed Media", type="primary", use_container_width=True):
        with st.spinner("Analyzing scene with YOLO + ReAct agent..."):
            try:
                resp = httpx.post(
                    f"{API_BASE}/scenes/{selected_scene_id}/analyze",
                    headers=get_headers(api_key_input),
                    timeout=180.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(
                        f"Analysis Complete! Processed {data.get('images_analyzed', 0)} images. "
                        f"Found {data.get('evidence_found', 0)} evidence items "
                        f"({data.get('flagged_for_review', 0)} flagged for review)."
                    )
                    if data.get("summary"):
                        st.info(data["summary"])
                    st.rerun()
                else:
                    st.error(f"Analysis failed: {resp.text}")
            except Exception as e:
                st.error(f"Analysis request error: {e}")


# ==========================================
# TAB 2: Evidence Catalog
# ==========================================
with tab_evidence:
    st.subheader(f"Cataloged Evidence — Scene `{selected_scene_id}`")

    try:
        ev_resp = httpx.get(
            f"{API_BASE}/scenes/{selected_scene_id}/evidence",
            headers=get_headers(api_key_input),
            timeout=10.0,
        )
        evidence_items = ev_resp.json() if ev_resp.status_code == 200 else []
    except Exception:
        evidence_items = []

    if not evidence_items:
        st.info("No evidence records found for this scene yet. Upload media and run analysis in the Ingestion tab.")
    else:
        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            class_filter = st.multiselect(
                "Filter by Class",
                options=["bloodstain", "footprint", "digital_device"],
                default=["bloodstain", "footprint", "digital_device"],
            )
        with col_f2:
            status_filter = st.selectbox(
                "Filter by Verification Status",
                options=["All", "Confirmed Reviewed", "Requires Human Review"],
            )

        filtered_items = [e for e in evidence_items if e["evidence_class"] in class_filter]
        if status_filter == "Confirmed Reviewed":
            filtered_items = [e for e in filtered_items if e.get("reviewed")]
        elif status_filter == "Requires Human Review":
            filtered_items = [e for e in filtered_items if e.get("requires_review")]

        st.caption(f"Showing {len(filtered_items)} of {len(evidence_items)} total evidence items")

        # Grid view for evidence items
        for item in filtered_items:
            ev_class = item["evidence_class"]
            badge_class = {
                "bloodstain": "badge-blood",
                "footprint": "badge-footprint",
                "digital_device": "badge-device",
            }.get(ev_class, "badge-device")

            with st.container():
                col_img, col_info = st.columns([1, 3])

                with col_img:
                    crop_url = item.get("crop_image")
                    if crop_url and Path(crop_url).exists():
                        try:
                            st.image(Image.open(crop_url), use_container_width=True, caption="Forensic Crop")
                        except Exception:
                            st.caption("No Crop Image")
                    else:
                        st.caption("No Crop Image")

                with col_info:
                    st.markdown(
                        f"<span class='{badge_class}'>{ev_class.upper()}</span> "
                        f"{'<span class=\"badge-review\">NEEDS REVIEW</span>' if item.get('requires_review') else ''} "
                        f"{'<span class=\"badge-confirmed\">CONFIRMED</span>' if item.get('reviewed') else ''}",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Evidence ID:** `{item['evidence_id']}`")
                    st.progress(item["confidence"], text=f"AI Confidence: {item['confidence']*100:.1f}%")
                    st.caption(f"Source: {Path(item['source_image']).name} | Logged: {item['timestamp']}")
                    if item.get("notes"):
                        st.write(f"📝 **Notes / Reason:** {item['notes']}")

                st.markdown("---")


# ==========================================
# TAB 3: Review Queue
# ==========================================
with tab_review:
    st.subheader("⚠️ Human-in-the-Loop Review Queue")
    st.caption("Items flagged by the ReAct Agent due to low confidence (<0.5), overlapping detections, or anomaly detection.")

    review_items = [e for e in evidence_items if e.get("requires_review")]

    if not review_items:
        st.success("🎉 All candidate evidence items for this scene have been verified or auto-approved!")
    else:
        st.warning(f"There are **{len(review_items)}** items awaiting investigator confirmation.")

        for item in review_items:
            with st.container():
                col_c1, col_c2, col_c3 = st.columns([1, 2, 1])

                with col_c1:
                    crop_url = item.get("crop_image")
                    if crop_url and Path(crop_url).exists():
                        st.image(Image.open(crop_url), use_container_width=True)
                    else:
                        st.write("*(No preview)*")

                with col_c2:
                    st.markdown(f"### {item['evidence_class'].upper()}")
                    st.write(f"**Confidence:** `{item['confidence']*100:.1f}%`")
                    st.write(f"**Flag Reason:** {item.get('notes', 'Flagged by Agent')}")
                    st.caption(f"Evidence ID: `{item['evidence_id']}`")

                with col_c3:
                    st.write("**Investigator Action**")
                    investigator_note = st.text_input("Review Note", key=f"note_{item['evidence_id']}")
                    if st.button("✅ Confirm Evidence", key=f"btn_{item['evidence_id']}", type="primary"):
                        try:
                            rev_res = httpx.patch(
                                f"{API_BASE}/evidence/{item['evidence_id']}/review",
                                json={"notes": investigator_note or "Confirmed by investigator"},
                                headers=get_headers(api_key_input),
                                timeout=5.0,
                            )
                            if rev_res.status_code == 200:
                                st.success("Verified!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                st.markdown("---")


# ==========================================
# TAB 4: Forensic Report & Visuals
# ==========================================
with tab_report:
    st.subheader("📋 Preliminary Forensic Survey Report")

    # Annotated images gallery
    st.markdown("#### Annotated Scene Imagery")
    annotated_dir = Path("data/annotated")
    annotated_files = list(annotated_dir.glob(f"annotated_{selected_scene_id}_*")) if annotated_dir.exists() else []

    if annotated_files:
        cols = st.columns(2)
        for idx, img_p in enumerate(annotated_files):
            with cols[idx % 2]:
                st.image(Image.open(img_p), caption=img_p.name, use_container_width=True)
    else:
        st.info("No annotated visual renders found yet. Run scene analysis in the Ingestion tab.")

    st.markdown("---")
    st.markdown("#### Agent Forensic Digest & Case Notes")

    # Generate or refresh report
    if st.button("🔄 Generate Updated AI Forensic Summary", type="secondary"):
        with st.spinner("Generating summary with agent..."):
            try:
                resp = httpx.post(
                    f"{API_BASE}/scenes/{selected_scene_id}/analyze",
                    headers=get_headers(api_key_input),
                    timeout=120.0,
                )
                if resp.status_code == 200:
                    st.success("Report updated!")
                    st.rerun()
            except Exception as e:
                st.error(f"Report error: {e}")

    # Report text representation
    counts = {}
    for item in evidence_items:
        c = item["evidence_class"]
        counts[c] = counts.get(c, 0) + 1

    report_text = f"""# Preliminary Forensic Survey Report
**Scene ID:** {selected_scene_id}
**Case Reference:** {active_scene.get('case_reference', 'N/A') if active_scene else 'N/A'}
**Survey Status:** AI-Assisted Preliminary Survey (Phase 1)

---

### Evidence Inventory:
- **Total Evidence Items Logged:** {len(evidence_items)}
- **Bloodstains:** {counts.get('bloodstain', 0)}
- **Footprints / Shoeprints:** {counts.get('footprint', 0)}
- **Digital Devices:** {counts.get('digital_device', 0)}
- **Items Requiring Human Review:** {sum(1 for e in evidence_items if e.get('requires_review'))}
- **Items Confirmed by Investigator:** {sum(1 for e in evidence_items if e.get('reviewed'))}

---
*Notice: This is an AI-assisted preliminary survey generated by RAZIN v0.1. All evidence items require human verification for chain of custody.*
"""
    st.markdown(report_text)
    st.download_button(
        label="📥 Download Forensic Report (.md)",
        data=report_text,
        file_name=f"forensic_report_{selected_scene_id}.md",
        mime="text/markdown",
    )
