import asyncio
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any, AsyncGenerator
import json

from app.ingestion.pipeline import ingest_bookmarks
from app.storage.duckdb_store import DuckDBStore
from app.embeddings.local_embedder import LocalEmbedder
from app.dependencies import get_store, get_embedder

# Simple in-memory task tracker
tasks: Dict[str, asyncio.Queue[Any]] = {}

router = APIRouter()

@router.post("/upload")
async def upload_bookmarks(
    file: UploadFile = File(...),
    storage: DuckDBStore = Depends(get_store),
    embedder: LocalEmbedder = Depends(get_embedder)
) -> Dict[str, str]:
    content = await file.read()
    html_content = content.decode("utf-8")
    
    task_id = "ingest_task" # Only one task for now or use UUID
    
    # Create a queue for this task
    queue: asyncio.Queue[Any] = asyncio.Queue()
    tasks[task_id] = queue
    
    # Run ingestion in background
    asyncio.create_task(run_ingestion(task_id, html_content, storage, embedder, queue))
    
    return {"task_id": task_id, "message": "Ingestion started"}

async def run_ingestion(task_id: str, html_content: str, storage: DuckDBStore, embedder: LocalEmbedder, queue: asyncio.Queue[Any]) -> None:
    try:
        async for event in ingest_bookmarks(html_content, storage, embedder):
            await queue.put(event)
    except Exception as e:
        await queue.put({"status": "error", "message": str(e)})
    finally:
        await queue.put(None) # Sentinel

@router.get("/ingest-status", response_model=None)
async def ingest_status(task_id: str) -> StreamingResponse | JSONResponse:
    queue = tasks.get(task_id)
    if not queue:
        return JSONResponse(status_code=404, content={"message": "Task not found"})
        
    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            event = await queue.get()
            if event is None:
                # Put it back in case other clients are listening? 
                # No, queue is consumed. 
                # Ideally use broadcast, but for now simple queue per task (assumes single client).
                break
            yield f"data: {json.dumps(event)}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
