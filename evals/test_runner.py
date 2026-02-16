import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from evals.run_evals import run_evals
from app.rag.engine import RAGResponse
from app.storage.base import RetrievedChunk

@pytest.mark.asyncio
async def test_eval_suite_mocked():
    # Mock engine to return perfect matches for the first item in dataset
    mock_response = RAGResponse(
        answer="DuckDB is an in-process SQL OLAP database.",
        sources=[
            RetrievedChunk(text="DuckDB content", score=1.0, metadata={"url": "https://duckdb.org/"})
        ]
    )
    
    with patch("evals.run_evals.get_engine") as mock_get_engine:
        mock_engine = AsyncMock()
        mock_engine.query.return_value = mock_response
        mock_get_engine.return_value = mock_engine
        
        # Mock Ragas to be fast
        with patch("evals.run_evals.calculate_faithfulness", return_value=1.0):
            with patch("evals.run_evals.calculate_answer_relevance", return_value=1.0):
                # Run
                await run_evals()
                # We expect it to run without error and save results
