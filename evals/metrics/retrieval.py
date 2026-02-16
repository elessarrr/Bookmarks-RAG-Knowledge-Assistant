from typing import List, Set

def precision_at_k(retrieved: List[str], ground_truth: List[str], k: int) -> float:
    """
    Calculate Precision@K.
    """
    if k <= 0:
        return 0.0
        
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
        
    gt_set = set(ground_truth)
    hits = sum(1 for url in top_k if url in gt_set)
    
    return hits / k

def recall(retrieved: List[str], ground_truth: List[str]) -> float:
    """
    Calculate Recall.
    """
    if not ground_truth:
        return 0.0
    
    gt_set = set(ground_truth)
    hits = sum(1 for url in retrieved if url in gt_set)
    
    return hits / len(gt_set)

def mrr(retrieved: List[str], ground_truth: List[str]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).
    Score is 1/rank of the first relevant item.
    """
    gt_set = set(ground_truth)
    
    for i, url in enumerate(retrieved):
        if url in gt_set:
            return 1.0 / (i + 1)
            
    return 0.0
