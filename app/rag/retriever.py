from typing import List, Dict, Any, Optional
from app.storage.base import BaseStorage, RetrievedChunk
from app.embeddings.base import BaseEmbedder

class Retriever:
    """
    RAG Retriever component.
    Orchestrates embedding the query and searching the vector store.
    """
    def __init__(self, storage: BaseStorage, embedder: BaseEmbedder):
        self.storage = storage
        self.embedder = embedder

    def retrieve(self, query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[RetrievedChunk]:
        """
        Embed query and retrieve relevant chunks.
        """
        if not query.strip():
            return []

        # Embed the query
        query_embedding = self.embedder.embed_single(query)
        
        # Search storage
        results = self.storage.search(query_embedding, k=k, filters=filters)
        
        return results
