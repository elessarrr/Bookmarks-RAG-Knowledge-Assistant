from typing import List
from unittest.mock import AsyncMock, patch

import pytest

from app.storage.duckdb_store import DuckDBStore
from app.storage.base import BaseStorage, RetrievedChunk
from app.embeddings.base import BaseEmbedder
from app.rag.llm.base import BaseLLM
from app.rag.engine import RAGResponse

from evals.chunking_comparison import (
    ChunkingStrategy,
    build_index_for_strategy,
    evaluate_qa_pairs,
    compare_chunking_strategies,
)


class FixedDimEmbedder(BaseEmbedder):
    """Deterministic 384-dim embedder for tests: same text always maps to the same vector."""

    def embed_single(self, text: str) -> List[float]:
        seed = float(len(text) % 97) / 97.0
        return [seed] * 384

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_single(t) for t in texts]


class FakeLLM(BaseLLM):
    async def generate(self, system_prompt, user_query, context_chunks):
        return "This is a fake grounded answer."

    async def generate_stream(self, system_prompt, user_query, context_chunks):
        yield "fake"


def make_store() -> BaseStorage:
    store = DuckDBStore(db_path=":memory:")
    store.initialize()
    return store


LONG_TEXT = " ".join(f"Sentence number {i} about ducks and databases." for i in range(200))


def test_build_index_for_strategy_chunk_count_varies_with_chunk_size():
    """The whole point of a chunking-strategy comparison is that different
    strategies actually produce a different index. If chunk_size doesn't
    change the chunk count, the comparison would be measuring nothing."""
    embedder = FixedDimEmbedder()
    documents = [("https://example.com/duckdb", LONG_TEXT)]

    small = ChunkingStrategy(name="small", chunk_size=20, overlap=5)
    large = ChunkingStrategy(name="large", chunk_size=800, overlap=100)

    small_count = build_index_for_strategy(documents, small, embedder, make_store())
    large_count = build_index_for_strategy(documents, large, embedder, make_store())

    assert small_count > large_count > 0


@pytest.mark.asyncio
async def test_evaluate_qa_pairs_aggregates_retrieval_metrics():
    qa_pairs = [
        {"question": "What is DuckDB?", "ground_truth_urls": ["https://duckdb.org/"]},
        {"question": "What is unrelated?", "ground_truth_urls": ["https://nomatch.example/"]},
    ]

    mock_engine = AsyncMock()
    mock_engine.query.side_effect = [
        RAGResponse(
            answer="DuckDB is an in-process OLAP database.",
            sources=[RetrievedChunk(text="duckdb content", score=0.9, metadata={"url": "https://duckdb.org/"})],
        ),
        RAGResponse(answer="I don't know.", sources=[]),
    ]

    metrics = await evaluate_qa_pairs(qa_pairs, mock_engine, k=5, include_answer_quality=False)

    assert metrics["precision_at_k"] == pytest.approx((1 / 5 + 0.0) / 2)
    assert metrics["recall"] == pytest.approx(0.5)
    assert metrics["mrr"] == pytest.approx(0.5)
    assert "faithfulness" not in metrics
    assert "answer_relevance" not in metrics


@pytest.mark.asyncio
async def test_evaluate_qa_pairs_includes_answer_quality_when_requested():
    qa_pairs = [{"question": "What is DuckDB?", "ground_truth_urls": ["https://duckdb.org/"]}]
    mock_engine = AsyncMock()
    mock_engine.query.return_value = RAGResponse(
        answer="DuckDB is an OLAP database.",
        sources=[RetrievedChunk(text="duckdb content", score=0.9, metadata={"url": "https://duckdb.org/"})],
    )

    with patch("evals.chunking_comparison.calculate_faithfulness", return_value=0.8) as mock_faithfulness, patch(
        "evals.chunking_comparison.calculate_answer_relevance", return_value=0.7
    ) as mock_relevance:
        metrics = await evaluate_qa_pairs(qa_pairs, mock_engine, k=5, include_answer_quality=True)

    mock_faithfulness.assert_called_once()
    mock_relevance.assert_called_once()
    assert metrics["faithfulness"] == pytest.approx(0.8)
    assert metrics["answer_relevance"] == pytest.approx(0.7)


@pytest.mark.asyncio
async def test_compare_chunking_strategies_returns_distinct_results_per_strategy():
    """End-to-end proof that the comparison mechanism is real: two different
    chunking strategies, run against the same documents and the same qa_pairs,
    must come back as separate indexes with separate, independently-computed
    metrics -- not the same number copy-pasted twice."""
    documents = [("https://duckdb.org/", LONG_TEXT)]
    qa_pairs = [{"question": "What is DuckDB?", "ground_truth_urls": ["https://duckdb.org/"]}]
    strategies = [
        ChunkingStrategy(name="small", chunk_size=20, overlap=5),
        ChunkingStrategy(name="large", chunk_size=800, overlap=100),
    ]

    results = await compare_chunking_strategies(
        documents=documents,
        qa_pairs=qa_pairs,
        strategies=strategies,
        embedder=FixedDimEmbedder(),
        llm=FakeLLM(),
        storage_factory=make_store,
        k=5,
        include_answer_quality=False,
    )

    assert set(results.keys()) == {"small", "large"}
    assert results["small"]["total_chunks"] > results["large"]["total_chunks"]
    for name in ("small", "large"):
        assert "metrics" in results[name]
        assert "precision_at_k" in results[name]["metrics"]
        assert results[name]["chunk_size"] == strategies[0 if name == "small" else 1].chunk_size
