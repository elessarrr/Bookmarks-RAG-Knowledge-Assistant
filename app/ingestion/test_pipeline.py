import pytest
from unittest.mock import AsyncMock, patch

from app.ingestion.pipeline import ingest_bookmarks
from app.storage.base import BaseStorage
from app.embeddings.base import BaseEmbedder
from app.ingestion.fetcher import FetchResult

# Mock dependencies
class MockStorage(BaseStorage):
    def __init__(self):
        self.bookmarks = {}
        self.chunks = []
        
    def upsert_bookmark(self, url, title, folder, date_added, domain, status):
        self.bookmarks[url] = {"status": status}
        
    def store_chunks(self, chunks):
        self.chunks.extend(chunks)
        
    def get_by_url(self, url):
        return self.bookmarks.get(url)
        
    def list_all_urls(self):
        return list(self.bookmarks.keys())
        
    def search(self, query_embedding, k, filters=None):
        return []

class MockEmbedder(BaseEmbedder):
    def embed_single(self, text):
        return [0.1] * 384
        
    def embed_batch(self, texts):
        return [[0.1] * 384 for _ in texts]

@pytest.mark.asyncio
async def test_ingest_pipeline_success():
    html_content = """
    <DL><p>
        <DT><A HREF="https://example.com">Example</A>
    </DL><p>
    """
    
    storage = MockStorage()
    embedder = MockEmbedder()
    
    # Mock fetcher to return valid HTML
    with patch("app.ingestion.pipeline.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = FetchResult(
            url="https://example.com",
            content="<html><body><p>This is enough content for the cleaner to pass it through.</p><p>Adding more text to ensure it exceeds the 100 char limit required by the cleaner.</p></body></html>",
            status_code=200
        )
        
        events = []
        async for event in ingest_bookmarks(html_content, storage, embedder):
            events.append(event)
            
        # Verify events
        assert events[0]["status"] == "starting"
        assert events[-1]["status"] == "completed"
        assert events[-1]["processed"] == 1
        
        # Verify storage
        assert "https://example.com" in storage.bookmarks
        assert storage.bookmarks["https://example.com"]["status"] == "processed"
        assert len(storage.chunks) > 0

@pytest.mark.asyncio
async def test_ingest_pipeline_deduplication():
    html_content = """
    <DL><p>
        <DT><A HREF="https://exists.com">Existing</A>
        <DT><A HREF="https://new.com">New</A>
    </DL><p>
    """
    
    storage = MockStorage()
    # Pre-seed existing
    storage.bookmarks["https://exists.com"] = {"status": "processed"}
    
    embedder = MockEmbedder()
    
    with patch("app.ingestion.pipeline.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = FetchResult(
            url="https://new.com",
            content="<html><body><p>Valid content for new bookmark. " * 5 + "</p></body></html>",
            status_code=200
        )
        
        events = []
        async for event in ingest_bookmarks(html_content, storage, embedder):
            events.append(event)
            
        # Should report 1 existing skipped
        info_events = [e for e in events if e["status"] == "info"]
        assert len(info_events) > 0
        assert "Skipping 1" in info_events[0]["message"]
        
        # Only 1 processed
        completion = events[-1]
        assert completion["processed"] == 1
        assert completion["skipped"] == 1

@pytest.mark.asyncio
async def test_ingest_pipeline_failure():
    html_content = """
    <DL><p>
        <DT><A HREF="https://fail.com">Fail</A>
    </DL><p>
    """
    
    storage = MockStorage()
    embedder = MockEmbedder()
    
    with patch("app.ingestion.pipeline.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = FetchResult(
            url="https://fail.com",
            content=None,
            status_code=404,
            error="Not Found"
        )
        
        events = []
        async for event in ingest_bookmarks(html_content, storage, embedder):
            events.append(event)
            
        completion = events[-1]
        assert completion["failed"] == 1
        
        assert storage.bookmarks["https://fail.com"]["status"] == "failed"
