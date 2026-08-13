# RAZIN Visual Assets & System Diagrams

This directory contains diagrams and architectural specifications for the **RAZIN** preliminary forensic evidence surveying platform.

---

## 📊 Available Visuals

### 1. Database Schema ERD
- **File:** [`database_erd.svg`](./database_erd.svg)
- **Description:** Complete entity relationship diagram showing `scenes`, `media`, and `evidence` tables, field data types, primary keys, foreign key constraints, and 1:N relations.

### 2. ReAct Agent Architecture & Triage Workflow
- **File:** [`react_agent_workflow.svg`](./react_agent_workflow.svg)
- **Description:** Detailed visualization of the ReAct (Reasoning + Acting) Agent loop with LLM reasoning (Gemini/Groq), tool calling (`log_evidence_tool`, `flag_for_review_tool`, `summarize_scene_tool`), confidence thresholding (<0.5), IoU bbox overlap checks (>0.3), and human-in-the-loop verification.

### 3. System Architecture & Dataflow
- **File:** [`system_architecture.svg`](./system_architecture.svg)
- **Description:** End-to-end data pipeline from scene ingestion and OpenCV frame extraction to YOLO detection, agentic triage, SQLite persistence, and the Streamlit dashboard interface.
