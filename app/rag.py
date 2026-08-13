"""
RAG (Retrieval-Augmented Generation) module for RAZIN forensic chatbot.

Indexes evidence metadata and visual crops into ChromaDB,
provides retrieval-augmented chat over evidence data.

Two collections:
  - razin_evidence_text   → text embeddings of evidence metadata
  - razin_evidence_visual → CLIP embeddings of evidence crop images
"""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from app.config import CHROMA_DIR, GOOGLE_API_KEY
from app.schemas import EvidenceItem


# ---------------------------------------------------------------------------
# Vector store singleton
# ---------------------------------------------------------------------------

_client: chromadb.ClientAPI | None = None


def get_vectorstore() -> chromadb.ClientAPI:
    """Get or create the persistent ChromaDB client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


# ---------------------------------------------------------------------------
# Text embedding (Google text-embedding-004)
# ---------------------------------------------------------------------------

def _get_text_embedding_fn():
    """Google Generative AI embedding function for ChromaDB."""
    if not GOOGLE_API_KEY:
        return None
    try:
        from chromadb.utils.embedding_functions import (
            GoogleGenerativeAiEmbeddingFunction,
        )

        return GoogleGenerativeAiEmbeddingFunction(
            api_key=GOOGLE_API_KEY,
            model_name="models/text-embedding-004",
        )
    except Exception:
        return None


def _get_text_collection():
    """Get or create the text evidence collection."""
    client = get_vectorstore()
    ef = _get_text_embedding_fn()
    kwargs: dict = {"name": "razin_evidence_text"}
    if ef:
        kwargs["embedding_function"] = ef
    return client.get_or_create_collection(**kwargs)


# ---------------------------------------------------------------------------
# CLIP visual embedding (openai/clip-vit-base-patch32)
# ---------------------------------------------------------------------------

_clip_model = None
_clip_processor = None


def _load_clip():
    """Lazy-load CLIP model and processor on first use."""
    global _clip_model, _clip_processor
    if _clip_model is None:
        try:
            from transformers import CLIPModel, CLIPProcessor

            model_name = "openai/clip-vit-base-patch32"
            _clip_processor = CLIPProcessor.from_pretrained(model_name)
            _clip_model = CLIPModel.from_pretrained(model_name)
            _clip_model.eval()
            print("[RAZIN] CLIP model loaded successfully.")
        except Exception as e:
            print(f"[RAZIN] CLIP model load failed: {e}")
            return None, None
    return _clip_model, _clip_processor


def _embed_image(image_path: str) -> list[float] | None:
    """Produce a CLIP embedding for an image file."""
    model, processor = _load_clip()
    if model is None:
        return None
    try:
        import torch
        from PIL import Image

        img = Image.open(image_path).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")
        with torch.no_grad():
            features = model.get_image_features(**inputs)
        features = features / features.norm(p=2, dim=-1, keepdim=True)
        return features.squeeze().tolist()
    except Exception:
        return None


def _embed_text_clip(text: str) -> list[float] | None:
    """Produce a CLIP text embedding (for cross-modal visual search)."""
    model, processor = _load_clip()
    if model is None:
        return None
    try:
        import torch

        inputs = processor(
            text=[text], return_tensors="pt", padding=True, truncation=True
        )
        with torch.no_grad():
            features = model.get_text_features(**inputs)
        features = features / features.norm(p=2, dim=-1, keepdim=True)
        return features.squeeze().tolist()
    except Exception:
        return None


def _get_visual_collection():
    """Get or create the visual evidence collection (CLIP embeddings)."""
    client = get_vectorstore()
    return client.get_or_create_collection(
        name="razin_evidence_visual",
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Evidence → text document conversion
# ---------------------------------------------------------------------------

def _evidence_to_document(item: EvidenceItem) -> str:
    """Convert an EvidenceItem to a searchable text document."""
    parts = [
        f"Evidence Class: {item.evidence_class.value}",
        f"Confidence: {item.confidence:.2f}",
        f"Status: {'Flagged for human review' if item.requires_review else 'Auto-logged by AI'}",
        f"Reviewed: {'Yes' if item.reviewed else 'No'}",
        f"Bounding Box: ({item.bbox.x_min:.0f}, {item.bbox.y_min:.0f}, "
        f"{item.bbox.x_max:.0f}, {item.bbox.y_max:.0f})",
        f"Source Image: {item.source_image}",
        f"Timestamp: {item.timestamp.isoformat() if hasattr(item.timestamp, 'isoformat') else str(item.timestamp)}",
    ]
    if item.notes:
        parts.append(f"Agent Notes: {item.notes}")
    if item.scene_area_label:
        parts.append(f"Scene Area: {item.scene_area_label}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def index_evidence(scene_id: str, evidence_list: list[EvidenceItem]) -> int:
    """Index evidence metadata into the text collection. Returns count indexed."""
    if not evidence_list:
        return 0

    collection = _get_text_collection()

    documents = []
    metadatas = []
    ids = []

    for item in evidence_list:
        doc = _evidence_to_document(item)
        eid = str(item.evidence_id)
        meta = {
            "scene_id": scene_id,
            "evidence_class": item.evidence_class.value,
            "confidence": float(item.confidence),
            "requires_review": bool(item.requires_review),
            "reviewed": bool(item.reviewed),
            "source_image": item.source_image or "",
            "crop_image": item.crop_image or "",
        }
        documents.append(doc)
        metadatas.append(meta)
        ids.append(eid)

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[RAZIN] Indexed {len(documents)} evidence items (text) for scene {scene_id}")
    return len(documents)


def index_evidence_visuals(scene_id: str, evidence_list: list[EvidenceItem]) -> int:
    """Index evidence crop images via CLIP into the visual collection. Returns count."""
    collection = _get_visual_collection()
    count = 0

    for item in evidence_list:
        if not item.crop_image:
            continue
        crop_path = Path(item.crop_image)
        if not crop_path.exists():
            continue

        embedding = _embed_image(str(crop_path))
        if embedding is None:
            continue

        eid = str(item.evidence_id)
        meta = {
            "scene_id": scene_id,
            "evidence_class": item.evidence_class.value,
            "confidence": float(item.confidence),
            "crop_image": str(item.crop_image),
            "source_image": item.source_image or "",
        }
        collection.upsert(
            ids=[eid],
            embeddings=[embedding],
            metadatas=[meta],
            documents=[_evidence_to_document(item)],
        )
        count += 1

    if count:
        print(f"[RAZIN] Indexed {count} evidence crops (CLIP) for scene {scene_id}")
    return count


# ---------------------------------------------------------------------------
# Querying
# ---------------------------------------------------------------------------

def query_evidence(
    scene_id: str | None,
    question: str,
    k: int = 5,
) -> list[dict]:
    """Query text evidence. scene_id=None searches all scenes."""
    collection = _get_text_collection()
    where = {"scene_id": scene_id} if scene_id else None

    try:
        results = collection.query(
            query_texts=[question],
            n_results=min(k, collection.count() or 1),
            where=where,
        )
    except Exception:
        return []

    sources = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else None
            sources.append({
                "document": doc,
                "metadata": meta,
                "distance": dist,
                "evidence_id": results["ids"][0][i] if results["ids"] else None,
            })
    return sources


def query_similar_visuals(
    scene_id: str | None,
    image_path: str | None = None,
    text_query: str | None = None,
    k: int = 5,
) -> list[dict]:
    """Query visual collection by image or text (CLIP cross-modal search)."""
    collection = _get_visual_collection()
    if collection.count() == 0:
        return []

    where = {"scene_id": scene_id} if scene_id else None

    embedding = None
    if image_path:
        embedding = _embed_image(image_path)
    elif text_query:
        embedding = _embed_text_clip(text_query)

    if embedding is None:
        return []

    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(k, collection.count()),
            where=where,
        )
    except Exception:
        return []

    sources = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else None
            sources.append({
                "document": doc,
                "metadata": meta,
                "distance": dist,
                "evidence_id": results["ids"][0][i] if results["ids"] else None,
            })
    return sources


# ---------------------------------------------------------------------------
# RAG Chat pipeline
# ---------------------------------------------------------------------------

CHAT_SYSTEM_PROMPT = """You are RAZIN's forensic investigation assistant.
You help crime scene investigators by answering questions about evidence logged in the system.

