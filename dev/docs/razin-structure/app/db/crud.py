"""
CRUD functions — RAZIN_Preliminary_Plan.md, Section 4.2 (Persistence).

Build-sequence step 3. These are the functions app/api/routes.py and
app/agents/tools.py call to read/write scenes and evidence. Expected
shape:

    def create_scene(scene: SceneUploadRequest) -> None: ...
    def create_evidence(item: EvidenceItem) -> str: ...          # returns evidence_id
    def flag_evidence_for_review(evidence_id: str, reason: str) -> None: ...
    def list_evidence_for_scene(scene_id: str) -> list[EvidenceItem]: ...
    def get_evidence(evidence_id: str) -> EvidenceItem | None: ...
"""

# TODO(build step 3): implement against app/db/database.py once the
# SQLAlchemy models exist.
