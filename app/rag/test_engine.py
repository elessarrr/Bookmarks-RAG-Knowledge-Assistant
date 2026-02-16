import pytest
from unittest.mock import MagicMock, AsyncMock
from app.rag.engine import RAGEngine, RAGResponse
from app.storage.base import RetrievedChunk

@pytest.mark.asyncio
async def test_rag_engine_query():
    mock_retriever = MagicMock()
    mock_llm = MagicMock()
    
    # Mock retrieval
    chunk = RetrievedChunk(text="Context text", score=0.9, metadata={"title": "Title", "url": "http://url.com"})
    mock_retriever.retrieve.return_value = [chunk]
    
    # Mock LLM generation
    mock_llm.generate = AsyncMock(return_value="Answer")
    
    engine = RAGEngine(mock_retriever, mock_llm)
    response = await engine.query("Question")
    
    assert isinstance(response, RAGResponse)
    assert response.answer == "Answer"
    assert len(response.sources) == 1
    assert response.sources[0] == chunk
    
    mock_retriever.retrieve.assert_called_with("Question", k=5, filters=None)
    mock_llm.generate.assert_called_once()
    
    # Check prompt context formatting
    call_args = mock_llm.generate.call_args
    context_list = call_args[0][2]
    assert len(context_list) == 1
    assert "[Source 1 (Title - http://url.com)]:\nContext text" in context_list[0]

@pytest.mark.asyncio
async def test_rag_engine_query_no_results():
    mock_retriever = MagicMock()
    mock_llm = MagicMock()
    
    mock_retriever.retrieve.return_value = []
    
    engine = RAGEngine(mock_retriever, mock_llm)
    response = await engine.query("Question")
    
    assert "couldn't find" in response.answer
    assert response.sources == []
    mock_llm.generate.assert_not_called()

@pytest.mark.asyncio
async def test_rag_engine_stream():
    mock_retriever = MagicMock()
    mock_llm = MagicMock()
    
    chunk = RetrievedChunk(text="Context", score=0.9, metadata={})
    mock_retriever.retrieve.return_value = [chunk]
    
    async def mock_stream(*args):
        yield "Part 1"
        yield "Part 2"
        
    mock_llm.generate_stream = mock_stream
    
    engine = RAGEngine(mock_retriever, mock_llm)
    parts = []
    async for part in engine.query_stream("Question"):
        parts.append(part)
        
    assert parts == ["Part 1", "Part 2"]
