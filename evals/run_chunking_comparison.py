"""
CLI entry point: benchmarks retrieval accuracy and generation quality across
multiple chunking strategies, using the eval dataset's own ground-truth URLs
as the source documents.

Requires Ollama running locally and the DB-independent embedder configured
in app.config (this evaluates against fresh, temporary in-memory indexes --
it does not touch the app's real bookmark database at settings.duckdb_path).

Usage:
    PYTHONPATH=. python evals/run_chunking_comparison.py
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Tuple

from app.dependencies import get_embedder, get_llm
from app.ingestion.cleaner import clean_html
from app.ingestion.fetcher import fetch_url
from app.storage.duckdb_store import DuckDBStore
from evals.chunking_comparison import DEFAULT_STRATEGIES, compare_chunking_strategies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATASET_PATH = "evals/dataset/qa_pairs.json"
RESULTS_DIR = "evals/results"


async def fetch_and_clean_documents(urls: List[str]) -> List[Tuple[str, str]]:
    """
    Fetches and cleans each URL exactly once, regardless of how many chunking
    strategies are being compared -- strategies differ in how the *same*
    cleaned text is chunked, not in what's fetched.
    """
    documents: List[Tuple[str, str]] = []
    for url in urls:
        result = await fetch_url(url)
        if result.status_code >= 400 or not result.content:
            logger.warning("Skipping %s (fetch failed: %s)", url, result.error)
            continue

        clean_text = clean_html(result.content)
        if not clean_text:
            logger.warning("Skipping %s (no content after cleaning)", url)
            continue

        documents.append((url, clean_text))

    return documents


async def main() -> None:
    if not os.path.exists(DATASET_PATH):
        logger.error("Dataset not found at %s", DATASET_PATH)
        return

    with open(DATASET_PATH, "r") as f:
        qa_pairs = json.load(f)

    urls = sorted({url for item in qa_pairs for url in item.get("ground_truth_urls", [])})
    logger.info("Fetching %d unique document(s) referenced by the eval dataset...", len(urls))
    documents = await fetch_and_clean_documents(urls)

    if not documents:
        logger.error("No documents could be fetched -- aborting comparison.")
        return

    embedder = get_embedder()
    llm = get_llm()

    print(f"\nComparing {len(DEFAULT_STRATEGIES)} chunking strategies across {len(documents)} document(s), "
          f"{len(qa_pairs)} qa pair(s)...\n")

    results = await compare_chunking_strategies(
        documents=documents,
        qa_pairs=qa_pairs,
        strategies=DEFAULT_STRATEGIES,
        embedder=embedder,
        llm=llm,
        storage_factory=lambda: DuckDBStore(db_path=":memory:"),
        k=5,
        include_answer_quality=True,
    )

    print("=== Chunking Strategy Comparison ===")
    print(json.dumps(results, indent=2))

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{RESULTS_DIR}/chunking_comparison_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump({"timestamp": timestamp, "results": results}, f, indent=2)

    print(f"\nResults saved to {filename}")


if __name__ == "__main__":
    asyncio.run(main())
