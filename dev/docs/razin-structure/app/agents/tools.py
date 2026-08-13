"""
LangChain tools for the ReAct agent — RAZIN_Preliminary_Plan.md, Section 4.2.

Build-sequence step 8: wrap detection as a tool, plus logging and
review-flag tools, so the agent (react_agent.py) can call them.

    from langchain_core.tools import tool
    from app.cv.detector import detect
    from app.models.schemas import DetectionResult, EvidenceItem

    @tool
    def detect_evidence_tool(image_path: str) -> list[DetectionResult]:
        \"\"\"Run the fine-tuned YOLO model on an image and return raw detections.\"\"\"
        return detect(image_path)

    @tool
    def log_evidence_tool(item: EvidenceItem) -> str:
        \"\"\"Persist a validated evidence item to the database. Returns the evidence_id.\"\"\"
        # TODO: call app/db/crud.py
        ...

    @tool
    def flag_for_review_tool(evidence_id: str, reason: str) -> None:
        \"\"\"Mark an evidence item as requiring human review.\"\"\"
        # TODO: call app/db/crud.py
        ...
"""
