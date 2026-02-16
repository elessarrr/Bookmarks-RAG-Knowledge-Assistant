import pytest
from evals.metrics.retrieval import precision_at_k, recall, mrr

def test_precision_at_k():
    retrieved = ["a", "b", "c", "d", "e"]
    ground_truth = ["a", "c", "f"]
    
    # K=1: "a" is in GT -> 1.0
    assert precision_at_k(retrieved, ground_truth, k=1) == 1.0
    
    # K=2: "a", "b". "a" is relevant. 1/2 = 0.5
    assert precision_at_k(retrieved, ground_truth, k=2) == 0.5
    
    # K=5: "a", "c" relevant. 2/5 = 0.4
    assert precision_at_k(retrieved, ground_truth, k=5) == 0.4
    
    # K > len(retrieved): still divide by K usually? Or len(retrieved)? 
    # Definition of P@K is relevant_in_top_k / k.
    assert precision_at_k(retrieved, ground_truth, k=10) == 0.2 # 2/10

def test_recall():
    retrieved = ["a", "b", "c"]
    ground_truth = ["a", "c", "f", "g"]
    
    # Found "a", "c" (2). Total relevant = 4. Recall = 2/4 = 0.5
    assert recall(retrieved, ground_truth) == 0.5
    
    # Zero recall
    assert recall(["x", "y"], ground_truth) == 0.0
    
    # Perfect recall
    assert recall(["a", "c", "f", "g", "z"], ground_truth) == 1.0

def test_mrr():
    ground_truth = ["target"]
    
    # First position (rank 1) -> 1/1 = 1.0
    assert mrr(["target", "a", "b"], ground_truth) == 1.0
    
    # Second position (rank 2) -> 1/2 = 0.5
    assert mrr(["a", "target", "b"], ground_truth) == 0.5
    
    # Third position (rank 3) -> 1/3 = 0.33...
    assert abs(mrr(["a", "b", "target"], ground_truth) - 0.333) < 0.01
    
    # Not found -> 0.0
    assert mrr(["a", "b"], ground_truth) == 0.0
    
    # Multiple ground truths: MRR usually considers the *first* relevant item found.
    ground_truth_multi = ["t1", "t2"]
    # "a", "t2" -> rank 2. 1/2 = 0.5
    assert mrr(["a", "t2", "t1"], ground_truth_multi) == 0.5
