import asyncio
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
import statistics

from app.dependencies import get_engine
from app.rag.engine import RAGEngine
from evals.metrics.retrieval import precision_at_k, recall, mrr
from evals.metrics.answer_quality import calculate_faithfulness, calculate_answer_relevance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATASET_PATH = "evals/dataset/qa_pairs.json"
RESULTS_DIR = "evals/results"

async def run_evals():
    # Load dataset
    if not os.path.exists(DATASET_PATH):
        logger.error(f"Dataset not found at {DATASET_PATH}")
        return

    with open(DATASET_PATH, "r") as f:
        qa_pairs = json.load(f)

    # Initialize Engine
    # Note: This uses the REAL storage and LLM as configured in app.config
    # Ensure Ollama is running and DB is populated for meaningful results.
    # For CI, we might mock, but this is the "run_evals" script.
    engine = get_engine()
    
    results = []
    
    print(f"Running evals on {len(qa_pairs)} examples...")
    
    for i, item in enumerate(qa_pairs):
        question = item["question"]
        ground_truth_urls = item.get("ground_truth_urls", [])
        
        print(f"[{i+1}/{len(qa_pairs)}] Processing: {question}")
        
        try:
            # Run RAG
            response = await engine.query(question, k=5)
            
            retrieved_urls = [s.metadata.get("url", "") for s in response.sources]
            retrieved_contexts = [s.text for s in response.sources]
            
            # Retrieval Metrics
            p_at_5 = precision_at_k(retrieved_urls, ground_truth_urls, k=5)
            rec = recall(retrieved_urls, ground_truth_urls)
            mrr_score = mrr(retrieved_urls, ground_truth_urls)
            
            # Answer Quality Metrics (Ragas)
            # Only run if we have an answer and contexts
            faithfulness = 0.0
            relevance = 0.0
            
            if response.answer and retrieved_contexts:
                # These can be slow
                faithfulness = calculate_faithfulness(question, response.answer, retrieved_contexts)
                relevance = calculate_answer_relevance(question, response.answer, retrieved_contexts)
            
            result_item = {
                "question": question,
                "answer": response.answer,
                "ground_truth_urls": ground_truth_urls,
                "retrieved_urls": retrieved_urls,
                "metrics": {
                    "precision_at_5": p_at_5,
                    "recall": rec,
                    "mrr": mrr_score,
                    "faithfulness": faithfulness,
                    "answer_relevance": relevance
                }
            }
            results.append(result_item)
            
        except Exception as e:
            logger.error(f"Error processing item {i}: {e}")
            results.append({
                "question": question,
                "error": str(e)
            })

    # Aggregate
    valid_results = [r for r in results if "metrics" in r]
    if not valid_results:
        print("No valid results to aggregate.")
        return

    agg_metrics = {
        "mean_precision_at_5": statistics.mean([r["metrics"]["precision_at_5"] for r in valid_results]),
        "mean_recall": statistics.mean([r["metrics"]["recall"] for r in valid_results]),
        "mean_mrr": statistics.mean([r["metrics"]["mrr"] for r in valid_results]),
        "mean_faithfulness": statistics.mean([r["metrics"]["faithfulness"] for r in valid_results]),
        "mean_answer_relevance": statistics.mean([r["metrics"]["answer_relevance"] for r in valid_results]),
    }
    
    print("\n=== Evaluation Results ===")
    print(json.dumps(agg_metrics, indent=2))
    
    # Save
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{RESULTS_DIR}/{timestamp}.json"
    
    output = {
        "timestamp": timestamp,
        "aggregate_metrics": agg_metrics,
        "details": results
    }
    
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    asyncio.run(run_evals())
