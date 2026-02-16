import asyncio
import uuid
import logging
from typing import AsyncGenerator, Dict, Any
from urllib.parse import urlparse

from app.ingestion.parser import parse_bookmarks, Bookmark
from app.ingestion.fetcher import fetch_url
from app.ingestion.cleaner import clean_html
from app.ingestion.chunker import chunk_text
from app.storage.base import BaseStorage, Chunk
from app.embeddings.base import BaseEmbedder
from app.config import settings

logger = logging.getLogger(__name__)

async def ingest_bookmarks(
    html_content: str, 
    storage: BaseStorage, 
    embedder: BaseEmbedder,
    chunk_size: int = 400,
    chunk_overlap: int = 50
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Orchestrates the ingestion process.
    Yields progress events.
    """
    # 1. Parse
    yield {"status": "parsing", "message": "Parsing HTML content..."}
    bookmarks = parse_bookmarks(html_content)
    total = len(bookmarks)
    
    yield {"status": "parsing_complete", "total": total, "message": f"Found {total} bookmarks"}
    
    if total == 0:
        return

    # 2. Process
    success_count = 0
    failed_count = 0
    
    for i, bookmark in enumerate(bookmarks):
        yield {
            "status": "processing", 
            "current": i + 1, 
            "total": total, 
            "url": bookmark.url,
            "title": bookmark.title
        }
        
        try:
            # Check if already exists? (Optional optimization, but let's upsert)
            
            # Fetch
            fetch_result = await fetch_url(bookmark.url)
            
            if fetch_result.status_code >= 400 or not fetch_result.content:
                # Log failure but continue
                # Update bookmark status in DB
                storage.upsert_bookmark(
                    url=bookmark.url,
                    title=bookmark.title,
                    folder=bookmark.folder,
                    date_added=bookmark.date_added,
                    domain=urlparse(bookmark.url).netloc,
                    status="failed"
                )
                failed_count += 1
                yield {"status": "failed", "url": bookmark.url, "reason": fetch_result.error or "Fetch failed"}
                continue
                
            # Clean
            clean_text = clean_html(fetch_result.content)
            if not clean_text:
                failed_count += 1
                yield {"status": "failed", "url": bookmark.url, "reason": "No content after cleaning"}
                continue
                
            # Chunk
            chunks = chunk_text(clean_text, chunk_size, chunk_overlap)
            if not chunks:
                 failed_count += 1
                 yield {"status": "failed", "url": bookmark.url, "reason": "No chunks generated"}
                 continue
            
            # Embed
            texts = [c.text for c in chunks]
            embeddings = embedder.embed_batch(texts)
            
            # Assign embeddings and convert to Storage Chunk
            db_chunks: list[Chunk] = []
            for j, c in enumerate(chunks):
                # chunk_text returns simple Chunk(text, start, end, chunk_index)
                # We need to map to app.storage.base.Chunk(chunk_id, bookmark_url, text, chunk_index, embedding, ...)
                
                db_chunks.append(Chunk(
                    chunk_id=str(uuid.uuid4()),
                    bookmark_url=bookmark.url,
                    text=c.text,
                    chunk_index=c.chunk_index,
                    embedding=embeddings[j],
                    start_char_idx=c.start_char_idx,
                    end_char_idx=c.end_char_idx
                ))
                
            # Store
            # First upsert bookmark metadata
            storage.upsert_bookmark(
                url=bookmark.url,
                title=bookmark.title,
                folder=bookmark.folder,
                date_added=bookmark.date_added,
                domain=urlparse(bookmark.url).netloc,
                status="indexed"
            )
            # Then store chunks
            storage.store_chunks(db_chunks)
            
            success_count += 1
            
        except Exception as e:
            failed_count += 1
            yield {"status": "error", "url": bookmark.url, "message": str(e)}
            
    yield {
        "status": "completed", 
        "success": success_count, 
        "failed": failed_count, 
        "message": "Ingestion complete"
    }
