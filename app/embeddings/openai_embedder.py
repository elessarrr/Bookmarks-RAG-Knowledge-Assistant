import httpx
import os
from typing import List
from app.embeddings.base import BaseEmbedder

class OpenAIEmbedder(BaseEmbedder):
    """
    OpenAI embedding model.
    """
    def __init__(self, api_key: str | None = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIEmbedder")
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single string.
        """
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of strings.
        """
        if not texts:
            return []
            
        # Replace newlines as recommended by OpenAI for older models, 
        # but 3-small handles it better. Still good practice for some cases.
        cleaned_texts = [text.replace("\n", " ") for text in texts]
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": cleaned_texts,
                    "model": self.model
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # OpenAI guarantees order matches input
            embeddings = [item["embedding"] for item in data["data"]]
            return embeddings
