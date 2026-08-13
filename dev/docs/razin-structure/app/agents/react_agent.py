"""
ReAct agent — RAZIN_Preliminary_Plan.md, Section 4.2 (React (ReAct) Agent).

Build-sequence step 8. LangGraph's `create_react_agent` is the current
standard entry point for this pattern, but its exact parameter names
shift between releases — check the installed version's docs before
relying on the snippet below.

    from langgraph.prebuilt import create_react_agent
    from langchain.chat_models import init_chat_model
    from app.agents.tools import detect_evidence_tool, log_evidence_tool, flag_for_review_tool

    RAZIN_AGENT_PROMPT = \"\"\"
    You are RAZIN's forensic evidence triage assistant. You review
    AI-generated object detections from crime-scene imagery and decide,
    per detection, whether to log it as candidate evidence or flag it
    for human review.

    Rules:
    1. Never assert a detection is confirmed evidence — always mark AI
       output as unverified, pending human confirmation.
    2. If confidence is below the configured threshold, always flag for
       review rather than logging automatically.
    3. If detections of different classes significantly overlap, flag
       both for review rather than silently picking one.
    4. When uncertain, prefer flagging over discarding.
    \"\"\"

    def build_agent():
        llm = init_chat_model("<provider-and-model>")  # see plan, Section 10
        return create_react_agent(
            model=llm,
            tools=[detect_evidence_tool, log_evidence_tool, flag_for_review_tool],
            prompt=RAZIN_AGENT_PROMPT,
        )
"""
