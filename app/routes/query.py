from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.rag.engine import RAGEngine
from app.storage.duckdb_store import DuckDBStore
from app.rag.retriever import Retriever
from app.dependencies import get_store, get_embedder, get_llm

router = APIRouter()

from app.rag.llm.base import BaseLLM
from app.embeddings.base import BaseEmbedder

# --- Dependencies ---

def get_retriever_dep(store: DuckDBStore = Depends(get_store), embedder: BaseEmbedder = Depends(get_embedder)) -> Retriever:
    return Retriever(store, embedder)

def get_engine_dep(retriever: Retriever = Depends(get_retriever_dep), llm: BaseLLM = Depends(get_llm)) -> RAGEngine:
    return RAGEngine(retriever, llm)

# --- Models ---

class QueryRequest(BaseModel):
    question: str
    filters: Optional[Dict[str, Any]] = None
    k: int = 5

class Source(BaseModel):
    text: str
    score: float
    url: str
    title: str
    folder: str
    date_added: Optional[datetime] = None
    domain: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]

class StatsResponse(BaseModel):
    total_bookmarks: int
    total_chunks: int
    failed_bookmarks: int

# --- Endpoints ---

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest,
    engine: RAGEngine = Depends(get_engine_dep)
) -> QueryResponse:
    try:
        response = await engine.query(request.question, k=request.k, filters=request.filters)
        
        sources = [
            Source(
                text=s.text,
                score=s.score,
                url=str(s.metadata.get("url", "")),
                title=str(s.metadata.get("title", "")),
                folder=str(s.metadata.get("folder", "")),
                date_added=s.metadata.get("date_added"),
                domain=str(s.metadata.get("domain", ""))
            )
            for s in response.sources
        ]
        
        return QueryResponse(answer=response.answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=StatsResponse)
async def stats_endpoint(store: DuckDBStore = Depends(get_store)) -> StatsResponse:
    # This logic should be in store class ideally
    try:
        # Count bookmarks
        res_bm = store.conn.execute("SELECT count(*) FROM bookmarks").fetchone()
        total_bookmarks = res_bm[0] if res_bm else 0
        
        res_fail = store.conn.execute("SELECT count(*) FROM bookmarks WHERE status = 'failed'").fetchone()
        failed_bookmarks = res_fail[0] if res_fail else 0
        
        # Count chunks
        res_chunks = store.conn.execute("SELECT count(*) FROM chunks").fetchone()
        total_chunks = res_chunks[0] if res_chunks else 0
        
        return StatsResponse(
            total_bookmarks=total_bookmarks,
            total_chunks=total_chunks,
            failed_bookmarks=failed_bookmarks
        )
    except Exception:
        # Tables might not exist yet
        return StatsResponse(total_bookmarks=0, total_chunks=0, failed_bookmarks=0)
