from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Chunk:
    chunk_id: str
    bookmark_url: str
    text: str
    chunk_index: int
    embedding: List[float]

@dataclass
class RetrievedChunk:
    text: str
    score: float
    metadata: Dict[str, Any]  # e.g. title, url, date_added

class BaseStorage(ABC):
    """
    Abstract base class for vector storage (DuckDB).
    """

    @abstractmethod
    def upsert_bookmark(self, url: str, title: str, folder: str, 
                        date_added: datetime, domain: str, status: str) -> None:
        """
        Insert or update bookmark metadata.
        """
        pass

    @abstractmethod
    def store_chunks(self, chunks: List[Chunk]) -> None:
        """
        Store embedded chunks for a bookmark.
        """
        pass
    
    @abstractmethod
    def get_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve bookmark metadata by URL.
        """
        pass
        
    @abstractmethod
    def list_all_urls(self) -> List[str]:
        """
        List all bookmark URLs currently in the store.
        """
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], k: int, 
               filters: Optional[Dict[str, Any]] = None) -> List[RetrievedChunk]:
        """
        Perform vector similarity search.
        
        Args:
            query_embedding: The vector of the query.
            k: Number of results to return.
            filters: Optional dictionary of filters (folder, domain, date range).
            
        Returns:
            List of RetrievedChunk objects ordered by similarity score.
        """
        pass