Rules:
1. Ground ALL answers in the retrieved evidence context below. Do not invent evidence.
2. If the context doesn't contain enough information to answer, say so clearly.
3. Refer to evidence by class, confidence score, and ID when discussing specific items.
4. Remind investigators that all AI-detected evidence is preliminary and requires human verification.
5. Be concise, professional, and forensically precise.
"""


def chat(
    scene_id: str | None,
    question: str,
    chat_history: list[dict] | None = None,
    llm: Any = None,
) -> dict:
    """
    Full RAG pipeline:
      1. Retrieve relevant evidence from ChromaDB (text + visual)
      2. Build prompt with context + conversation history
      3. Call LLM → return answer + source evidence IDs
    """
    chat_history = chat_history or []

    # 1. Retrieve context
    text_sources = query_evidence(scene_id, question, k=6)
    visual_sources = query_similar_visuals(scene_id, text_query=question, k=3)

    # Merge & deduplicate
    seen_ids: set[str] = set()
    all_sources: list[dict] = []
    for src in text_sources + visual_sources:
        eid = src.get("evidence_id")
        if eid and eid not in seen_ids:
            seen_ids.add(eid)
            all_sources.append(src)

    # 2. Build context string
    if all_sources:
        context_parts = []
        for i, src in enumerate(all_sources, 1):
            context_parts.append(
                f"[Evidence {i}] (ID: {src['evidence_id']})\n{src['document']}"
            )
        context_str = "\n\n".join(context_parts)
    else:
        context_str = "No relevant evidence found in the database for this query."

    scope_label = f"Scene: {scene_id}" if scene_id else "All scenes"
    user_prompt = (
        f"--- Retrieved Evidence Context ({scope_label}) ---\n"
        f"{context_str}\n"
        f"--- End Context ---\n\n"
        f"Investigator's question: {question}"
    )

    # 3. Call LLM
    if llm is None:
        from app.agent import _get_llm
        llm = _get_llm()

    if llm is None:
        return {
            "answer": (
                f"LLM not configured. Retrieved {len(all_sources)} evidence items:\n\n"
                f"{context_str}"
            ),
            "sources": _format_sources(all_sources),
        }

    try:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        messages = [SystemMessage(content=CHAT_SYSTEM_PROMPT)]

        # Inject last 6 turns of conversation history
        for turn in chat_history[-6:]:
            if turn.get("role") == "user":
                messages.append(HumanMessage(content=turn["content"]))
            elif turn.get("role") == "assistant":
                messages.append(AIMessage(content=turn["content"]))

        messages.append(HumanMessage(content=user_prompt))

        response = llm.invoke(messages)
        answer = (
            response.content.strip()
            if response and response.content
            else "No response from LLM."
        )
    except Exception as e:
        answer = (
            f"LLM error: {e}. Retrieved {len(all_sources)} relevant evidence items."
        )

    return {
        "answer": answer,
        "sources": _format_sources(all_sources),
    }


def _format_sources(sources: list[dict]) -> list[dict]:
    """Format source evidence for API response."""
    return [
        {
            "evidence_id": s.get("evidence_id"),
            "evidence_class": s.get("metadata", {}).get("evidence_class"),
            "confidence": s.get("metadata", {}).get("confidence"),
            "crop_image": s.get("metadata", {}).get("crop_image"),
        }
        for s in sources
    ]
