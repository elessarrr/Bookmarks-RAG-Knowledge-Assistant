from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from app import main as main_module

app = main_module.app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

def test_built_static_files_serve_react_shell(tmp_path):
    frontend_dist = tmp_path / "frontend" / "dist"
    frontend_dist.mkdir(parents=True)
    (frontend_dist / "index.html").write_text(
        '<html><body><div id="root"></div></body></html>',
        encoding="utf-8",
    )

    static_app = FastAPI()
    static_app.mount(
        "/",
        StaticFiles(
            directory=main_module.select_static_directory(
                frontend_dist,
                tmp_path / "static",
            ),
            html=True,
        ),
    )

    response = TestClient(static_app).get("/")

    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text
    assert "API is running" not in response.text

def test_select_static_directory_prefers_frontend_build(tmp_path):
    frontend_dist = tmp_path / "frontend" / "dist"
    frontend_dist.mkdir(parents=True)
    (frontend_dist / "index.html").write_text("<div id='root'></div>")
    fallback_static = tmp_path / "static"

    select_static_directory = getattr(main_module, "select_static_directory", None)

    assert select_static_directory is not None
    assert select_static_directory(frontend_dist, fallback_static) == str(frontend_dist)

def test_select_static_directory_creates_fallback(tmp_path):
    frontend_dist = tmp_path / "frontend" / "dist"
    fallback_static = tmp_path / "static"

    select_static_directory = getattr(main_module, "select_static_directory", None)

    assert select_static_directory is not None
    assert select_static_directory(frontend_dist, fallback_static) == str(fallback_static)
    assert (fallback_static / "index.html").is_file()

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
