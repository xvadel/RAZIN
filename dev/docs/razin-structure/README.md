# RAZIN

AI- and computer-vision-assisted preliminary crime-scene evidence surveying.
Full plan: see `RAZIN_Preliminary_Plan.md` (not included in this scaffold —
keep it alongside this repo).

This is the **Phase 1 skeleton** — build-sequence step 1 (repo scaffold +
Docker + a working `/health` endpoint) plus step 2 (Pydantic schemas), done.
Everything else is stubbed with `TODO` comments pointing at the plan section
and build-sequence step that fills it in.

## Run it

**Docker (recommended):**
```
docker compose up --build
curl http://localhost:8000/health
```

**Locally:**
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Structure

```
app/
├── main.py            # FastAPI entrypoint — /health is live
├── api/routes.py       # /scenes, /evidence endpoints — stubbed, see TODOs
├── models/schemas.py   # Pydantic models — implemented
├── cv/detector.py      # YOLO wrapper — stub (build steps 5-7)
├── agents/             # ReAct agent + tools — stub (build step 8)
├── db/                 # SQLAlchemy models + CRUD — stub (build step 3)
└── dashboard/           # Streamlit UI — placeholder (build step 10)
dataset/                # labeled training images go here
models/                 # exported model weights (.pt) go here
data/                   # runtime data — SQLite file, uploads (Docker volume)
```

## Next steps

Follow the build sequence in the plan (Section 4.2): SQLite + CRUD next,
then wire real logic into the `/scenes` endpoints, then the detector, then
the agent. Each stub file says exactly which step unblocks it.
