"""
FastAPI HTTP Endpoint Integration Tests for RAZIN.
"""

from io import BytesIO
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_image_bytes() -> bytes:
    img = Image.new("RGB", (320, 240), color=(100, 100, 100))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_api_full_flow():
    print("=" * 60)
    print("1. Testing /health probe...")
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    print(f"✓ /health OK: {res.json()}")

    print("\n2. Testing /scenes (Create Scene)...")
    scene_id = "SCENE-API-TEST-99"
    res = client.post("/scenes", json={"scene_id": scene_id, "case_reference": "CASE-CR-404"})
    assert res.status_code == 200
    data = res.json()
    assert data["scene_id"] == scene_id
    print(f"✓ Scene created: {data}")

    print("\n3. Testing /scenes (List Scenes)...")
    res = client.get("/scenes")
    assert res.status_code == 200
    scenes = res.json()
    assert any(s["scene_id"] == scene_id for s in scenes)
    print(f"✓ Retrieved {len(scenes)} scenes.")

    print("\n4. Testing /scenes/{scene_id}/upload...")
    img_bytes = create_test_image_bytes()
    files = {"file": ("scene_sample.jpg", img_bytes, "image/jpeg")}
    res = client.post(f"/scenes/{scene_id}/upload", files=files)
    assert res.status_code == 200
    upload_data = res.json()
    assert upload_data["status"] == "uploaded"
    print(f"✓ Media uploaded: {upload_data}")

    print("\n5. Testing /scenes/{scene_id}/analyze...")
    res = client.post(f"/scenes/{scene_id}/analyze")
    assert res.status_code == 200
    analysis = res.json()
    print(f"✓ Analysis complete: {analysis}")

    print("\n6. Testing /scenes/{scene_id}/evidence...")
    res = client.get(f"/scenes/{scene_id}/evidence")
    assert res.status_code == 200
    evidence = res.json()
    print(f"✓ Logged evidence count: {len(evidence)}")

    print("\n7. Testing static file serving /files/...")
    uploaded_path = upload_data["path"]
    res = client.get(f"/files/{uploaded_path}")
    assert res.status_code == 200
    print("✓ Static file serving OK.")

    print("\n8. Testing /scenes/{scene_id}/reindex (ChromaDB Indexing)...")
    res = client.post(f"/scenes/{scene_id}/reindex")
    assert res.status_code == 200
    reindex_data = res.json()
    assert reindex_data["status"] == "reindexed"
    print(f"✓ Reindex OK: {reindex_data}")

    print("\n9. Testing /scenes/{scene_id}/chat (RAG Chatbot)...")
    chat_payload = {
        "message": "What evidence was found in this scene?",
        "history": [],
        "scope": "scene",
    }
    res = client.post(f"/scenes/{scene_id}/chat", json=chat_payload)
    assert res.status_code == 200
    chat_data = res.json()
    assert "answer" in chat_data
    print(f"✓ Chat OK: answer length={len(chat_data['answer'])}, sources={len(chat_data.get('sources', []))}")

    print("\n" + "=" * 60)
    print("ALL API ENDPOINT TESTS PASSED! 🚀")


if __name__ == "__main__":
    test_api_full_flow()

