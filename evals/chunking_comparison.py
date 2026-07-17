"""
Compares retrieval and generation-quality metrics across multiple chunking
strategies, using the same source documents and the same qa_pairs for each.

Each strategy gets its own fresh, isolated vector index (built via
`build_index_for_strategy`), so results are never contaminated by a
different strategy's chunks. This module only contains the reusable
comparison logic; see `run_chunking_comparison.py` for the CLI entry point
that wires it up against real fetched bookmarks and the configured
embedder/LLM.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple
from urllib.parse import urlparse

from app.embeddings.base import BaseEmbedder
from app.ingestion.chunker import chunk_text
from app.rag.engine import RAGEngine
from app.rag.llm.base import BaseLLM
from app.rag.retriever import Retriever
from app.storage.base import BaseStorage, Chunk
from evals.metrics.answer_quality import calculate_answer_relevance, calculate_faithfulness
from evals.metrics.retrieval import mrr, precision_at_k, recall

logger = logging.getLogger(__name__)


@dataclass
class ChunkingStrategy:
    name: str
    chunk_size: int
    overlap: int


DEFAULT_STRATEGIES: List[ChunkingStrategy] = [
    ChunkingStrategy(name="small", chunk_size=150, overlap=20),
    ChunkingStrategy(name="default", chunk_size=400, overlap=50),
    ChunkingStrategy(name="large", chunk_size=800, overlap=100),
]


def build_index_for_strategy(
    documents: List[Tuple[str, str]],
    strategy: ChunkingStrategy,
    embedder: BaseEmbedder,
    storage: BaseStorage,
) -> int:
    """
    Chunk, embed, and store a fixed set of already-fetched (url, cleaned_text)
    documents under one chunking strategy.

    Returns the total number of chunks written, so a comparison can report
    index size alongside retrieval quality -- a strategy that produces more,
    smaller chunks is a meaningfully different index, not just a different
    number in a results table.
    """
    total_chunks = 0
    for url, text in documents:
        chunks = chunk_text(text, strategy.chunk_size, strategy.overlap)
        if not chunks:
            continue

        texts = [c.text for c in chunks]
        embeddings = embedder.embed_batch(texts)

        db_chunks = [
            Chunk(
                chunk_id=str(uuid.uuid4()),
                bookmark_url=url,
                text=c.text,
                chunk_index=c.chunk_index,
                embedding=embeddings[i],
                start_char_idx=c.start_char_idx,
                end_char_idx=c.end_char_idx,
            )
            for i, c in enumerate(chunks)
        ]

        storage.upsert_bookmark(
            url=url,
            title=url,
            folder="eval",
            date_added=None,
            domain=urlparse(url).netloc,
            status="indexed",
        )
        storage.store_chunks(db_chunks)
        total_chunks += len(db_chunks)

    return total_chunks


async def evaluate_qa_pairs(
    qa_pairs: List[Dict[str, Any]],
    engine: RAGEngine,
    k: int = 5,
    include_answer_quality: bool = True,
) -> Dict[str, float]:
    """
    Run every question in `qa_pairs` through `engine` and aggregate retrieval
    metrics (precision@k, recall, MRR). Optionally also computes RAGAS-based
    generation-quality metrics (faithfulness, answer relevance) -- these
    require a live LLM/embedding backend, so they can be skipped for fast,
    fully-mocked comparisons.
    """
    precisions: List[float] = []
    recalls: List[float] = []
    mrrs: List[float] = []
    faithfulnesses: List[float] = []
    relevances: List[float] = []

    for item in qa_pairs:
        question = item["question"]
        ground_truth_urls = item.get("ground_truth_urls", [])

        response = await engine.query(question, k=k)
        retrieved_urls = [s.metadata.get("url", "") for s in response.sources]
        retrieved_contexts = [s.text for s in response.sources]

        precisions.append(precision_at_k(retrieved_urls, ground_truth_urls, k=k))
        recalls.append(recall(retrieved_urls, ground_truth_urls))
        mrrs.append(mrr(retrieved_urls, ground_truth_urls))

        if include_answer_quality and response.answer and retrieved_contexts:
            faithfulnesses.append(calculate_faithfulness(question, response.answer, retrieved_contexts))
            relevances.append(calculate_answer_relevance(question, response.answer, retrieved_contexts))

    def _mean(values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    metrics: Dict[str, float] = {
        "precision_at_k": _mean(precisions),
        "recall": _mean(recalls),
        "mrr": _mean(mrrs),
    }
    if include_answer_quality:
        metrics["faithfulness"] = _mean(faithfulnesses)
        metrics["answer_relevance"] = _mean(relevances)

    return metrics


async def compare_chunking_strategies(
    documents: List[Tuple[str, str]],
    qa_pairs: List[Dict[str, Any]],
    strategies: List[ChunkingStrategy],
    embedder: BaseEmbedder,
    llm: BaseLLM,
    storage_factory: Callable[[], BaseStorage],
    k: int = 5,
    include_answer_quality: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """
    Build one fresh, isolated vector index per chunking strategy from the
    same source documents, evaluate the same qa_pairs against each, and
    return a per-strategy comparison of retrieval and generation-quality
    metrics.

    `storage_factory` must return a *new*, uninitialized BaseStorage each
    call (e.g. `lambda: DuckDBStore(":memory:")`) -- strategies must never
    share an index, or the comparison would be meaningless.
    """
    results: Dict[str, Dict[str, Any]] = {}

    for strategy in strategies:
        storage = storage_factory()
        storage.initialize()

        chunk_count = build_index_for_strategy(documents, strategy, embedder, storage)

        retriever = Retriever(storage=storage, embedder=embedder)
        engine = RAGEngine(retriever=retriever, llm=llm)

        metrics = await evaluate_qa_pairs(qa_pairs, engine, k=k, include_answer_quality=include_answer_quality)

        results[strategy.name] = {
            "chunk_size": strategy.chunk_size,
            "overlap": strategy.overlap,
            "total_chunks": chunk_count,
            "metrics": metrics,
        }

        logger.info(
            "chunking strategy=%s chunk_size=%d overlap=%d total_chunks=%d metrics=%s",
            strategy.name,
            strategy.chunk_size,
            strategy.overlap,
            chunk_count,
            metrics,
        )

    return results
