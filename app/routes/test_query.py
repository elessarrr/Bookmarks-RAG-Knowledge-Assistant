from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.routes.query import router as query_router
from app.rag.engine import RAGResponse, RAGEngine
from app.storage.base import RetrievedChunk
from app.storage.duckdb_store import DuckDBStore
import pytest
from unittest.mock import MagicMock, AsyncMock

test_app = FastAPI()
test_app.include_router(query_router)

# Use override_dependency for TestClient
# Patching inside the test function context for client calls doesn't always work 
# because FastAPI resolves dependencies at request time, but patching might not be active 
# in the context where FastAPI is running if not done carefully.
# Better to use app.dependency_overrides.

client = TestClient(test_app)

@pytest.mark.asyncio
async def test_query_endpoint():
    # Mock engine
    mock_engine = AsyncMock(spec=RAGEngine)
    mock_engine.query.return_value = RAGResponse(
        answer="Test Answer",
        sources=[
            RetrievedChunk(
                text="Source Text",
                score=0.9,
                metadata={"url": "http://test.com", "title": "Test Title"}
            )
        ]
    )
    
    # Override dependency
    from app.routes.query import get_engine_dep
    test_app.dependency_overrides[get_engine_dep] = lambda: mock_engine
    
    try:
        response = client.post(
            "/query",
            json={"question": "What is test?", "k": 3}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Test Answer"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["url"] == "http://test.com"
        
        mock_engine.query.assert_called_with("What is test?", k=3, filters=None)
    finally:
        test_app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_stats_endpoint():
    # Mock store
    mock_store = MagicMock(spec=DuckDBStore)
    mock_conn = MagicMock()
    mock_store.conn = mock_conn
    
    # Mock execute results
    # total_bookmarks, failed_bookmarks, total_chunks
    
    mock_cursor = MagicMock()
    # fetchone returns a tuple/row
    mock_cursor.fetchone.side_effect = [[10], [2], [50]]
    mock_conn.execute.return_value = mock_cursor
    
    from app.routes.query import get_store
    test_app.dependency_overrides[get_store] = lambda: mock_store
    
    try:
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_bookmarks"] == 10
        assert data["failed_bookmarks"] == 2
        assert data["total_chunks"] == 50
    finally:
        test_app.dependency_overrides = {}
