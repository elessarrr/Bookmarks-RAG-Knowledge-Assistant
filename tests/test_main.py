from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

def test_static_files():
    # We created dummy index.html in main.py if not exists
    response = client.get("/")
    assert response.status_code == 200
    assert "Bookmark RAG Tool" in response.text or "API is running" in response.text

def test_api_routes_mounted():
    # Check if ingest router is mounted (POST /api/upload)
    # We expect 422 because we didn't send a file, but route exists
    response = client.post("/api/upload")
    assert response.status_code == 422
    
    # Check if query router is mounted (GET /api/stats)
    response = client.get("/api/stats")
    # Might be 200 if DB is ready (mocked or in-memory) or 500 if DB path invalid/locked
    # But route should exist (not 404)
    assert response.status_code in [200, 500]
