import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.ingestion.fetcher import FetchResult
from app.rag.llm.base import BaseLLM
from app.storage.duckdb_store import DuckDBStore
from app.embeddings.base import BaseEmbedder

# Mock LLM
class MockLLM(BaseLLM):
    async def generate(self, system_prompt, user_query, context_chunks):
        return "This is a generated answer based on the context."
    async def generate_stream(self, system_prompt, user_query, context_chunks):
        yield "This is "
        yield "a generated "
        yield "answer."

# Mock Embedder
class MockEmbedder(BaseEmbedder):
    def embed_single(self, text):
        return [0.1] * 384
    def embed_batch(self, texts):
        return [[0.1] * 384 for _ in texts]

# Shared Store for test
test_store = DuckDBStore(db_path=":memory:")
test_store.initialize()

@pytest.fixture
def mock_fetcher():
    with patch("app.ingestion.pipeline.fetch_url", new_callable=AsyncMock) as mock:
        def side_effect(url):
            content = f"<html><body><h1>Content for {url}</h1><p>This is some meaningful text content about {url} that is long enough to be indexed by our RAG system. We need at least 100 characters usually.</p></body></html>"
            return FetchResult(url, content, 200)
        mock.side_effect = side_effect
        yield mock

@pytest.mark.asyncio
async def test_smoke_end_to_end(mock_fetcher):
    # Override dependencies
    from app.dependencies import get_store, get_embedder, get_llm
    
    app.dependency_overrides[get_store] = lambda: test_store
    app.dependency_overrides[get_embedder] = lambda: MockEmbedder()
    app.dependency_overrides[get_llm] = lambda: MockLLM()
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Check Health
            resp = await client.get("/health")
            assert resp.status_code == 200
            
            # 2. Upload Bookmarks
            with open("tests/fixtures/real_bookmarks.html", "rb") as f:
                resp = await client.post("/api/upload", files={"file": ("bookmarks.html", f, "text/html")})
            assert resp.status_code == 200
            task_id = resp.json()["task_id"]
            
            # 3. Wait for ingestion
            max_retries = 20
            for _ in range(max_retries):
                await asyncio.sleep(0.5)
                resp = await client.get("/api/stats")
                stats = resp.json()
                if stats["total_bookmarks"] >= 6:
                    break
                
            stats = (await client.get("/api/stats")).json()
            if stats["total_bookmarks"] == 0:
                pytest.fail("Ingestion did not complete. Background task might not be running.")

            assert stats["total_bookmarks"] >= 6
            assert stats["total_chunks"] > 0
            
            # 4. Query
            query_payload = {
                "question": "What is DuckDB?",
                "k": 3
            }
            resp = await client.post("/api/query", json=query_payload)
            assert resp.status_code == 200
            data = resp.json()
            
            assert data["answer"] == "This is a generated answer based on the context."
            assert len(data["sources"]) > 0
            
    finally:
        app.dependency_overrides = {}
        # Clear store tables for next run if needed (but in-memory is fresh per process, 
        # though test_store is global in this file. Good to clear if multiple tests.)
        test_store.conn.execute("DELETE FROM chunks")
        test_store.conn.execute("DELETE FROM bookmarks")
