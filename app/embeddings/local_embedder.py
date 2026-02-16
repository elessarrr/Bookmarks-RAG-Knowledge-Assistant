from typing import List
from sentence_transformers import SentenceTransformer
from app.embeddings.base import BaseEmbedder

class LocalEmbedder(BaseEmbedder):
    """
    Local embedding model using sentence-transformers.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_single(self, text: str) -> List[float]:
        # SentenceTransformer returns ndarray or list depending on config, usually ndarray
        # cast to list[float]
        return list(self.model.encode(text).tolist())

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return list(self.model.encode(texts).tolist())
