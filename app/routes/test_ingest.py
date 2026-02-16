from fastapi.testclient import TestClient
import pytest
from unittest.mock import MagicMock, patch

# Note: app.main now includes routers, so we can use app directly or build test app.
# Using test_app to isolate if needed, but we need to override dependencies.

from fastapi import FastAPI
from app.routes.ingest import router as ingest_router

test_app = FastAPI()
test_app.include_router(ingest_router)

client = TestClient(test_app)

@pytest.mark.asyncio
async def test_upload_endpoint():
    # Mock dependencies
    # app.routes.ingest imports get_store, get_embedder from app.dependencies
    # We need to patch where they are IMPORTED in app.routes.ingest
    
    with patch("app.routes.ingest.get_store") as mock_storage_dep:
        with patch("app.routes.ingest.get_embedder") as mock_embedder_dep:
            mock_storage = MagicMock()
            mock_embedder = MagicMock()
            mock_storage_dep.return_value = mock_storage
            mock_embedder_dep.return_value = mock_embedder
            
            # Use dependency_overrides for FastAPI
            # But here we are patching the functions directly which should work if they are called directly
            # or if they are used as Depends(func).
            
            # Better approach with FastAPI:
            from app.dependencies import get_store, get_embedder
            test_app.dependency_overrides[get_store] = lambda: mock_storage
            test_app.dependency_overrides[get_embedder] = lambda: mock_embedder
            
            # Mock ingestion pipeline
            with patch("app.routes.ingest.ingest_bookmarks") as mock_pipeline:
                 # mock_pipeline returns async generator
                async def mock_gen(*args, **kwargs):
                    yield {"status": "starting"}
                    yield {"status": "completed"}
                
                mock_pipeline.side_effect = mock_gen
                
                response = client.post(
                    "/upload",
                    files={"file": ("bookmarks.html", "<html>...</html>", "text/html")}
                )
                
                assert response.status_code == 200
                assert "task_id" in response.json()
            
            # Cleanup
            test_app.dependency_overrides = {}

from app.routes import ingest

@pytest.mark.asyncio
async def test_status_endpoint():
    import asyncio
    queue = asyncio.Queue()
    await queue.put({"status": "progress"})
    await queue.put(None)
    
    ingest.tasks["test_task"] = queue
    
    response = client.get("/ingest-status?task_id=test_task")
    assert response.status_code == 200
    
    # Read stream
    content = response.text
    # Backend now uses json.dumps, so quotes are double quotes
    assert 'data: {"status": "progress"}' in content
