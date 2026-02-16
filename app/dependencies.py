from app.storage.duckdb_store import DuckDBStore
from app.embeddings.local_embedder import LocalEmbedder
from app.rag.llm.ollama_client import OllamaClient
from app.rag.retriever import Retriever
from app.rag.engine import RAGEngine
from app.config import settings

# Global instances
_store = None
_embedder = None
_llm = None

def get_store() -> DuckDBStore:
    global _store
    if _store is None:
        _store = DuckDBStore(db_path=settings.duckdb_path)
        _store.initialize()
    return _store

def get_embedder() -> LocalEmbedder:
    global _embedder
    if _embedder is None:
        # Load once
        _embedder = LocalEmbedder(model_name=settings.embedding_model)
    return _embedder

def get_llm() -> OllamaClient:
    global _llm
    if _llm is None:
        _llm = OllamaClient(base_url=settings.ollama_base_url, model=settings.llm_model)
    return _llm

def get_retriever() -> Retriever:
    return Retriever(get_store(), get_embedder())

def get_engine() -> RAGEngine:
    return RAGEngine(get_retriever(), get_llm())
