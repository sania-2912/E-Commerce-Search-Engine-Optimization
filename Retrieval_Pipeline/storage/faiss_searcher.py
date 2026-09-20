"""FAISS Index Searcher"""
import numpy as np
from typing import List
import Retrieval_Pipeline.models.model_loader as ml

def search_bge_faiss(query_vec: np.ndarray, top_n: int = 50) -> List[dict]:
    if ml.faiss_index is None:
        raise RuntimeError("FAISS text index not loaded.")
    scores, indices = ml.faiss_index.search(query_vec.astype(np.float32), top_n)
    candidates = []
    for fidx, score in zip(indices[0], scores[0]):
        if fidx != -1:
            pid = ml.faiss_to_pid.get(int(fidx))
            if pid:
                candidates.append({
                    "pid": pid,
                    "semantic_score": float(score),
                    "final_score": float(score),
                })
    return candidates
