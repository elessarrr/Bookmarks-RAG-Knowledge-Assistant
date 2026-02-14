from abc import ABC, abstractmethod
from typing import List

class BaseEmbedder(ABC):
    """
    Abstract base class for embedding models.
    All concrete implementations (Local, OpenAI) must inherit from this.
    """
    
    @abstractmethod
    def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single string.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the vector embedding.
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of strings.
        
        Args:
            texts: A list of strings to embed.
            
        Returns:
            A list of lists of floats, where each inner list is a vector.
        """
        pass
