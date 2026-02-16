from unittest.mock import MagicMock
from app.rag.retriever import Retriever
from app.storage.base import RetrievedChunk

def test_retrieve_basic():
    mock_storage = MagicMock()
    mock_embedder = MagicMock()
    
    # Mock embedding
    mock_embedder.embed_single.return_value = [0.1, 0.2, 0.3]
    
    # Mock search results
    mock_chunk = RetrievedChunk(text="Result", score=0.9, metadata={"url": "http://a.com"})
    mock_storage.search.return_value = [mock_chunk]
    
    retriever = Retriever(mock_storage, mock_embedder)
    results = retriever.retrieve("test query", k=3)
    
    assert len(results) == 1
    assert results[0] == mock_chunk
    
    mock_embedder.embed_single.assert_called_with("test query")
    mock_storage.search.assert_called_with([0.1, 0.2, 0.3], k=3, filters=None)

def test_retrieve_with_filters():
    mock_storage = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.embed_single.return_value = [0.1]
    
    retriever = Retriever(mock_storage, mock_embedder)
    filters = {"folder": "Tech"}
    retriever.retrieve("query", k=5, filters=filters)
    
    mock_storage.search.assert_called_with([0.1], k=5, filters=filters)

def test_retrieve_empty_query():
    mock_storage = MagicMock()
    mock_embedder = MagicMock()
    
    retriever = Retriever(mock_storage, mock_embedder)
    results = retriever.retrieve("")
    
    assert results == []
    mock_embedder.embed_single.assert_not_called()
    mock_storage.search.assert_not_called()
